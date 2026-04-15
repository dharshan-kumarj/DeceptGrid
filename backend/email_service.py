"""
email_service.py – Async SMTP OTP Email Delivery

Uses aiosmtplib for non-blocking SMTP with STARTTLS.
All SMTP credentials are read from environment variables (never hardcoded).

Usage:
    from email_service import send_otp_email
    await send_otp_email(
        to_address="sarah@gridco.local",
        otp_code="483921",
        session_id="<uuid>",
        target_meter="SM-REAL-051",
    )
"""

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SMTP configuration – sourced exclusively from environment
# ---------------------------------------------------------------------------
SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER: str = os.environ["SMTP_USER"]    # raises KeyError if missing → fail fast
SMTP_PASS: str = os.environ["SMTP_PASS"]
SMTP_FROM: str = os.environ.get("SMTP_FROM", SMTP_USER)


# ---------------------------------------------------------------------------
# Email builder
# ---------------------------------------------------------------------------

def _build_otp_email(
    to_address: str,
    otp_code: str,
    session_id: str,
    target_meter: str,
    from_address: str,
) -> MIMEMultipart:
    """
    Construct a multipart/alternative (text + HTML) OTP notification email.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[DeceptGrid] Your One-Time Access Code"
    msg["From"] = from_address
    msg["To"] = to_address

    plain_body = (
        f"DeceptGrid Security Alert\n"
        f"{'=' * 40}\n\n"
        f"An access request has been received for meter: {target_meter}\n\n"
        f"Your one-time code (valid for 5 minutes):\n\n"
        f"    {otp_code}\n\n"
        f"Session reference: {session_id}\n\n"
        f"If you did NOT initiate this request, do NOT enter this code and\n"
        f"contact the security team immediately.\n\n"
        f"This code will expire automatically and cannot be reused.\n"
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1a1a2e; background: #f4f4f8; padding: 20px;">
        <div style="max-width: 520px; margin: auto; background: #ffffff;
                    border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.12); overflow: hidden;">
          <div style="background: #0f3460; padding: 24px 32px;">
            <h2 style="color: #e94560; margin: 0; font-size: 20px; letter-spacing: 1px;">
              🔐 DeceptGrid Security
            </h2>
          </div>
          <div style="padding: 32px;">
            <p style="font-size: 15px; margin-top: 0;">
              An access request was received for meter
              <strong style="color: #0f3460;">{target_meter}</strong>.
            </p>
            <p style="font-size: 14px; color: #555;">Your one-time access code:</p>
            <div style="text-align: center; margin: 28px 0;">
              <span style="display: inline-block; font-size: 38px; font-weight: bold;
                           letter-spacing: 10px; color: #0f3460;
                           background: #eef2ff; padding: 16px 28px;
                           border-radius: 8px; border: 2px dashed #7b8cde;">
                {otp_code}
              </span>
            </div>
            <p style="font-size: 13px; color: #888; text-align: center;">
              ⏱ Expires in <strong>5 minutes</strong> &nbsp;|&nbsp; Single use only
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
            <p style="font-size: 12px; color: #aaa;">
              Session ID: <code>{session_id}</code><br>
              If you did not initiate this request, contact the security team immediately.
            </p>
          </div>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def send_otp_email(
    to_address: str,
    otp_code: str,
    session_id: str,
    target_meter: str,
) -> None:
    """
    Send the OTP email asynchronously.

    Raises:
        aiosmtplib.SMTPException – on any SMTP-level error (caller should
            log and return 500 rather than leaking the OTP or session_id).
        OSError – if the SMTP server is unreachable.
    """
    msg = _build_otp_email(
        to_address=to_address,
        otp_code=otp_code,
        session_id=session_id,
        target_meter=target_meter,
        from_address=SMTP_FROM,
    )

    logger.info(
        "Sending OTP email to=%r session=%s meter=%s",
        to_address,
        session_id,
        target_meter,
    )

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,   # STARTTLS upgrade on port 587
    )

    logger.info("OTP email delivered successfully to=%r", to_address)
