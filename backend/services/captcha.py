"""Captcha service"""
import random
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from services.database import db
from services.email import fetch_site_settings
from models.schemas import Captcha

logger = logging.getLogger(__name__)


async def generate_captcha_challenge() -> dict:
    """Generate a simple math captcha"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operators = [('+', num1 + num2), ('-', abs(num1 - num2)), ('×', num1 * num2 if num1 < 10 and num2 < 10 else num1 + num2)]
    operator, answer = random.choice(operators)
    
    # Make subtraction always positive
    if operator == '-':
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2
    
    captcha = Captcha(
        num1=num1,
        num2=num2,
        operator=operator,
        answer=answer,
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    )
    
    await db.captchas.insert_one(captcha.model_dump())
    
    return {
        "id": captcha.id,
        "challenge": f"{num1} {operator} {num2} = ?",
        "expires_at": captcha.expires_at
    }


async def verify_recaptcha(token: str, remote_ip: Optional[str], secret_key: str) -> bool:
    """Verify Google reCAPTCHA v2 token"""
    if not secret_key:
        return False

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret_key, "response": token, "remoteip": remote_ip or ""}
        )
        data = resp.json()
        return data.get("success", False)


async def verify_captcha(captcha_id: str, answer: int) -> bool:
    """Verify math captcha answer"""
    captcha = await db.captchas.find_one({"id": captcha_id})
    if not captcha:
        return False
    
    # Check expiration
    expires_at = datetime.fromisoformat(captcha["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.captchas.delete_one({"id": captcha_id})
        return False
    
    # Verify answer
    if captcha["answer"] == answer:
        await db.captchas.delete_one({"id": captcha_id})
        return True
    
    return False


async def get_captcha_method():
    """Get current captcha method based on settings"""
    settings = await fetch_site_settings()
    if settings.get("recaptcha_enable_submit") and settings.get("recaptcha_site_key"):
        return "recaptcha"
    return "math"
