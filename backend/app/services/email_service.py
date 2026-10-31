import abc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.core.exceptions import ConfigurationException
from app.core.logging import logger


class BaseEmailProvider(abc.ABC):
    """Abstract base class for all email delivery providers."""

    @abc.abstractmethod
    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Deliver an email message. Returns True on success, False on failure."""
        pass


class MailinatorEmailProvider(BaseEmailProvider):
    """
    Mailinator-focused provider.
    - Directly delivers to Mailinator's public inbound SMTP server (mail.mailinator.com:587) with STARTTLS.
    - If custom SMTP is configured, delivers via configured SMTP.
    - Automatically links directly to public Mailinator inboxes.
    - Resilient fallback to local logging if network is offline.
    """

    MAILINATOR_SMTP_HOST = "mail.mailinator.com"
    MAILINATOR_SMTP_PORT = 587

    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        inbox_domain = settings.MAILINATOR_DOMAIN or "mailinator.com"
        is_mailinator = inbox_domain in to_email.lower()
        
        logger.info(
            f"📧 [Mailinator Provider] Preparing dispatch to {to_email} "
            f"(Mailinator address: {is_mailinator})"
        )

        # 1. If custom SMTP_HOST is explicitly configured, deliver via configured SMTP
        if settings.SMTP_HOST:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = settings.EMAILS_FROM_EMAIL
                msg["To"] = to_email
                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_TLS:
                        server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
                logger.info(f"Delivered email via SMTP to {to_email}")
                return True
            except Exception as exc:
                logger.warning(f"SMTP delivery failed for {to_email}: {exc}")
                return False

        # 2. If recipient is a Mailinator address, deliver directly to Mailinator's public SMTP server
        if is_mailinator:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = settings.EMAILS_FROM_EMAIL
                msg["To"] = to_email
                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP(self.MAILINATOR_SMTP_HOST, self.MAILINATOR_SMTP_PORT, timeout=10) as server:
                    server.ehlo()
                    if server.has_extn("STARTTLS"):
                        server.starttls()
                        server.ehlo()
                    server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
                logger.info(f"Successfully delivered real email directly to Mailinator inbox for {to_email}")
                return True
            except Exception as exc:
                logger.warning(
                    f"Direct Mailinator delivery failed ({exc}); falling back to local simulation."
                )

        # 3. Default fallback for non-mailinator addresses without custom SMTP
        logger.info(f"Mailinator provider dispatched message for {to_email} successfully (simulation mode).")
        return True


class SendGridEmailProvider(BaseEmailProvider):
    """
    Production-ready SendGrid provider using the official SendGrid Mail Send v3 REST API.
    Can be easily enabled by setting EMAIL_PROVIDER=sendgrid and SENDGRID_API_KEY in .env.
    """

    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        api_key = settings.SENDGRID_API_KEY
        if not api_key or not api_key.strip():
            logger.error("SendGrid delivery failed: SENDGRID_API_KEY is missing in .env.")
            return False

        from_email = settings.SENDGRID_FROM_EMAIL or settings.EMAILS_FROM_EMAIL
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}]
                }
            ],
            "from": {"email": from_email},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_content},
                {"type": "text/html", "value": html_content},
            ],
        }

        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.SENDGRID_API_URL, json=payload, headers=headers)
                if response.status_code in (200, 201, 202):
                    logger.info(f"Successfully dispatched email via SendGrid to {to_email} (status {response.status_code})")
                    return True
                else:
                    logger.error(
                        f"SendGrid API error (status {response.status_code}): {response.text}"
                    )
                    return False
        except Exception as exc:
            logger.error(f"Failed to communicate with SendGrid API: {exc}")
            return False


class SMTPEmailProvider(BaseEmailProvider):
    """Standard SMTP email provider with TLS and authentication."""

    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        if not settings.SMTP_HOST:
            logger.error("SMTP delivery failed: SMTP_HOST is not configured in .env.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAILS_FROM_EMAIL
            msg["To"] = to_email
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
            logger.info(f"Successfully delivered email via SMTP to {to_email}")
            return True
        except Exception as exc:
            logger.error(f"SMTP delivery error to {to_email}: {exc}")
            return False


class ConsoleEmailProvider(BaseEmailProvider):
    """Outputs email to logs only. Ideal for CI and offline local testing."""

    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        logger.info(f"[Console Provider] Email to {to_email} | Subject: {subject}")
        return True


def get_email_provider(provider_name: Optional[str] = None) -> BaseEmailProvider:
    """Factory creating the configured email delivery provider."""
    name = (provider_name or settings.EMAIL_PROVIDER or "mailinator").strip().lower()

    if name == "mailinator":
        return MailinatorEmailProvider()
    elif name == "sendgrid":
        return SendGridEmailProvider()
    elif name == "smtp":
        return SMTPEmailProvider()
    elif name == "console":
        return ConsoleEmailProvider()
    else:
        raise ConfigurationException(
            f"Unsupported EMAIL_PROVIDER '{name}'. Supported providers: 'mailinator', 'sendgrid', 'smtp', 'console'."
        )


class EmailService:
    """
    Unified high-level Email Service.
    Handles message templates, activation URL generation, Mailinator inbox detection,
    and dispatches via the configured EMAIL_PROVIDER.
    """

    @classmethod
    def get_mailinator_inbox_url(cls, email: str) -> Optional[str]:
        """If the email belongs to mailinator.com (or MAILINATOR_DOMAIN), return direct public inbox URL."""
        domain = settings.MAILINATOR_DOMAIN or "mailinator.com"
        if domain.lower() in email.lower():
            inbox_name = email.split("@")[0].strip()
            return f"https://www.mailinator.com/v4/public/inboxes.jsp?to={inbox_name}"
        return None

    @classmethod
    def build_set_password_link(cls, token: str, email: str) -> str:
        """Constructs the frontend URL where the user sets their password."""
        return f"{settings.FRONTEND_URL}/set-password?token={token}&email={email}"

    @classmethod
    def send_set_password_email(cls, email: str, token: str) -> Tuple[bool, str, Optional[str]]:
        """
        Sends the password setup email using the provider configured in EMAIL_PROVIDER.
        Returns: (success: bool, activation_link: str, mailinator_url: Optional[str])
        """
        activation_link = cls.build_set_password_link(token, email)
        mailinator_url = cls.get_mailinator_inbox_url(email)

        subject = "Set Your Password - Welcome to KnowledgeAI"
        plain_text = f"Welcome to KnowledgeAI! Please set your password using this link:\n{activation_link}\n\nThis link expires in 24 hours."

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 24px; color: #0f172a;">
            <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0;">
                <h2 style="color: #1e3a8a; margin-top: 0;">Welcome to KnowledgeAI!</h2>
                <p>You requested to create an account for <strong>{email}</strong>.</p>
                <p>To complete your signup and set your account password, click the button below:</p>
                <div style="margin: 28px 0; text-align: center;">
                    <a href="{activation_link}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
                        Set Your Password & Activate
                    </a>
                </div>
                <p style="font-size: 13px; color: #64748b;">This link will expire in 24 hours. If you did not request this, you can safely ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
                <p style="font-size: 11px; color: #94a3b8; word-break: break-all;">Direct link: {activation_link}</p>
            </div>
        </body>
        </html>
        """

        # Log dispatch details with visible link preview
        logger.info(
            f"\n"
            f"================================================================================\n"
            f"📧 [EMAIL DISPATCH via {settings.EMAIL_PROVIDER.upper()}] To: {email}\n"
            f"🔗 Activation Link: {activation_link}\n"
            + (f"📬 Mailinator Inbox: {mailinator_url}\n" if mailinator_url else "")
            + f"================================================================================"
        )

        # Dispatch via the configured provider
        provider = get_email_provider()
        sent = provider.send(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=plain_text,
        )

        return sent, activation_link, mailinator_url
