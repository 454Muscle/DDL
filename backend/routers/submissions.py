"""Submissions router - public submission endpoints"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone

from services.database import db
from services.email import (
    fetch_site_settings, send_submission_email, 
    send_bulk_submission_email, send_admin_submissions_summary
)
from services.captcha import verify_recaptcha, verify_captcha, generate_captcha_challenge
from services.utils import parse_file_size_to_bytes, validate_http_url
from models.schemas import (
    Submission, SubmissionCreate, BulkSubmissionCreate, Download
)

router = APIRouter(tags=["submissions"])


@router.get("/captcha")
async def get_captcha():
    """Generate a new captcha challenge"""
    return await generate_captcha_challenge()


@router.post("/submissions", response_model=Submission)
async def create_submission(submission: SubmissionCreate, request: Request):
    """Create a new submission"""
    settings = await fetch_site_settings()

    # If reCAPTCHA is enabled, require keys to be present
    if settings.get("recaptcha_enable_submit"):
        if not settings.get("recaptcha_site_key") or not settings.get("recaptcha_secret_key"):
            raise HTTPException(status_code=400, detail="reCAPTCHA is enabled but not configured")

        ok = await verify_recaptcha(
            submission.recaptcha_token,
            request.client.host if request.client else None,
            settings.get("recaptcha_secret_key", ""),
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Invalid reCAPTCHA. Please try again.")
    else:
        if not await verify_captcha(submission.captcha_id, submission.captcha_answer):
            raise HTTPException(status_code=400, detail="Invalid captcha. Please try again.")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get rate limit settings
    daily_limit = settings.get("daily_submission_limit", 10)
    
    # Check rate limit by IP
    client_ip = request.client.host if request.client else "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": client_ip, "date": today}, {"_id": 0})
    
    if rate_entry and rate_entry.get("count", 0) >= daily_limit:
        raise HTTPException(
            status_code=429, 
            detail=f"Daily submission limit ({daily_limit}) reached. Try again tomorrow."
        )
    # Update rate limit counter
    await db.rate_limits.update_one(
        {"ip_address": client_ip, "date": today},
        {"$inc": {"count": 1}},
        upsert=True
    )

    # Parse file size to bytes
    file_size_bytes = parse_file_size_to_bytes(submission.file_size) if submission.file_size else None

    submission_obj = Submission(
        name=submission.name,
        download_link=submission.download_link,
        type=submission.type,
        submission_date=today,
        seen_by_admin=False,
        file_size=submission.file_size,
        file_size_bytes=file_size_bytes,
        description=submission.description,
        category=submission.category,
        tags=submission.tags or [],
        site_name=submission.site_name,
        site_url=validate_http_url(submission.site_url),
        submitter_email=submission.submitter_email,
    )

    doc = submission_obj.model_dump()
    await db.submissions.insert_one(doc)

    # Emails (one per request)
    if submission.submitter_email:
        asyncio.create_task(send_submission_email(submission.submitter_email, doc))

    asyncio.create_task(send_admin_submissions_summary([doc]))

    # auto-approve if enabled
    if settings.get("auto_approve_submissions"):
        download_obj = Download(
            name=doc["name"],
            download_link=doc["download_link"],
            type=doc["type"],
            submission_date=doc["submission_date"],
            approved=True,
            file_size=doc.get("file_size"),
            file_size_bytes=doc.get("file_size_bytes"),
            description=doc.get("description"),
            category=doc.get("category"),
            tags=doc.get("tags", []),
            site_name=doc.get("site_name"),
            site_url=doc.get("site_url")
        )
        await db.downloads.insert_one(download_obj.model_dump())
        await db.submissions.update_one({"id": submission_obj.id}, {"$set": {"status": "approved", "seen_by_admin": True}})

    return submission_obj


@router.post("/submissions/bulk")
async def create_submissions_bulk(payload: BulkSubmissionCreate, request: Request):
    """Create multiple submissions at once"""
    settings = await fetch_site_settings()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_limit = settings.get("daily_submission_limit", 10)

    client_ip = request.client.host if request.client else "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": client_ip, "date": today}, {"_id": 0})
    used = rate_entry.get("count", 0) if rate_entry else 0

    requested_count = len(payload.items)
    if requested_count <= 0:
        raise HTTPException(status_code=400, detail="No items provided")

    if used + requested_count > daily_limit:
        raise HTTPException(status_code=429, detail=f"Daily submission limit ({daily_limit}) exceeded")

    # captcha / recaptcha verification once for whole batch
    if settings.get("recaptcha_enable_submit"):
        if not settings.get("recaptcha_site_key") or not settings.get("recaptcha_secret_key"):
            raise HTTPException(status_code=400, detail="reCAPTCHA is enabled but not configured")
        ok = await verify_recaptcha(
            payload.recaptcha_token,
            request.client.host if request.client else None,
            settings.get("recaptcha_secret_key", ""),
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Invalid reCAPTCHA. Please try again.")
    else:
        if not await verify_captcha(payload.captcha_id, payload.captcha_answer):
            raise HTTPException(status_code=400, detail="Invalid captcha. Please try again.")

    # increment rate limit by number of items
    await db.rate_limits.update_one(
        {"ip_address": client_ip, "date": today},
        {"$inc": {"count": requested_count}},
        upsert=True
    )

    created_docs = []
    for s in payload.items:
        file_size_bytes = parse_file_size_to_bytes(s.file_size) if s.file_size else None
        submission_obj = Submission(
            name=s.name,
            download_link=s.download_link,
            type=s.type,
            submission_date=today,
            seen_by_admin=False,
            file_size=s.file_size,
            file_size_bytes=file_size_bytes,
            description=s.description,
            category=s.category,
            tags=s.tags or [],
            site_name=s.site_name,
            site_url=validate_http_url(s.site_url),
            submitter_email=(payload.submitter_email or s.submitter_email)
        )
        doc = submission_obj.model_dump()
        await db.submissions.insert_one(doc)
        created_docs.append(doc)

    # emails (one per request)
    email = (payload.submitter_email or '').strip()
    if email:
        asyncio.create_task(send_bulk_submission_email(email, created_docs))

    asyncio.create_task(send_admin_submissions_summary(created_docs))

    # auto-approve if enabled
    if settings.get("auto_approve_submissions"):
        for doc in created_docs:
            download_obj = Download(
                name=doc["name"],
                download_link=doc["download_link"],
                type=doc["type"],
                submission_date=doc["submission_date"],
                approved=True,
                file_size=doc.get("file_size"),
                file_size_bytes=doc.get("file_size_bytes"),
                description=doc.get("description"),
                category=doc.get("category"),
                tags=doc.get("tags", []),
                site_name=doc.get("site_name"),
                site_url=doc.get("site_url")
            )
            await db.downloads.insert_one(download_obj.model_dump())
            await db.submissions.update_one({"id": doc["id"]}, {"$set": {"status": "approved", "seen_by_admin": True}})

    return {"success": True, "count": len(created_docs)}


@router.get("/submissions/remaining")
async def get_remaining_submissions(request: Request):
    """Check remaining submissions for today"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    settings = await fetch_site_settings()
    daily_limit = settings.get("daily_submission_limit", 10)
    
    client_ip = request.client.host if request.client else "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": client_ip, "date": today}, {"_id": 0})
    
    used = rate_entry.get("count", 0) if rate_entry else 0
    remaining = max(0, daily_limit - used)
    
    return {"daily_limit": daily_limit, "used": used, "remaining": remaining}
