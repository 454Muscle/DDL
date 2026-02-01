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

class DownloadCreate(BaseModel):
    name: str
    download_link: str
    type: str  # game, software, movie, tv_show

class Submission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    download_link: str
    type: str
    submission_date: str
    status: str = "pending"  # pending, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SubmissionCreate(BaseModel):
    name: str
    download_link: str
    type: str

class ThemeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global_theme"
    mode: str = "dark"  # dark or light
    accent_color: str = "#00FF41"  # matrix green default

class ThemeUpdate(BaseModel):
    mode: Optional[str] = None
    accent_color: Optional[str] = None

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
    type_filter: Optional[str] = None
):
    skip = (page - 1) * limit
    query = {"approved": True}
    if type_filter and type_filter != "all":
        query["type"] = type_filter
    
    total = await db.downloads.count_documents(query)
    pages = (total + limit - 1) // limit
    
    downloads = await db.downloads.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return PaginatedDownloads(items=downloads, total=total, page=page, pages=pages)

# Submissions - Public
@api_router.post("/submissions", response_model=Submission)
async def create_submission(submission: SubmissionCreate):
    submission_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    submission_obj = Submission(
        name=submission.name,
        download_link=submission.download_link,
        type=submission.type,
        submission_date=submission_date
    )
    doc = submission_obj.model_dump()
    await db.submissions.insert_one(doc)
    return submission_obj

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
        approved=True
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
