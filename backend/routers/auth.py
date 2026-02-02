"""Authentication router - user auth endpoints"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta

from services.database import db, FRONTEND_URL
from services.email import fetch_site_settings, send_email_via_resend
from services.captcha import verify_recaptcha, verify_captcha, generate_captcha_challenge
from services.utils import hash_password, generate_token
from models.schemas import (
    UserRegister, UserLogin, User,
    UserForgotPasswordRequest, PasswordResetConfirmRequest
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(user: UserRegister, request: Request):
    """Register a new user"""
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


@router.post("/login")
async def login_user(user: UserLogin, request: Request):
    """Login user"""
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


@router.get("/user/{user_id}")
async def get_user(user_id: str):
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/forgot-password")
async def user_forgot_password(payload: UserForgotPasswordRequest):
    """Request password reset for user"""
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


@router.post("/reset-password")
async def user_reset_password(payload: PasswordResetConfirmRequest):
    """Confirm password reset for user"""
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
