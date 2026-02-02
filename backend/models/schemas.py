"""Pydantic models and schemas"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone


# ===== DOWNLOAD MODELS =====

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


class PaginatedDownloads(BaseModel):
    items: List[Download]
    total: int
    page: int
    pages: int


# ===== SUBMISSION MODELS =====

class Submission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    download_link: str
    type: str
    submission_date: str
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    seen_by_admin: bool = False
    file_size: Optional[str] = None
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
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


class BulkSubmissionCreate(BaseModel):
    items: List[SubmissionCreate]
    submitter_email: Optional[str] = None
    captcha_answer: Optional[int] = None
    captcha_id: Optional[str] = None
    recaptcha_token: Optional[str] = None


class PaginatedSubmissions(BaseModel):
    items: List[Submission]
    total: int
    page: int
    pages: int


# ===== USER MODELS =====

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


# ===== CATEGORY MODELS =====

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # game, software, movie, tv_show, all
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CategoryCreate(BaseModel):
    name: str
    type: str = "all"


# ===== CAPTCHA MODELS =====

class Captcha(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    num1: int
    num2: int
    operator: str
    answer: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str


# ===== THEME MODELS =====

class ThemeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global_theme"
    mode: str = "dark"
    accent_color: str = "#00FF41"


class ThemeUpdate(BaseModel):
    mode: Optional[str] = None
    accent_color: Optional[str] = None


# ===== SPONSORED MODELS =====

class SponsoredDownload(BaseModel):
    name: str
    download_link: str
    type: str
    description: Optional[str] = None


# ===== SITE SETTINGS MODELS =====

class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "site_settings"
    daily_submission_limit: int = 10
    top_downloads_enabled: bool = True
    top_downloads_count: int = 5
    sponsored_downloads: List[dict] = []

    # Trending downloads settings
    trending_downloads_enabled: bool = False
    trending_downloads_count: int = 5

    # Branding / typography
    site_name: Optional[str] = "DOWNLOAD ZONE"
    site_name_font_family: str = "JetBrains Mono"
    site_name_font_weight: str = "700"
    site_name_font_color: str = "#00FF41"
    body_font_family: str = "JetBrains Mono"
    body_font_weight: str = "400"

    # Footer
    footer_enabled: bool = True
    footer_line1_template: str = "For DMCA copyright complaints send an email to {admin_email}."
    footer_line2_template: str = "Copyright © {site_name} {year}. All rights reserved."

    # Submissions workflow
    auto_approve_submissions: bool = False

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

    # Trending downloads settings
    trending_downloads_enabled: Optional[bool] = None
    trending_downloads_count: Optional[int] = None

    # Branding / typography
    site_name: Optional[str] = None
    site_name_font_family: Optional[str] = None
    site_name_font_weight: Optional[str] = None
    site_name_font_color: Optional[str] = None
    body_font_family: Optional[str] = None
    body_font_weight: Optional[str] = None

    # Footer
    footer_enabled: Optional[bool] = None
    footer_line1_template: Optional[str] = None
    footer_line2_template: Optional[str] = None

    # Submissions workflow
    auto_approve_submissions: Optional[bool] = None

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


# ===== RATE LIMIT MODELS =====

class RateLimitEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ip_address: str
    date: str
    count: int = 0


# ===== ADMIN MODELS =====

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


class AdminUpdateEmailRequest(BaseModel):
    current_password: str
    new_email: EmailStr


class ResendSettingsUpdate(BaseModel):
    resend_api_key: Optional[str] = None
    resend_sender_email: Optional[str] = None


# ===== PASSWORD RESET MODELS =====

class UserForgotPasswordRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class TokenOnlyRequest(BaseModel):
    token: str
