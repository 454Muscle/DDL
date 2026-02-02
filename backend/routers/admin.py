"""Admin router - admin-only endpoints"""
import asyncio
import random
import uuid
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone, timedelta
from typing import Optional

from services.database import db, ADMIN_PASSWORD, FRONTEND_URL
from services.email import fetch_site_settings, send_email_via_resend, send_approval_email
from services.utils import hash_password, generate_token
from models.schemas import (
    AdminLogin, AdminInitRequest, AdminChangePasswordRequest,
    AdminForgotPasswordRequest, AdminUpdateEmailRequest,
    PasswordResetConfirmRequest, TokenOnlyRequest, ResendSettingsUpdate,
    SiteSettingsUpdate, PaginatedDownloads, PaginatedSubmissions,
    Download, Category, CategoryCreate
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/init")
async def admin_init(payload: AdminInitRequest):
    """Initialize admin credentials"""
    settings = await fetch_site_settings()
    if settings.get("admin_password_hash"):
        raise HTTPException(status_code=400, detail="Admin is already initialized")

    settings["admin_email"] = payload.email.lower()
    settings["admin_password_hash"] = hash_password(payload.password)

    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)
    return {"success": True}


@router.post("/login")
async def admin_login(login: AdminLogin):
    """Admin login"""
    settings = await fetch_site_settings()
    # Prefer DB-stored password hash; fallback to env for bootstrap
    if settings.get("admin_password_hash"):
        if hash_password(login.password) == settings.get("admin_password_hash"):
            return {"success": True, "message": "Access granted"}
    else:
        if login.password == ADMIN_PASSWORD:
            return {"success": True, "message": "Access granted"}

    raise HTTPException(status_code=401, detail="Invalid password")


@router.post("/password/change/request")
async def admin_request_password_change(payload: AdminChangePasswordRequest):
    """Request admin password change (requires current password)"""
    settings = await fetch_site_settings()
    if not settings.get("admin_email"):
        raise HTTPException(status_code=400, detail="Admin email is not configured")

    # Require current password
    if settings.get("admin_password_hash"):
        if hash_password(payload.current_password) != settings.get("admin_password_hash"):
            raise HTTPException(status_code=401, detail="Invalid current password")
    else:
        if payload.current_password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid current password")

    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=30)).isoformat()

    # store pending token
    await db.admin_password_resets.insert_one({
        "token": token,
        "new_password_hash": hash_password(payload.new_password),
        "created_at": now.isoformat(),
        "expires_at": expires_at,
        "type": "change"
    })

    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL is not configured")

    link = f"{FRONTEND_URL}/admin/confirm-password-change?token={token}"
    html = f"""
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Confirm Admin Password Change</h2>
      <p>Click the link below to confirm your admin password change. This link expires in 30 minutes.</p>
      <p><a href='{link}'>Confirm password change</a></p>
    </body></html>
    """

    ok = await send_email_via_resend(settings["admin_email"], "Confirm admin password change", html)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

    return {"success": True}


@router.post("/forgot-password")
async def admin_forgot_password(payload: AdminForgotPasswordRequest):
    """Admin forgot password"""
    settings = await fetch_site_settings()

    # Admin must be initialized first
    if not settings.get("admin_email") or not settings.get("admin_password_hash"):
        raise HTTPException(status_code=400, detail="Admin is not initialized")

    # do not reveal if emails mismatch (still return success)
    if payload.email.lower() != settings.get("admin_email"):
        return {"success": True}

    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=30)).isoformat()

    await db.admin_password_resets.insert_one({
        "token": token,
        "new_password_hash": None,
        "created_at": now.isoformat(),
        "expires_at": expires_at,
        "type": "forgot"
    })

    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL is not configured")

    link = f"{FRONTEND_URL}/admin/reset-password?token={token}"
    html = f"""
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Reset Admin Password</h2>
      <p>Click the link below to set a new admin password. This link expires in 30 minutes.</p>
      <p><a href='{link}'>Reset admin password</a></p>
    </body></html>
    """

    await send_email_via_resend(settings["admin_email"], "Reset admin password", html)
    return {"success": True}


@router.post("/reset-password")
async def admin_reset_password(payload: PasswordResetConfirmRequest):
    """Confirm admin password reset"""
    settings = await fetch_site_settings()
    req = await db.admin_password_resets.find_one({"token": payload.token}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        exp = datetime.fromisoformat(req["expires_at"])
    except Exception:
        exp = datetime.now(timezone.utc)
    if exp < datetime.now(timezone.utc):
        await db.admin_password_resets.delete_one({"token": payload.token})
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    settings["admin_password_hash"] = hash_password(payload.new_password)
    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)

    await db.admin_password_resets.delete_one({"token": payload.token})
    return {"success": True}


@router.post("/password/change/confirm")
async def admin_confirm_password_change(payload: TokenOnlyRequest):
    """Confirm admin password change"""
    settings = await fetch_site_settings()
    req = await db.admin_password_resets.find_one({"token": payload.token}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # check expiry
    try:
        exp = datetime.fromisoformat(req["expires_at"])
    except Exception:
        exp = datetime.now(timezone.utc)
    if exp < datetime.now(timezone.utc):
        await db.admin_password_resets.delete_one({"token": payload.token})
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if req.get("type") != "change":
        raise HTTPException(status_code=400, detail="Invalid token")

    # update admin password hash
    settings["admin_password_hash"] = req["new_password_hash"]
    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)

    await db.admin_password_resets.delete_one({"token": payload.token})
    return {"success": True}


@router.post("/email/update")
async def admin_update_email(payload: AdminUpdateEmailRequest):
    """Update admin email (requires current password)"""
    settings = await fetch_site_settings()
    if settings.get("admin_password_hash"):
        if hash_password(payload.current_password) != settings.get("admin_password_hash"):
            raise HTTPException(status_code=401, detail="Invalid current password")
    else:
        if not ADMIN_PASSWORD or payload.current_password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid current password")

    settings["admin_email"] = payload.new_email.lower()
    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)
    return {"success": True}


# ===== SUBMISSIONS MANAGEMENT =====

@router.get("/submissions", response_model=PaginatedSubmissions)
async def get_submissions(page: int = 1, limit: int = 20, status: Optional[str] = None):
    """Get submissions with optional status filter"""
    skip = (page - 1) * limit
    
    # Build filter based on status param
    query = {}
    if status and status in ["pending", "approved", "rejected"]:
        query["status"] = status
    
    submissions = await db.submissions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # mark returned submissions as seen (only for pending)
    if status == "pending" or not status:
        ids = [s.get("id") for s in submissions if s.get("id") and s.get("status") == "pending"]
        if ids:
            await db.submissions.update_many({"id": {"$in": ids}}, {"$set": {"seen_by_admin": True}})

    total = await db.submissions.count_documents(query)
    pages = (total + limit - 1) // limit

    return {
        "items": submissions,
        "total": total,
        "page": page,
        "pages": pages
    }


@router.get("/submissions/unseen-count")
async def admin_unseen_submissions_count():
    """Get count of pending submissions"""
    settings = await fetch_site_settings()
    if settings.get("auto_approve_submissions"):
        return {"count": 0}

    # Count all pending submissions (unseen or not) for the notification badge
    count = await db.submissions.count_documents({"status": "pending"})
    return {"count": count}


@router.post("/submissions/{submission_id}/approve")
async def approve_submission(submission_id: str):
    """Approve a submission"""
    submission = await db.submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    download_obj = Download(
        name=submission["name"],
        download_link=submission["download_link"],
        type=submission["type"],
        submission_date=submission["submission_date"],
        approved=True,
        file_size=submission.get("file_size"),
        file_size_bytes=submission.get("file_size_bytes"),
        description=submission.get("description"),
        category=submission.get("category"),
        tags=submission.get("tags", []),
        site_name=submission.get("site_name"),
        site_url=submission.get("site_url")
    )
    
    await db.downloads.insert_one(download_obj.model_dump())
    await db.submissions.update_one({"id": submission_id}, {"$set": {"status": "approved"}})
    
    # Send approval notification email to submitter (async, non-blocking)
    submitter_email = submission.get("submitter_email")
    if submitter_email:
        asyncio.create_task(send_approval_email(submitter_email, submission))
    
    return {"success": True, "message": "Submission approved"}


@router.post("/submissions/{submission_id}/reject")
async def reject_submission(submission_id: str):
    """Reject a submission"""
    result = await db.submissions.update_one({"id": submission_id}, {"$set": {"status": "rejected"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"success": True, "message": "Submission rejected"}


@router.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: str):
    """Delete a submission"""
    result = await db.submissions.delete_one({"id": submission_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"success": True}


# ===== DOWNLOADS MANAGEMENT =====

@router.get("/downloads", response_model=PaginatedDownloads)
async def admin_search_downloads(search: str = Query(""), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    """Search downloads (admin)"""
    query = {"approved": True}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    total = await db.downloads.count_documents(query)
    pages = (total + limit - 1) // limit
    skip = (page - 1) * limit

    items = await db.downloads.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }


@router.delete("/downloads/{download_id}")
async def delete_download(download_id: str):
    """Delete a download"""
    result = await db.downloads.delete_one({"id": download_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"success": True, "message": "Download deleted"}


# ===== SPONSORED ANALYTICS =====

@router.get("/sponsored/analytics")
async def get_sponsored_analytics():
    """Get click analytics for all sponsored downloads"""
    settings = await fetch_site_settings()
    sponsored = settings.get("sponsored_downloads", [])
    
    analytics = []
    for item in sponsored:
        item_id = item.get("id", "")
        
        # Get total clicks
        total_clicks = await db.sponsored_clicks.count_documents({"sponsored_id": item_id})
        
        # Get clicks in last 24 hours
        day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        clicks_24h = await db.sponsored_clicks.count_documents({
            "sponsored_id": item_id,
            "timestamp": {"$gte": day_ago}
        })
        
        # Get clicks in last 7 days
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        clicks_7d = await db.sponsored_clicks.count_documents({
            "sponsored_id": item_id,
            "timestamp": {"$gte": week_ago}
        })
        
        analytics.append({
            "id": item_id,
            "name": item.get("name", "Unknown"),
            "total_clicks": total_clicks,
            "clicks_24h": clicks_24h,
            "clicks_7d": clicks_7d
        })
    
    return {"analytics": analytics}


# ===== CATEGORIES =====

@router.post("/categories")
async def create_category(category: CategoryCreate):
    """Create a category"""
    # Check if exists
    existing = await db.categories.find_one({"name": category.name, "type": category.type}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    cat_obj = Category(name=category.name, type=category.type)
    await db.categories.insert_one(cat_obj.model_dump())
    return cat_obj.model_dump()


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    """Delete a category"""
    result = await db.categories.delete_one({"id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True}


# ===== RESEND EMAIL SETTINGS =====

@router.post("/resend/test")
async def resend_test_email():
    """Send test email via Resend"""
    settings = await fetch_site_settings()
    if not settings.get("admin_email"):
        raise HTTPException(status_code=400, detail="Admin email is not configured")

    html = """
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Resend Test Email</h2>
      <p>This is a test email to confirm your Resend configuration is working.</p>
    </body></html>
    """

    ok = await send_email_via_resend(settings["admin_email"], "Resend test email", html)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send test email")

    return {"success": True}


@router.put("/resend")
async def update_resend_settings(update: ResendSettingsUpdate):
    """Update Resend settings"""
    settings = await fetch_site_settings()

    if update.resend_api_key is not None:
        settings["resend_api_key"] = update.resend_api_key.strip() or None

    if update.resend_sender_email is not None:
        settings["resend_sender_email"] = update.resend_sender_email.strip() or None

    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)

    # never return api key in response
    settings = dict(settings)
    settings["resend_api_key"] = None
    settings["recaptcha_secret_key"] = None
    return settings


# ===== SITE SETTINGS =====

@router.put("/settings")
async def update_site_settings(update: SiteSettingsUpdate):
    """Update site settings"""
    settings = await fetch_site_settings()
    
    if update.daily_submission_limit is not None:
        settings["daily_submission_limit"] = max(5, min(100, update.daily_submission_limit))
    
    if update.top_downloads_enabled is not None:
        settings["top_downloads_enabled"] = update.top_downloads_enabled
    
    if update.top_downloads_count is not None:
        settings["top_downloads_count"] = max(5, min(20, update.top_downloads_count))
    
    if update.sponsored_downloads is not None:
        settings["sponsored_downloads"] = update.sponsored_downloads[:5]

    if update.recaptcha_site_key is not None:
        settings["recaptcha_site_key"] = update.recaptcha_site_key.strip() or None

    if update.recaptcha_secret_key is not None:
        settings["recaptcha_secret_key"] = update.recaptcha_secret_key.strip() or None

    if update.recaptcha_enable_submit is not None:
        settings["recaptcha_enable_submit"] = bool(update.recaptcha_enable_submit)

    if update.recaptcha_enable_auth is not None:
        settings["recaptcha_enable_auth"] = bool(update.recaptcha_enable_auth)

    # If either toggle is enabled, require both keys
    if (settings.get("recaptcha_enable_submit") or settings.get("recaptcha_enable_auth")) and (
        not settings.get("recaptcha_site_key") or not settings.get("recaptcha_secret_key")
    ):
        raise HTTPException(status_code=400, detail="reCAPTCHA keys are required when enabling reCAPTCHA")

    # Branding / typography
    if update.site_name is not None:
        settings["site_name"] = update.site_name.strip() or None

    if update.site_name_font_family is not None:
        settings["site_name_font_family"] = update.site_name_font_family

    if update.site_name_font_weight is not None:
        settings["site_name_font_weight"] = update.site_name_font_weight

    if update.site_name_font_color is not None:
        settings["site_name_font_color"] = update.site_name_font_color

    if update.body_font_family is not None:
        settings["body_font_family"] = update.body_font_family

    if update.body_font_weight is not None:
        settings["body_font_weight"] = update.body_font_weight

    # Footer
    if update.footer_enabled is not None:
        settings["footer_enabled"] = bool(update.footer_enabled)

    if update.footer_line1_template is not None:
        settings["footer_line1_template"] = update.footer_line1_template

    if update.footer_line2_template is not None:
        settings["footer_line2_template"] = update.footer_line2_template

    # Trending downloads settings
    if update.trending_downloads_enabled is not None:
        settings["trending_downloads_enabled"] = bool(update.trending_downloads_enabled)

    if update.trending_downloads_count is not None:
        settings["trending_downloads_count"] = max(5, min(20, update.trending_downloads_count))

    # Submissions workflow
    if update.auto_approve_submissions is not None:
        settings["auto_approve_submissions"] = bool(update.auto_approve_submissions)

    # Admin email (can be updated anytime)
    if update.admin_email is not None:
        settings["admin_email"] = update.admin_email.lower().strip() if update.admin_email else None

    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings},
        upsert=True
    )
    return settings


# ===== SEED DATABASE =====

@router.post("/seed")
async def seed_database():
    """Seed database with sample data"""
    count = await db.downloads.count_documents({})
    if count >= 5000:
        return {"success": False, "message": f"Database already has {count} items"}
    
    await db.downloads.delete_many({})
    
    # Seed default categories
    default_categories = [
        {"name": "Action", "type": "game"}, {"name": "RPG", "type": "game"}, {"name": "Strategy", "type": "game"},
        {"name": "FPS", "type": "game"}, {"name": "Racing", "type": "game"}, {"name": "Sports", "type": "game"},
        {"name": "Productivity", "type": "software"}, {"name": "Development", "type": "software"},
        {"name": "Graphics", "type": "software"}, {"name": "Utilities", "type": "software"},
        {"name": "Action", "type": "movie"}, {"name": "Comedy", "type": "movie"}, {"name": "Drama", "type": "movie"},
        {"name": "Sci-Fi", "type": "movie"}, {"name": "Horror", "type": "movie"}, {"name": "Thriller", "type": "movie"},
        {"name": "Drama", "type": "tv_show"}, {"name": "Comedy", "type": "tv_show"}, {"name": "Sci-Fi", "type": "tv_show"},
        {"name": "Crime", "type": "tv_show"}, {"name": "Documentary", "type": "tv_show"}
    ]
    
    for cat in default_categories:
        existing = await db.categories.find_one({"name": cat["name"], "type": cat["type"]}, {"_id": 0})
        if not existing:
            cat_obj = Category(name=cat["name"], type=cat["type"])
            await db.categories.insert_one(cat_obj.model_dump())
    
    # Sample data generators
    game_prefixes = ["Super", "Mega", "Ultra", "Epic", "Cyber", "Dark", "Shadow", "Crystal", "Dragon", "Space"]
    game_suffixes = ["Warriors", "Quest", "Saga", "Chronicles", "Adventures", "Legends", "Heroes", "Knights"]
    game_categories = ["Action", "RPG", "Strategy", "FPS", "Racing", "Sports"]
    game_tags = ["multiplayer", "singleplayer", "co-op", "open-world", "indie", "AAA", "remastered", "GOTY"]
    
    software_names = [
        "VLC Media Player", "GIMP Image Editor", "Audacity Audio Editor", "LibreOffice Suite", "Firefox Browser",
        "Blender 3D", "Inkscape Vector", "OBS Studio", "HandBrake Video", "7-Zip Archiver",
        "Notepad++ Editor", "FileZilla FTP", "KeePass Password", "Thunderbird Mail", "XAMPP Server",
        "TurboOffice Pro", "DataMaster Suite", "CodeForge IDE", "PhotoMax Studio", "VideoFlex Editor"
    ]
    software_categories = ["Productivity", "Development", "Graphics", "Utilities"]
    software_tags = ["portable", "open-source", "freeware", "cross-platform", "windows", "mac", "linux"]
    
    movie_genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Thriller"]
    movie_tags = ["720p", "1080p", "4K", "HDR", "BluRay", "WEB-DL", "subtitles", "dual-audio"]
    
    tv_shows = [
        ("Quantum Detective", 5), ("Starship Voyagers", 7), ("The Last Frontier", 4), ("Midnight City", 6),
        ("Corporate Chaos", 3), ("Medical Mayhem", 8), ("Legal Eagles", 5), ("Cooking Catastrophe", 4)
    ]
    tv_categories = ["Drama", "Comedy", "Sci-Fi", "Crime", "Documentary"]
    tv_tags = ["complete-season", "ongoing", "finale", "premiere", "HDTV", "WEB-DL"]
    
    downloads = []
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    # Generate games (~1500)
    for i in range(1500):
        prefix = random.choice(game_prefixes)
        suffix = random.choice(game_suffixes)
        version = f"{random.randint(1,3)}.{random.randint(0,9)}"
        name = f"{prefix} {suffix} {version}"
        
        days_offset = random.randint(0, 365)
        date = base_date + timedelta(days=days_offset)
        size_gb = random.randint(5, 100)
        size = f"{size_gb}.{random.randint(0,9)} GB"
        size_bytes = size_gb * 1024 * 1024 * 1024
        
        downloads.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "download_link": f"https://example.com/games/{uuid.uuid4().hex[:8]}",
            "type": "game",
            "submission_date": date.strftime("%Y-%m-%d"),
            "approved": True,
            "created_at": date.isoformat(),
            "download_count": random.randint(0, 50000),
            "file_size": size,
            "file_size_bytes": size_bytes,
            "description": f"Epic {random.choice(['adventure', 'action', 'strategy'])} game",
            "category": random.choice(game_categories),
            "tags": random.sample(game_tags, random.randint(2, 4))
        })
    
    # Generate software (~1200)
    for i in range(1200):
        base_name = random.choice(software_names)
        version = f"{random.randint(1,25)}.{random.randint(0,9)}.{random.randint(0,999)}"
        name = f"{base_name} v{version}"
        
        days_offset = random.randint(0, 365)
        date = base_date + timedelta(days=days_offset)
        size_mb = random.randint(10, 2000)
        size = f"{size_mb} MB"
        size_bytes = size_mb * 1024 * 1024
        
        downloads.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "download_link": f"https://example.com/software/{uuid.uuid4().hex[:8]}",
            "type": "software",
            "submission_date": date.strftime("%Y-%m-%d"),
            "approved": True,
            "created_at": date.isoformat(),
            "download_count": random.randint(0, 100000),
            "file_size": size,
            "file_size_bytes": size_bytes,
            "description": f"{'Portable' if random.random() > 0.7 else 'Full'} version",
            "category": random.choice(software_categories),
            "tags": random.sample(software_tags, random.randint(2, 4))
        })
    
    # Generate movies (~1300)
    movie_adjectives = ["The", "A", "Last", "Final", "Dark", "Eternal", "Hidden", "Secret", "Lost"]
    movie_nouns = ["Knight", "Storm", "Journey", "Mission", "Dream", "Night", "Day", "Legacy", "Code"]
    
    for i in range(1300):
        adj = random.choice(movie_adjectives)
        noun = random.choice(movie_nouns)
        year = random.randint(2020, 2025)
        quality = random.choice(["720p", "1080p", "2160p 4K", "BluRay", "WEB-DL"])
        name = f"{adj} {noun} ({year}) {quality}"
        
        days_offset = random.randint(0, 365)
        date = base_date + timedelta(days=days_offset)
        size_gb = random.randint(1, 20)
        size = f"{size_gb}.{random.randint(0,9)} GB"
        size_bytes = size_gb * 1024 * 1024 * 1024
        
        downloads.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "download_link": f"https://example.com/movies/{uuid.uuid4().hex[:8]}",
            "type": "movie",
            "submission_date": date.strftime("%Y-%m-%d"),
            "approved": True,
            "created_at": date.isoformat(),
            "download_count": random.randint(0, 75000),
            "file_size": size,
            "file_size_bytes": size_bytes,
            "description": f"{random.choice(movie_genres)} film",
            "category": random.choice(movie_genres),
            "tags": random.sample(movie_tags, random.randint(2, 4))
        })
    
    # Generate TV shows (~1000)
    for show_name, seasons in tv_shows:
        for season in range(1, seasons + 1):
            episodes = random.randint(8, 24)
            for episode in range(1, episodes + 1):
                if len(downloads) >= 5000:
                    break
                quality = random.choice(["720p", "1080p", "WEB-DL", "HDTV"])
                name = f"{show_name} S{season:02d}E{episode:02d} {quality}"
                
                days_offset = random.randint(0, 365)
                date = base_date + timedelta(days=days_offset)
                size_mb = random.randint(200, 1500)
                size = f"{size_mb} MB"
                size_bytes = size_mb * 1024 * 1024
                
                downloads.append({
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "download_link": f"https://example.com/tv/{uuid.uuid4().hex[:8]}",
                    "type": "tv_show",
                    "submission_date": date.strftime("%Y-%m-%d"),
                    "approved": True,
                    "created_at": date.isoformat(),
                    "download_count": random.randint(0, 30000),
                    "file_size": size,
                    "file_size_bytes": size_bytes,
                    "description": f"Season {season}, Episode {episode}",
                    "category": random.choice(tv_categories),
                    "tags": random.sample(tv_tags, random.randint(2, 3))
                })
            if len(downloads) >= 5000:
                break
        if len(downloads) >= 5000:
            break
    
    downloads = downloads[:5000]
    
    if downloads:
        await db.downloads.insert_many(downloads)
    
    # Create indexes
    await db.downloads.create_index([("name", "text")])
    await db.downloads.create_index([("type", 1)])
    await db.downloads.create_index([("approved", 1)])
    await db.downloads.create_index([("category", 1)])
    await db.downloads.create_index([("tags", 1)])
    await db.downloads.create_index([("file_size_bytes", 1)])
    
    return {"success": True, "message": f"Seeded {len(downloads)} downloads with categories and tags"}
