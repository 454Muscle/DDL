from fastapi import FastAPI, APIRouter, HTTPException, Query, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random
import hashlib
import asyncio
import resend

import httpx
from datetime import timedelta


import secrets

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

# Resend email config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://downloadportal-1.preview.emergentagent.com')

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    file_size_bytes: Optional[int] = None  # For filtering
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    site_name: Optional[str] = None
    site_url: Optional[str] = None

class DownloadCreate(BaseModel):
    name: str
    download_link: str
    type: str
    file_size: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class Submission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    download_link: str
    type: str
    submission_date: str
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_size: Optional[str] = None
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    # optional on existing legacy submissions; required on new submissions via SubmissionCreate
    site_name: Optional[str] = None
    site_url: Optional[str] = None
    submitter_email: Optional[str] = None
    submitter_user_id: Optional[str] = None

class SubmissionCreate(BaseModel):
    name: str
    download_link: str
    type: str
    site_name: str = Field(min_length=1, max_length=15)
    site_url: str
    file_size: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    submitter_email: Optional[str] = None
    captcha_answer: Optional[int] = None
    captcha_id: Optional[str] = None
    recaptcha_token: Optional[str] = None

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_verified: bool = False

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    captcha_answer: Optional[int] = None
    captcha_id: Optional[str] = None
    recaptcha_token: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    recaptcha_token: Optional[str] = None

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # game, software, movie, tv_show, all
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CategoryCreate(BaseModel):
    name: str
    type: str = "all"

class Captcha(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    num1: int
    num2: int
    operator: str
    answer: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str

class ThemeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global_theme"
    mode: str = "dark"
    accent_color: str = "#00FF41"

class ThemeUpdate(BaseModel):
    mode: Optional[str] = None
    accent_color: Optional[str] = None

class SponsoredDownload(BaseModel):
    name: str
    download_link: str
    type: str
    description: Optional[str] = None

class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "site_settings"
    daily_submission_limit: int = 10
    top_downloads_enabled: bool = True
    top_downloads_count: int = 5
    sponsored_downloads: List[dict] = []

    # Google reCAPTCHA v2 settings (optional)
    recaptcha_site_key: Optional[str] = None
    recaptcha_secret_key: Optional[str] = None
    recaptcha_enable_submit: bool = False
    recaptcha_enable_auth: bool = False

    # Resend email settings (optional)
    resend_api_key: Optional[str] = None
    resend_sender_email: Optional[str] = None

    # Admin credentials stored in DB (set from Admin UI)
    admin_email: Optional[EmailStr] = None
    admin_password_hash: Optional[str] = None

class SiteSettingsUpdate(BaseModel):
    daily_submission_limit: Optional[int] = None
    top_downloads_enabled: Optional[bool] = None
    top_downloads_count: Optional[int] = None
    sponsored_downloads: Optional[List[dict]] = None

    # Google reCAPTCHA v2 settings
    recaptcha_site_key: Optional[str] = None
    recaptcha_secret_key: Optional[str] = None
    recaptcha_enable_submit: Optional[bool] = None
    recaptcha_enable_auth: Optional[bool] = None

    # Resend email settings
    resend_api_key: Optional[str] = None
    resend_sender_email: Optional[str] = None

    # Admin credentials
    admin_email: Optional[EmailStr] = None

def validate_http_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Site URL is required")
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Site URL must start with http:// or https://")
    return url


class RateLimitEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ip_address: str
    date: str
    count: int = 0

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

class AdminLogin(BaseModel):
    password: str

class AdminInitRequest(BaseModel):
    email: EmailStr
    password: str

class AdminChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AdminForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResendSettingsUpdate(BaseModel):
    resend_api_key: Optional[str] = None
    resend_sender_email: Optional[str] = None

class UserForgotPasswordRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

# ===== SETTINGS / EMAIL HELPERS =====

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def fetch_site_settings() -> dict:
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    if not settings:
        settings = SiteSettings().model_dump()
        await db.site_settings.insert_one(settings)
    return settings

async def send_email_via_resend(to_email: str, subject: str, html: str) -> bool:
    settings = await fetch_site_settings()
    api_key = settings.get("resend_api_key") or RESEND_API_KEY
    sender = settings.get("resend_sender_email") or SENDER_EMAIL

    if not api_key or not sender or not to_email:
        logger.info("Email not sent: missing Resend configuration or recipient")
        return False

    resend.api_key = api_key
    params = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# ===== HELPER FUNCTIONS =====

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def parse_file_size_to_bytes(size_str: str) -> Optional[int]:
    """Convert file size string to bytes for filtering"""
    if not size_str:
        return None
    size_str = size_str.upper().strip()
    try:
        if 'GB' in size_str:
            return int(float(size_str.replace('GB', '').strip()) * 1024 * 1024 * 1024)
        elif 'MB' in size_str:
            return int(float(size_str.replace('MB', '').strip()) * 1024 * 1024)
        elif 'KB' in size_str:
            return int(float(size_str.replace('KB', '').strip()) * 1024)
        elif 'B' in size_str:
            return int(float(size_str.replace('B', '').strip()))
        else:
            return int(float(size_str) * 1024 * 1024)  # Assume MB
    except (ValueError, TypeError):
        return None

async def send_submission_email(email: str, submission: dict):
    """Send confirmation email to submitter"""
    if not email:
        return

    if not FRONTEND_URL:
        logger.info("Email not sent: FRONTEND_URL is not configured")
        return
    
    submit_url = f"{FRONTEND_URL}/submit"
    html_content = f"""
    <html>
    <body style="font-family: 'Courier New', monospace; background-color: #0a0a0a; color: #00FF41; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 2px solid #00FF41; padding: 20px;">
            <h1 style="color: #00FF41; border-bottom: 1px solid #00FF41; padding-bottom: 10px;">
                DOWNLOAD ZONE - SUBMISSION RECEIVED
            </h1>
            <p>Your submission has been received and is pending admin approval.</p>
            
            <h2 style="color: #00FFFF;">SUBMISSION DETAILS:</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Name:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('name', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Type:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('type', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Category:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('category', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">File Size:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('file_size', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Date:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('submission_date', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Time:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">{submission.get('created_at', 'N/A')}</td>
                </tr>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="{submit_url}" style="display: inline-block; padding: 10px 20px; background-color: #00FF41; color: #000; text-decoration: none; font-weight: bold;">
                    SUBMIT ANOTHER FILE
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                This is an automated message from Download Zone.
            </p>
        </div>
    </body>
    </html>
    """
    
    ok = await send_email_via_resend(
        email,
        f"Download Zone - Submission Received: {submission.get('name', 'Unknown')}",
        html_content
    )
    if ok:
        logger.info(f"Email sent to {email}")
    else:
        logger.info(f"Email not sent to {email}")

# ===== CAPTCHA ROUTES =====

@api_router.get("/captcha")
async def generate_captcha():
    """Generate a simple math captcha"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operators = [('+', num1 + num2), ('-', abs(num1 - num2)), ('×', num1 * num2 if num1 < 10 and num2 < 10 else num1 + num2)]
    operator, answer = random.choice(operators)
    
    # Make subtraction always positive
    if operator == '-' and num1 < num2:
        num1, num2 = num2, num1
        answer = num1 - num2
    
    captcha_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc).isoformat()
    
    captcha = {
        "id": captcha_id,
        "num1": num1,
        "num2": num2,
        "operator": operator,
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at
    }
    
    await db.captchas.insert_one(captcha)
    
    return {
        "id": captcha_id,
        "question": f"What is {num1} {operator} {num2}?"
    }

# ===== RECAPTCHA HELPERS =====

async def verify_recaptcha(token: str, remote_ip: Optional[str], secret_key: str) -> bool:
    """Verify Google reCAPTCHA v2 token server-side"""
    if not token or not secret_key:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": secret_key, "response": token, "remoteip": remote_ip},
            )
        data = resp.json()
        return bool(data.get("success"))
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {str(e)}")
        return False

async def verify_captcha(captcha_id: str, answer: int) -> bool:
    """Verify captcha answer"""
    if not captcha_id or answer is None:
        return False
    
    captcha = await db.captchas.find_one({"id": captcha_id}, {"_id": 0})
    if not captcha:
        return False
    
    # Delete used captcha
    await db.captchas.delete_one({"id": captcha_id})
    
    return captcha.get("answer") == answer

# ===== USER AUTH ROUTES =====

@api_router.post("/auth/register")
async def register_user(user: UserRegister, request: Request):
    settings = await fetch_site_settings()

    # Verify captcha (math) OR reCAPTCHA depending on admin settings
    if settings.get("recaptcha_enable_auth"):
        if not settings.get("recaptcha_site_key") or not settings.get("recaptcha_secret_key"):
            raise HTTPException(status_code=400, detail="reCAPTCHA is enabled but not configured")

        ok = await verify_recaptcha(
            user.recaptcha_token,
            request.client.host if request.client else None,
            settings.get("recaptcha_secret_key", ""),
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")
    else:
        if not await verify_captcha(user.captcha_id, user.captcha_answer):
            raise HTTPException(status_code=400, detail="Invalid captcha")
    
    # Check if email exists
    existing = await db.users.find_one({"email": user.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_obj = User(
        email=user.email.lower(),
        password_hash=hash_password(user.password),
        is_verified=True  # Auto-verify for now
    )
    
    await db.users.insert_one(user_obj.model_dump())
    
    return {
        "success": True,
        "message": "Registration successful",
        "user_id": user_obj.id,
        "email": user_obj.email
    }

@api_router.post("/auth/login")
async def login_user(user: UserLogin, request: Request):
    settings = await fetch_site_settings()

    if settings.get("recaptcha_enable_auth"):
        if not settings.get("recaptcha_site_key") or not settings.get("recaptcha_secret_key"):
            raise HTTPException(status_code=400, detail="reCAPTCHA is enabled but not configured")

        ok = await verify_recaptcha(
            user.recaptcha_token,
            request.client.host if request.client else None,
            settings.get("recaptcha_secret_key", ""),
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

    # Find user
    db_user = await db.users.find_one({"email": user.email.lower()}, {"_id": 0})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check password
    if db_user.get("password_hash") != hash_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "success": True,
        "user_id": db_user.get("id"),
        "email": db_user.get("email")
    }

@api_router.get("/auth/user/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ===== CATEGORY ROUTES =====

@api_router.get("/categories")
async def get_categories(type_filter: Optional[str] = None):
    query = {}
    if type_filter and type_filter != "all":
        query["$or"] = [{"type": type_filter}, {"type": "all"}]
    
    categories = await db.categories.find(query, {"_id": 0}).to_list(100)
    return {"items": categories}

@api_router.post("/admin/categories")
async def create_category(category: CategoryCreate):
    # Check if exists
    existing = await db.categories.find_one({"name": category.name, "type": category.type}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    cat_obj = Category(name=category.name, type=category.type)
    await db.categories.insert_one(cat_obj.model_dump())
    return cat_obj.model_dump()

@api_router.delete("/admin/categories/{category_id}")
async def delete_category(category_id: str):
    result = await db.categories.delete_one({"id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True}

# ===== TAGS ROUTES =====

@api_router.get("/tags")
async def get_popular_tags(limit: int = Query(50, ge=1, le=100)):
    """Get popular tags from downloads"""
    pipeline = [
        {"$match": {"approved": True}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    tags = await db.downloads.aggregate(pipeline).to_list(limit)
    return {"items": [{"name": t["_id"], "count": t["count"]} for t in tags]}

# ===== DOWNLOADS ROUTES =====

@api_router.get("/")
async def root():
    return {"message": "Download Portal API"}

@api_router.get("/downloads", response_model=PaginatedDownloads)
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

# Top Downloads (includes sponsored)
@api_router.get("/downloads/top")
async def get_top_downloads():
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

# Submissions - Public (with or without registration)
@api_router.post("/submissions", response_model=Submission)
async def create_submission(submission: SubmissionCreate, request: Request):
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
    settings = await fetch_site_settings()
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
        file_size=submission.file_size,
        file_size_bytes=file_size_bytes,
        description=submission.description,
        category=submission.category,
        tags=submission.tags or [],
        site_name=submission.site_name,
        site_url=validate_http_url(submission.site_url),
        submitter_email=submission.submitter_email
    )
    doc = submission_obj.model_dump()
    await db.submissions.insert_one(doc)
    
    # Send confirmation email
    if submission.submitter_email:
        asyncio.create_task(send_submission_email(submission.submitter_email, doc))
    
    return submission_obj
    
# Admin init (set email + password the first time)
@api_router.post("/admin/init")
async def admin_init(payload: AdminInitRequest):
    settings = await fetch_site_settings()
    if settings.get("admin_password_hash"):
        raise HTTPException(status_code=400, detail="Admin is already initialized")

    settings["admin_email"] = payload.email.lower()
    settings["admin_password_hash"] = hash_password(payload.password)

    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)
    return {"success": True}

# Admin request password change (requires current password; sends magic link)
@api_router.post("/admin/password/change/request")
async def admin_request_password_change(payload: AdminChangePasswordRequest):
    settings = await fetch_site_settings()
    if not settings.get("admin_email"):

# Admin forgot password (send magic link)
@api_router.post("/admin/forgot-password")
async def admin_forgot_password(payload: AdminForgotPasswordRequest):
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

# Admin confirm password reset (forgot password)
@api_router.post("/admin/reset-password")
async def admin_reset_password(payload: PasswordResetConfirmRequest):
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
        "expires_at": expires_at
    })

    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL is not configured")

    link = f"{FRONTEND_URL}/admin/reset-password?token={token}"
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

# Admin confirm password change
@api_router.post("/admin/password/change/confirm")
async def admin_confirm_password_change(payload: PasswordResetConfirmRequest):
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

    # update admin password hash
    settings["admin_password_hash"] = req["new_password_hash"]
    await db.site_settings.update_one({"id": "site_settings"}, {"$set": settings}, upsert=True)

    await db.admin_password_resets.delete_one({"token": payload.token})
    return {"success": True}

# User forgot password (send magic link)
@api_router.post("/auth/forgot-password")
async def user_forgot_password(payload: UserForgotPasswordRequest):
    user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not user:
        # do not reveal existence
        return {"success": True}

    token = generate_token()
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=30)).isoformat()

    await db.user_password_resets.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": now.isoformat(),
        "expires_at": expires_at
    })

    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL is not configured")

    link = f"{FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Reset your password</h2>
      <p>Click the link below to reset your password. This link expires in 30 minutes.</p>
      <p><a href='{link}'>Reset password</a></p>
    </body></html>
    """

    await send_email_via_resend(payload.email.lower(), "Reset your password", html)
    return {"success": True}

# User confirm password reset
@api_router.post("/auth/reset-password")
async def user_reset_password(payload: PasswordResetConfirmRequest):
    req = await db.user_password_resets.find_one({"token": payload.token}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        exp = datetime.fromisoformat(req["expires_at"])
    except Exception:
        exp = datetime.now(timezone.utc)
    if exp < datetime.now(timezone.utc):
        await db.user_password_resets.delete_one({"token": payload.token})
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    await db.users.update_one(
        {"id": req["user_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password)}}
    )

    await db.user_password_resets.delete_one({"token": payload.token})
    return {"success": True}

# Check remaining submissions for today
@api_router.get("/submissions/remaining")
async def get_remaining_submissions(request: Request):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    settings = await fetch_site_settings()
    daily_limit = settings.get("daily_submission_limit", 10)
    
    client_ip = request.client.host if request.client else "anonymous"
    rate_entry = await db.rate_limits.find_one({"ip_address": client_ip, "date": today}, {"_id": 0})
    
    used = rate_entry.get("count", 0) if rate_entry else 0
    remaining = max(0, daily_limit - used)
    
    return {"daily_limit": daily_limit, "used": used, "remaining": remaining}

# Admin Login
@api_router.post("/admin/login")
async def admin_login(login: AdminLogin):
    settings = await fetch_site_settings()
    # Prefer DB-stored password hash; fallback to env for bootstrap
    if settings.get("admin_password_hash"):
        if hash_password(login.password) == settings.get("admin_password_hash"):
            return {"success": True, "message": "Access granted"}
    else:
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

# Public: expose only safe reCAPTCHA settings (site key + toggles)
@api_router.get("/recaptcha/settings")
async def get_recaptcha_settings_public():
    settings = await fetch_site_settings()
    return {
        "site_key": settings.get("recaptcha_site_key"),
        "enable_submit": bool(settings.get("recaptcha_enable_submit")),

# Resend settings update (Admin)
@api_router.put("/admin/resend")
async def update_resend_settings(update: ResendSettingsUpdate):
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

        "enable_auth": bool(settings.get("recaptcha_enable_auth")),
    }


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
async def get_site_settings_public():
    settings = await fetch_site_settings()

    # Never expose secret keys publicly
    settings = dict(settings)
    settings["recaptcha_secret_key"] = None
    settings["resend_api_key"] = None
    return settings

# Site Settings - Update (Admin)
@api_router.put("/admin/settings")
async def update_site_settings(update: SiteSettingsUpdate):
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
    
    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings},
        upsert=True
    )
    return settings

# Get statistics
@api_router.get("/stats")
async def get_stats():
    total = await db.downloads.count_documents({"approved": True})
    games = await db.downloads.count_documents({"approved": True, "type": "game"})
    software = await db.downloads.count_documents({"approved": True, "type": "software"})
    movies = await db.downloads.count_documents({"approved": True, "type": "movie"})
    tv_shows = await db.downloads.count_documents({"approved": True, "type": "tv_show"})
    
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

# Seed database with sample data (includes categories and tags)
@api_router.post("/admin/seed")
async def seed_database():
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
        date = base_date + __import__('datetime').timedelta(days=days_offset)
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
        date = base_date + __import__('datetime').timedelta(days=days_offset)
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
        date = base_date + __import__('datetime').timedelta(days=days_offset)
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
                date = base_date + __import__('datetime').timedelta(days=days_offset)
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
