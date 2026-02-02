"""Downloads router - public download endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone, timedelta

from services.database import db
from services.email import fetch_site_settings
from services.utils import parse_file_size_to_bytes
from models.schemas import PaginatedDownloads, Download, ThemeSettings, ThemeUpdate

router = APIRouter(tags=["downloads"])


@router.get("/")
async def root():
    return {"message": "Download Portal API"}


@router.get("/downloads", response_model=PaginatedDownloads)
async def get_downloads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query("date_desc"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    size_min: Optional[str] = None,
    size_max: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None
):
    skip = (page - 1) * limit
    query = {"approved": True}
    
    if type_filter and type_filter != "all":
        query["type"] = type_filter
    if search and search.strip():
        query["name"] = {"$regex": search.strip(), "$options": "i"}
    if category:
        query["category"] = category
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query["tags"] = {"$in": tag_list}
    
    # Date range filter
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        if date_query:
            query["submission_date"] = date_query
    
    # File size filter
    if size_min or size_max:
        size_query = {}
        if size_min:
            min_bytes = parse_file_size_to_bytes(size_min)
            if min_bytes:
                size_query["$gte"] = min_bytes
        if size_max:
            max_bytes = parse_file_size_to_bytes(size_max)
            if max_bytes:
                size_query["$lte"] = max_bytes
        if size_query:
            query["file_size_bytes"] = size_query
    
    # Sorting
    sort_field = "created_at"
    sort_order = -1
    if sort_by == "date_desc":
        sort_field, sort_order = "created_at", -1
    elif sort_by == "date_asc":
        sort_field, sort_order = "created_at", 1
    elif sort_by == "downloads_desc":
        sort_field, sort_order = "download_count", -1
    elif sort_by == "downloads_asc":
        sort_field, sort_order = "download_count", 1
    elif sort_by == "name_asc":
        sort_field, sort_order = "name", 1
    elif sort_by == "name_desc":
        sort_field, sort_order = "name", -1
    elif sort_by == "size_desc":
        sort_field, sort_order = "file_size_bytes", -1
    elif sort_by == "size_asc":
        sort_field, sort_order = "file_size_bytes", 1
    
    total = await db.downloads.count_documents(query)
    pages = max((total + limit - 1) // limit, 1)
    
    downloads = await db.downloads.find(query, {"_id": 0}).sort(sort_field, sort_order).skip(skip).limit(limit).to_list(limit)
    
    return PaginatedDownloads(items=downloads, total=total, page=page, pages=pages)


@router.get("/downloads/top")
async def get_top_downloads():
    """Get top downloads including sponsored"""
    settings = await fetch_site_settings()
    
    enabled = settings.get("top_downloads_enabled", True)
    count = settings.get("top_downloads_count", 5)
    sponsored = settings.get("sponsored_downloads", [])
    
    if not enabled:
        return {"enabled": False, "items": [], "sponsored": []}
    
    remaining_count = max(0, count - len(sponsored))
    top = []
    if remaining_count > 0:
        top = await db.downloads.find(
            {"approved": True},
            {"_id": 0}
        ).sort("download_count", -1).limit(remaining_count).to_list(remaining_count)
    
    return {
        "enabled": True,
        "sponsored": sponsored[:5],
        "items": top,
        "total_slots": count
    }


@router.post("/downloads/{download_id}/increment")
async def increment_download_count(download_id: str):
    """Increment download count"""
    result = await db.downloads.update_one(
        {"id": download_id},
        {"$inc": {"download_count": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"success": True}


@router.get("/downloads/trending")
async def get_trending_downloads():
    """Get trending downloads based on recent activity"""
    settings = await fetch_site_settings()
    
    enabled = settings.get("trending_downloads_enabled", False)
    count = settings.get("trending_downloads_count", 5)
    
    if not enabled:
        return {"enabled": False, "items": []}
    
    # Get downloads with activity in the last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    # Aggregate recent download activity
    pipeline = [
        {"$match": {"timestamp": {"$gte": seven_days_ago}}},
        {"$group": {"_id": "$download_id", "recent_count": {"$sum": 1}}},
        {"$sort": {"recent_count": -1}},
        {"$limit": count}
    ]
    
    trending_ids = []
    async for doc in db.download_activity.aggregate(pipeline):
        trending_ids.append(doc["_id"])
    
    # Fetch the actual download documents
    trending = []
    if trending_ids:
        trending = await db.downloads.find(
            {"id": {"$in": trending_ids}, "approved": True},
            {"_id": 0}
        ).to_list(count)
        
        # Sort by the order of trending_ids (most active first)
        id_to_download = {d["id"]: d for d in trending}
        trending = [id_to_download[tid] for tid in trending_ids if tid in id_to_download]
    
    # If we don't have enough trending data, fall back to most downloaded overall
    if len(trending) < count:
        existing_ids = [t["id"] for t in trending]
        fallback = await db.downloads.find(
            {"approved": True, "id": {"$nin": existing_ids}},
            {"_id": 0}
        ).sort("download_count", -1).limit(count - len(trending)).to_list(count)
        trending.extend(fallback)
    
    return {
        "enabled": True,
        "items": trending[:count]
    }


@router.post("/downloads/{download_id}/track")
async def track_download_activity(download_id: str):
    """Track a download click for trending calculation"""
    # First increment the download count
    result = await db.downloads.update_one(
        {"id": download_id},
        {"$inc": {"download_count": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Also record the activity for trending calculation
    await db.download_activity.insert_one({
        "download_id": download_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True}


@router.post("/sponsored/{sponsored_id}/click")
async def track_sponsored_click(sponsored_id: str):
    """Track a click on a sponsored download"""
    await db.sponsored_clicks.insert_one({
        "sponsored_id": sponsored_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True}


# Theme endpoints
@router.get("/theme", response_model=ThemeSettings)
async def get_theme():
    """Get current theme settings"""
    theme = await db.theme.find_one({"id": "global_theme"}, {"_id": 0})
    if not theme:
        theme = ThemeSettings().model_dump()
        await db.theme.insert_one(theme)
    return ThemeSettings(**theme)


@router.put("/theme", response_model=ThemeSettings)
async def update_theme(update: ThemeUpdate):
    """Update theme settings"""
    current = await db.theme.find_one({"id": "global_theme"}, {"_id": 0})
    if not current:
        current = ThemeSettings().model_dump()
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    current.update(update_data)
    
    await db.theme.update_one(
        {"id": "global_theme"},
        {"$set": current},
        upsert=True
    )
    return ThemeSettings(**current)


# Categories and Tags
@router.get("/categories")
async def get_categories(type_filter: Optional[str] = None):
    """Get all categories"""
    query = {}
    if type_filter and type_filter != "all":
        query["$or"] = [{"type": type_filter}, {"type": "all"}]
    categories = await db.categories.find(query, {"_id": 0}).to_list(100)
    return categories


@router.get("/tags")
async def get_popular_tags(limit: int = Query(50, ge=1, le=100)):
    """Get popular tags from downloads"""
    pipeline = [
        {"$match": {"approved": True}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    tags = []
    async for doc in db.downloads.aggregate(pipeline):
        tags.append({"name": doc["_id"], "count": doc["count"]})
    return tags


# Public settings
@router.get("/settings")
async def get_site_settings_public():
    """Get public site settings (excluding sensitive data)"""
    settings = await fetch_site_settings()
    # Remove sensitive fields
    settings.pop("resend_api_key", None)
    settings.pop("recaptcha_secret_key", None)
    settings.pop("admin_password_hash", None)
    return settings


@router.get("/recaptcha/settings")
async def get_recaptcha_settings_public():
    """Get reCAPTCHA settings for frontend"""
    settings = await fetch_site_settings()
    return {
        "site_key": settings.get("recaptcha_site_key"),
        "enable_submit": settings.get("recaptcha_enable_submit", False),
        "enable_auth": settings.get("recaptcha_enable_auth", False),
    }


# Stats
@router.get("/stats")
async def get_stats():
    """Get download statistics"""
    total = await db.downloads.count_documents({"approved": True})
    games = await db.downloads.count_documents({"approved": True, "type": "game"})
    software = await db.downloads.count_documents({"approved": True, "type": "software"})
    movies = await db.downloads.count_documents({"approved": True, "type": "movie"})
    tv_shows = await db.downloads.count_documents({"approved": True, "type": "tv_show"})
    
    # Get total downloads
    result = await db.downloads.aggregate([
        {"$match": {"approved": True}},
        {"$group": {"_id": None, "total_downloads": {"$sum": "$download_count"}}}
    ]).to_list(1)
    total_downloads = result[0]["total_downloads"] if result else 0
    
    return {
        "total": total,
        "games": games,
        "software": software,
        "movies": movies,
        "tv_shows": tv_shows,
        "total_downloads": total_downloads
    }
