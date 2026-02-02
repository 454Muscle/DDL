"""Email service using Resend"""
import asyncio
import logging
import resend
from typing import List

from services.database import db, RESEND_API_KEY, SENDER_EMAIL, FRONTEND_URL
from models.schemas import SiteSettings

logger = logging.getLogger(__name__)


async def fetch_site_settings() -> dict:
    """Fetch site settings from database"""
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    if not settings:
        settings = SiteSettings().model_dump()
        await db.site_settings.insert_one(settings)
    return settings


async def send_email_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Send email using Resend API"""
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


async def send_bulk_submission_email(email: str, submissions: List[dict]):
    """Send confirmation email for bulk submissions"""
    if not email:
        return
    if not FRONTEND_URL:
        logger.info("Email not sent: FRONTEND_URL is not configured")
        return

    submit_url = f"{FRONTEND_URL}/submit"

    rows = ""
    for s in submissions[:50]:
        rows += f"""
        <tr>
            <td style=\"padding: 8px; border: 1px solid #333; color: #00FF41;\">{s.get('name','N/A')}</td>
            <td style=\"padding: 8px; border: 1px solid #333; color: #00FF41;\">{s.get('type','N/A')}</td>
            <td style=\"padding: 8px; border: 1px solid #333; color: #00FF41;\">{s.get('submission_date','N/A')}</td>
        </tr>
        """

    html = f"""
    <html>
    <body style=\"font-family: 'Courier New', monospace; background-color: #0a0a0a; color: #00FF41; padding: 20px;\">
        <div style=\"max-width: 600px; margin: 0 auto; border: 2px solid #00FF41; padding: 20px;\">
            <h1 style=\"color: #00FF41; border-bottom: 1px solid #00FF41; padding-bottom: 10px;\">DOWNLOAD ZONE - BATCH SUBMISSION RECEIVED</h1>
            <p>Your submissions have been received and are pending admin approval.</p>
            <h2 style=\"color: #00FFFF;\">SUBMISSIONS:</h2>
            <table style=\"width: 100%; border-collapse: collapse;\">
                <tr>
                    <td style=\"padding: 8px; border: 1px solid #333; color: #888;\">Name</td>
                    <td style=\"padding: 8px; border: 1px solid #333; color: #888;\">Type</td>
                    <td style=\"padding: 8px; border: 1px solid #333; color: #888;\">Date</td>
                </tr>
                {rows}
            </table>
            <p style=\"margin-top: 20px;\"><a href=\"{submit_url}\" style=\"display: inline-block; padding: 10px 20px; background-color: #00FF41; color: #000; text-decoration: none; font-weight: bold;\">SUBMIT MORE</a></p>
        </div>
    </body>
    </html>
    """

    await send_email_via_resend(email, f"Download Zone - Batch Submission Received ({len(submissions)})", html)


async def send_approval_email(email: str, submission: dict):
    """Send notification email to submitter when their submission is approved"""
    if not email:
        return
    
    if not FRONTEND_URL:
        logger.info("Approval email not sent: FRONTEND_URL is not configured")
        return
    
    home_url = FRONTEND_URL
    html_content = f"""
    <html>
    <body style="font-family: 'Courier New', monospace; background-color: #0a0a0a; color: #00FF41; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 2px solid #00FF41; padding: 20px;">
            <h1 style="color: #00FF41; border-bottom: 1px solid #00FF41; padding-bottom: 10px;">
                DOWNLOAD ZONE - SUBMISSION APPROVED
            </h1>
            <p style="color: #00FF41; font-size: 16px;">Great news! Your submission has been approved and is now live on Download Zone.</p>
            
            <h2 style="color: #00FFFF;">APPROVED CONTENT:</h2>
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
            </table>
            
            <p style="margin-top: 20px;">
                <a href="{home_url}" style="display: inline-block; padding: 10px 20px; background-color: #00FF41; color: #000; text-decoration: none; font-weight: bold;">
                    VIEW ON DOWNLOAD ZONE
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                Thank you for contributing to Download Zone!
            </p>
        </div>
    </body>
    </html>
    """
    
    ok = await send_email_via_resend(
        email,
        f"Download Zone - Submission Approved: {submission.get('name', 'Unknown')}",
        html_content
    )
    if ok:
        logger.info(f"Approval email sent to {email}")
    else:
        logger.info(f"Approval email not sent to {email}")


async def send_admin_submissions_summary(submissions: List[dict]):
    """Send summary of new submissions to admin"""
    settings = await fetch_site_settings()
    admin_email = settings.get("admin_email")
    if not admin_email:
        return

    items_html = "".join(
        f"<li><b>{s.get('name','N/A')}</b> ({s.get('type','N/A')})</li>" for s in submissions[:50]
    )
    html = f"""
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>New submissions received</h2>
      <p>Count: {len(submissions)}</p>
      <ul>{items_html}</ul>
    </body></html>
    """
    await send_email_via_resend(admin_email, f"New submissions received ({len(submissions)})", html)
