from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Admin credentials (simple hardcoded)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# ===== MODELS =====

class Download(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    download_link: str
    type: str  # game, software, movie, tv_show
    submission_date: str
    approved: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    download_count: int = 0
    file_size: Optional[str] = None
    description: Optional[str] = None

class DownloadCreate(BaseModel):
    name: str
    download_link: str
    type: str  # game, software, movie, tv_show
    file_size: Optional[str] = None
    description: Optional[str] = None

class Submission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    download_link: str
    type: str
    submission_date: str
    status: str = "pending"  # pending, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_size: Optional[str] = None
    description: Optional[str] = None

class SubmissionCreate(BaseModel):
    name: str
    download_link: str
    type: str
    file_size: Optional[str] = None
    description: Optional[str] = None

class ThemeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global_theme"
    mode: str = "dark"  # dark or light
    accent_color: str = "#00FF41"  # matrix green default

class ThemeUpdate(BaseModel):
    mode: Optional[str] = None
    accent_color: Optional[str] = None

class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "site_settings"
    daily_submission_limit: int = 10  # 5-100 configurable

class SiteSettingsUpdate(BaseModel):
    daily_submission_limit: Optional[int] = None

class RateLimitEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ip_address: str
    date: str
    count: int = 0

class AdminLogin(BaseModel):
    password: str

class PaginatedDownloads(BaseModel):
    items: List[Download]
    total: int
    page: int
    pages: int

class PaginatedSubmissions(BaseModel):
    items: List[Submission]
    total: int
    page: int
    pages: int

# ===== ROUTES =====

@api_router.get("/")
async def root():
    return {"message": "Download Portal API"}

# Downloads - Public
@api_router.get("/downloads", response_model=PaginatedDownloads)
async def get_downloads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query("date_desc", description="Sort options: date_desc, date_asc, downloads_desc, downloads_asc, name_asc, name_desc"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    size_min: Optional[str] = None,
    size_max: Optional[str] = None
):
    skip = (page - 1) * limit
    query = {"approved": True}
    
    if type_filter and type_filter != "all":
        query["type"] = type_filter
    if search and search.strip():
        query["name"] = {"$regex": search.strip(), "$options": "i"}
    
    # Date range filter
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        if date_query:
            query["submission_date"] = date_query
    
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
    
    total = await db.downloads.count_documents(query)
    pages = max((total + limit - 1) // limit, 1)
    
    downloads = await db.downloads.find(query, {"_id": 0}).sort(sort_field, sort_order).skip(skip).limit(limit).to_list(limit)
    
    return PaginatedDownloads(items=downloads, total=total, page=page, pages=pages)

# Top Downloads
@api_router.get("/downloads/top")
async def get_top_downloads(limit: int = Query(10, ge=1, le=20)):
    top = await db.downloads.find(
        {"approved": True},
        {"_id": 0}
    ).sort("download_count", -1).limit(limit).to_list(limit)
    return {"items": top}

# Increment download count
@api_router.post("/downloads/{download_id}/increment")
async def increment_download_count(download_id: str):
    result = await db.downloads.update_one(
        {"id": download_id},
        {"$inc": {"download_count": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"success": True}

# Submissions - Public
@api_router.post("/submissions", response_model=Submission)
async def create_submission(submission: SubmissionCreate, client_ip: Optional[str] = Query(None)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get rate limit settings
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    daily_limit = settings.get("daily_submission_limit", 10) if settings else 10
    
    # Check rate limit by IP (use a simple identifier if no IP provided)
    ip_key = client_ip or "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": ip_key, "date": today}, {"_id": 0})
    
    if rate_entry and rate_entry.get("count", 0) >= daily_limit:
        raise HTTPException(
            status_code=429, 
            detail=f"Daily submission limit ({daily_limit}) reached. Try again tomorrow."
        )
    
    # Update rate limit counter
    await db.rate_limits.update_one(
        {"ip_address": ip_key, "date": today},
        {"$inc": {"count": 1}},
        upsert=True
    )
    
    submission_date = today
    submission_obj = Submission(
        name=submission.name,
        download_link=submission.download_link,
        type=submission.type,
        submission_date=submission_date,
        file_size=submission.file_size,
        description=submission.description
    )
    doc = submission_obj.model_dump()
    await db.submissions.insert_one(doc)
    return submission_obj

# Check remaining submissions for today
@api_router.get("/submissions/remaining")
async def get_remaining_submissions(client_ip: Optional[str] = Query(None)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    daily_limit = settings.get("daily_submission_limit", 10) if settings else 10
    
    ip_key = client_ip or "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": ip_key, "date": today}, {"_id": 0})
    
    used = rate_entry.get("count", 0) if rate_entry else 0
    remaining = max(0, daily_limit - used)
    
    return {"daily_limit": daily_limit, "used": used, "remaining": remaining}

# Admin Login
@api_router.post("/admin/login")
async def admin_login(login: AdminLogin):
    if login.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Access granted"}
    raise HTTPException(status_code=401, detail="Invalid password")

# Admin - Get Pending Submissions
@api_router.get("/admin/submissions", response_model=PaginatedSubmissions)
async def get_admin_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    skip = (page - 1) * limit
    query = {}
    if status:
        query["status"] = status
    
    total = await db.submissions.count_documents(query)
    pages = max((total + limit - 1) // limit, 1)
    
    submissions = await db.submissions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return PaginatedSubmissions(items=submissions, total=total, page=page, pages=pages)

# Admin - Approve Submission
@api_router.post("/admin/submissions/{submission_id}/approve")
async def approve_submission(submission_id: str):
    submission = await db.submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Create download from submission
    download_obj = Download(
        name=submission["name"],
        download_link=submission["download_link"],
        type=submission["type"],
        submission_date=submission["submission_date"],
        approved=True,
        file_size=submission.get("file_size"),
        description=submission.get("description")
    )
    
    await db.downloads.insert_one(download_obj.model_dump())
    await db.submissions.update_one({"id": submission_id}, {"$set": {"status": "approved"}})
    
    return {"success": True, "message": "Submission approved"}

# Admin - Reject Submission
@api_router.post("/admin/submissions/{submission_id}/reject")
async def reject_submission(submission_id: str):
    result = await db.submissions.update_one({"id": submission_id}, {"$set": {"status": "rejected"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"success": True, "message": "Submission rejected"}

# Admin - Delete Submission
@api_router.delete("/admin/submissions/{submission_id}")
async def delete_submission(submission_id: str):
    result = await db.submissions.delete_one({"id": submission_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"success": True, "message": "Submission deleted"}

# Admin - Delete Download
@api_router.delete("/admin/downloads/{download_id}")
async def delete_download(download_id: str):
    result = await db.downloads.delete_one({"id": download_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"success": True, "message": "Download deleted"}

# Theme Settings - Get
@api_router.get("/theme", response_model=ThemeSettings)
async def get_theme():
    theme = await db.theme_settings.find_one({"id": "global_theme"}, {"_id": 0})
    if not theme:
        default_theme = ThemeSettings()
        await db.theme_settings.insert_one(default_theme.model_dump())
        return default_theme
    return ThemeSettings(**theme)

# Theme Settings - Update
@api_router.put("/theme", response_model=ThemeSettings)
async def update_theme(update: ThemeUpdate):
    theme = await db.theme_settings.find_one({"id": "global_theme"}, {"_id": 0})
    if not theme:
        theme = ThemeSettings().model_dump()
    
    if update.mode:
        theme["mode"] = update.mode
    if update.accent_color:
        theme["accent_color"] = update.accent_color
    
    await db.theme_settings.update_one(
        {"id": "global_theme"}, 
        {"$set": theme}, 
        upsert=True
    )
    return ThemeSettings(**theme)

# Site Settings - Get
@api_router.get("/settings")
async def get_site_settings():
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    if not settings:
        default_settings = SiteSettings()
        await db.site_settings.insert_one(default_settings.model_dump())
        return default_settings.model_dump()
    return settings

# Site Settings - Update (Admin)
@api_router.put("/admin/settings")
async def update_site_settings(update: SiteSettingsUpdate):
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    if not settings:
        settings = SiteSettings().model_dump()
    
    if update.daily_submission_limit is not None:
        # Clamp between 5 and 100
        settings["daily_submission_limit"] = max(5, min(100, update.daily_submission_limit))
    
    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings},
        upsert=True
    )
    return settings

# Seed database with sample data
@api_router.post("/admin/seed")
async def seed_database():
    # Check if already seeded
    count = await db.downloads.count_documents({})
    if count >= 5000:
        return {"success": False, "message": f"Database already has {count} items"}
    
    # Clear existing data
    await db.downloads.delete_many({})
    
    # Sample data generators
    game_prefixes = ["Super", "Mega", "Ultra", "Epic", "Cyber", "Dark", "Shadow", "Crystal", "Dragon", "Space", "Battle", "Star", "Legend of", "Tales of", "World of", "Age of", "Rise of", "Fall of", "Dawn of", "Realm of"]
    game_suffixes = ["Warriors", "Quest", "Saga", "Chronicles", "Adventures", "Legends", "Heroes", "Knights", "Hunters", "Fighters", "Racers", "Simulator", "Tactics", "Empire", "Kingdom", "World", "Online", "Remastered", "Definitive Edition", "GOTY"]
    game_themes = ["Fantasy", "Sci-Fi", "Horror", "RPG", "FPS", "Strategy", "Racing", "Sports", "Puzzle", "Platformer"]
    
    software_names = [
        # Real open source
        "VLC Media Player", "GIMP Image Editor", "Audacity Audio Editor", "LibreOffice Suite", "Firefox Browser",
        "Blender 3D", "Inkscape Vector", "OBS Studio", "HandBrake Video", "7-Zip Archiver",
        "Notepad++ Editor", "FileZilla FTP", "KeePass Password", "Thunderbird Mail", "XAMPP Server",
        "Git Version Control", "Python Interpreter", "Node.js Runtime", "VS Code Editor", "Atom Editor",
        "Krita Digital Art", "Scribus Publisher", "Calibre E-Book", "VirtualBox VM", "PuTTY SSH",
        # Fictional
        "TurboOffice Pro", "DataMaster Suite", "CodeForge IDE", "PhotoMax Studio", "VideoFlex Editor",
        "SyncCloud Pro", "BackupGuard Plus", "SystemTuner Pro", "DriverBoost Max", "CleanSweep Ultra",
        "PDFWizard Pro", "ArchiveX Pro", "ScreenCap Pro", "AudioMix Studio", "RenderFarm Pro",
        "DevTools Ultimate", "DBAdmin Pro", "NetMonitor Plus", "SecureVault Pro", "TaskMaster Pro"
    ]
    
    movie_genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller", "Romance", "Adventure", "Mystery", "Fantasy"]
    movie_adjectives = ["The", "A", "Last", "Final", "Dark", "Eternal", "Hidden", "Secret", "Lost", "Forgotten", "Ancient", "New", "Old"]
    movie_nouns = ["Knight", "Storm", "Journey", "Mission", "Dream", "Night", "Day", "Legacy", "Code", "Protocol", "Truth", "Lies", "Shadows", "Light", "War", "Peace", "Love", "Hate", "Fear", "Hope"]
    movie_years = list(range(2020, 2026))
    
    tv_shows = [
        # Fictional shows with seasons
        ("Quantum Detective", 5), ("Starship Voyagers", 7), ("The Last Frontier", 4), ("Midnight City", 6),
        ("Corporate Chaos", 3), ("Medical Mayhem", 8), ("Legal Eagles", 5), ("Cooking Catastrophe", 4),
        ("Reality Breakdown", 6), ("Historical Hijinks", 3), ("Animated Adventures", 9), ("Documentary Deep Dive", 4),
        ("Crime Scene Alpha", 7), ("Supernatural Stories", 5), ("Romantic Rendezvous", 4), ("Family Fiascos", 6),
        ("Teen Turmoil", 5), ("Senior Shenanigans", 3), ("Pet Pandemonium", 4), ("Home Improvement Hell", 5),
        ("Game Show Galore", 8), ("Talk Show Titans", 6), ("News Network Nonsense", 4), ("Sports Spectacular", 7),
        ("Mystery Manor", 5), ("Ghost Hunters Inc", 4), ("Alien Archives", 3), ("Time Travelers", 6),
        ("Robot Revolution", 4), ("Cyber City", 5), ("Virtual Reality", 3), ("Digital Dreams", 4)
    ]
    
    downloads = []
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    # Generate games (~1500)
    for i in range(1500):
        prefix = random.choice(game_prefixes)
        suffix = random.choice(game_suffixes)
        version = f"{random.randint(1,3)}.{random.randint(0,9)}"
        name = f"{prefix} {suffix} {version}"
        if random.random() > 0.7:
            name += f" - {random.choice(game_themes)} Edition"
        
        days_offset = random.randint(0, 365)
        date = base_date + __import__('datetime').timedelta(days=days_offset)
        size = f"{random.randint(5, 100)}.{random.randint(0,9)} GB"
        
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
            "description": f"{random.choice(game_themes)} game with {random.choice(['stunning graphics', 'immersive gameplay', 'multiplayer support', 'mod support', 'achievements'])}"
        })
    
    # Generate software (~1200)
    for i in range(1200):
        base_name = random.choice(software_names)
        version = f"{random.randint(1,25)}.{random.randint(0,9)}.{random.randint(0,999)}"
        name = f"{base_name} v{version}"
        
        days_offset = random.randint(0, 365)
        date = base_date + __import__('datetime').timedelta(days=days_offset)
        size = f"{random.randint(10, 2000)} MB"
        
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
            "description": f"{'Portable' if random.random() > 0.7 else 'Full'} version - {random.choice(['Windows', 'Mac', 'Linux', 'Cross-platform'])}"
        })
    
    # Generate movies (~1300)
    for i in range(1300):
        adj = random.choice(movie_adjectives)
        noun = random.choice(movie_nouns)
        year = random.choice(movie_years)
        genre = random.choice(movie_genres)
        quality = random.choice(["720p", "1080p", "2160p 4K", "BluRay", "WEB-DL", "HDRip"])
        name = f"{adj} {noun} ({year}) {quality}"
        
        days_offset = random.randint(0, 365)
        date = base_date + __import__('datetime').timedelta(days=days_offset)
        size = f"{random.randint(1, 20)}.{random.randint(0,9)} GB"
        
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
            "description": f"{genre} - {random.choice(['English', 'Multi-language'])} - {random.choice(['Subtitles included', 'No subtitles'])}"
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
                date = base_date + __import__('datetime').timedelta(days=days_offset)
                size = f"{random.randint(200, 1500)} MB"
                
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
                    "description": f"Season {season}, Episode {episode}"
                })
            if len(downloads) >= 5000:
                break
        if len(downloads) >= 5000:
            break
    
    # Ensure exactly 5000 items
    downloads = downloads[:5000]
    
    # Bulk insert
    if downloads:
        await db.downloads.insert_many(downloads)
    
    # Create index for search
    await db.downloads.create_index([("name", "text")])
    await db.downloads.create_index([("type", 1)])
    await db.downloads.create_index([("approved", 1)])
    
    return {"success": True, "message": f"Seeded {len(downloads)} downloads"}

# Get statistics
@api_router.get("/stats")
async def get_stats():
    total = await db.downloads.count_documents({"approved": True})
    games = await db.downloads.count_documents({"approved": True, "type": "game"})
    software = await db.downloads.count_documents({"approved": True, "type": "software"})
    movies = await db.downloads.count_documents({"approved": True, "type": "movie"})
    tv_shows = await db.downloads.count_documents({"approved": True, "type": "tv_show"})
    
    # Get top downloaded
    top_downloads = await db.downloads.find(
        {"approved": True}, 
        {"_id": 0, "name": 1, "download_count": 1, "type": 1}
    ).sort("download_count", -1).limit(5).to_list(5)
    
    return {
        "total": total,
        "by_type": {
            "game": games,
            "software": software,
            "movie": movies,
            "tv_show": tv_shows
        },
        "top_downloads": top_downloads
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
