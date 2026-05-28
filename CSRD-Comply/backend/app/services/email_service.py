"""
CSRD Comply — Email Service for Transactional Emails.

Handles:
- Registration confirmation
- Password reset
- Subscription notifications
- Deadline reminders
- Report status updates

Uses SMTP (sendmail) for self-hosted or SendGrid/Mailgun/SES integration.
"""
import logging
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data."""
    to: List[str]
    subject: str
    html_body: str
    text_body: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class EmailServiceError(Exception):
    """Email service error."""
    pass


class EmailService:
    """
    Transactional email service for CSRD Comply.

    Supports multiple providers:
    1. SMTP (default, self-hosted)
    2. SendGrid (if SENDGRID_API_KEY set)
    3. Mailgun (if MAILGUN_API_KEY set)
    4. Console (development mode — prints to logs)
    """

    def __init__(self):
        self._from_email = getattr(settings, "EMAIL_FROM", "noreply@csrdcomply.io")
        self._from_name = getattr(settings, "EMAIL_FROM_NAME", "CSRD Comply")
        self._smtp_host = getattr(settings, "SMTP_HOST", "localhost")
        self._smtp_port = getattr(settings, "SMTP_PORT", 587)
        self._smtp_user = getattr(settings, "SMTP_USER", "")
        self._smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        self._sendgrid_key = getattr(settings, "SENDGRID_API_KEY", "")
        self._mailgun_key = getattr(settings, "MAILGUN_API_KEY", "")
        self._mailgun_domain = getattr(settings, "MAILGUN_DOMAIN", "")
        self._environment = settings.ENVIRONMENT

    def send(self, message: EmailMessage) -> bool:
        """
        Send an email. In development mode, logs instead of sending.

        Args:
            message: EmailMessage to send

        Returns:
            True if sent successfully
        """
        if self._environment == "development":
            return self._send_console(message)

        if self._sendgrid_key:
            return self._send_sendgrid(message)
        elif self._mailgun_key:
            return self._send_mailgun(message)
        else:
            return self._send_smtp(message)

    def send_async(self, message: EmailMessage) -> None:
        """Send email asynchronously in a background thread."""
        thread = threading.Thread(target=self.send, args=(message,))
        thread.daemon = True
        thread.start()

    def _send_console(self, message: EmailMessage) -> bool:
        """Log email to console (development mode)."""
        logger.info(
            f"[EMAIL] To: {', '.join(message.to)} | "
            f"Subject: {message.subject} | "
            f"Body: {message.html_body[:200]}..."
        )
        return True

    def _send_smtp(self, message: EmailMessage) -> bool:
        """Send via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self._from_name} <{self._from_email}>"
            msg["To"] = ", ".join(message.to)
            msg["Subject"] = message.subject
            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Plain text fallback
            text_part = MIMEText(
                message.text_body or self._html_to_text(message.html_body),
                "plain", "utf-8"
            )
            msg.attach(text_part)

            # HTML body
            html_part = MIMEText(message.html_body, "html", "utf-8")
            msg.attach(html_part)

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                if self._smtp_user and self._smtp_password:
                    server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._from_email, message.to, msg.as_string())

            logger.info(f"Email sent via SMTP to {', '.join(message.to)}: {message.subject}")
            return True

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False

    def _send_sendgrid(self, message: EmailMessage) -> bool:
        """Send via SendGrid API."""
        try:
            import requests
            payload = {
                "personalizations": [{"to": [{"email": e} for e in message.to]}],
                "from": {"email": self._from_email, "name": self._from_name},
                "subject": message.subject,
                "content": [
                    {"type": "text/plain", "value": message.text_body or self._html_to_text(message.html_body)},
                    {"type": "text/html", "value": message.html_body},
                ],
            }
            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._sendgrid_key}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if resp.status_code in (200, 201, 202):
                logger.info(f"Email sent via SendGrid to {', '.join(message.to)}")
                return True
            else:
                logger.error(f"SendGrid error {resp.status_code}: {resp.text[:200]}")
                return False

        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False

    def _send_mailgun(self, message: EmailMessage) -> bool:
        """Send via Mailgun API."""
        try:
            import requests
            resp = requests.post(
                f"https://api.mailgun.net/v3/{self._mailgun_domain}/messages",
                auth=("api", self._mailgun_key),
                data={
                    "from": f"{self._from_name} <{self._from_email}>",
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.text_body or self._html_to_text(message.html_body),
                    "html": message.html_body,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                logger.info(f"Email sent via Mailgun to {', '.join(message.to)}")
                return True
            else:
                logger.error(f"Mailgun error {resp.status_code}: {resp.text[:200]}")
                return False

        except Exception as e:
            logger.error(f"Mailgun send failed: {e}")
            return False

    def _html_to_text(self, html: str) -> str:
        """Convert basic HTML to plain text."""
        import re
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    # ── Template Builders ──────────────────────────────────────

    def _build_base_html(self, title: str, body_html: str) -> str:
        """Build base HTML email template with CSRD Comply branding."""
        return f"""<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f4f7fb; color: #333; }}
.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
.header {{ background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
.header h1 {{ margin: 0; font-size: 22px; font-weight: 600; }}
.body {{ background: white; padding: 30px 20px; }}
.footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
.btn {{ display: inline-block; background: #2b6cb0; color: white !important; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 600; margin: 10px 0; }}
.btn:hover {{ background: #1a365d; }}
</style></head>
<body>
<div class="container">
<div class="header"><h1>{title}</h1></div>
<div class="body">{body_html}</div>
<div class="footer">
<p><strong>CSRD Comply</strong> — SaaS di conformità CSRD/ESG per PMI Europee</p>
<p>© {datetime.now().year} CSRD Comply. Tutti i diritti riservati.</p>
<p style="font-size:11px;color:#999;">
<a href="{{UNSUBSCRIBE_URL}}" style="color:#999;">Disiscriviti</a> |
<a href="mailto:support@csrdcomply.io" style="color:#999;">Contattaci</a>
</p>
</div>
</div>
</body>
</html>"""

    def build_welcome_email(self, name: str, company_name: str, login_url: str) -> EmailMessage:
        """Build registration welcome email."""
        html = self._build_base_html(
            "Benvenuto in CSRD Comply! 🚀",
            f"""
            <p>Ciao <strong>{name}</strong>,</p>
            <p>Grazie per esserti registrato a <strong>CSRD Comply</strong>! La tua azienda <strong>{company_name}</strong> è ora pronta per iniziare il percorso di conformità CSRD.</p>
            <div style="background:#f0f7ff;padding:20px;border-radius:8px;margin:20px 0;">
                <h3 style="margin-top:0;color:#2b6cb0;">Prossimi passi:</h3>
                <ol style="margin-bottom:0;">
                    <li>Completa il <strong>questionario di contesto</strong> aziendale</li>
                    <li>Avvia la <strong>valutazione di doppia materialità</strong></li>
                    <li>Calcola le <strong>emissioni GHG</strong> della tua azienda</li>
                    <li>Genera il <strong>report CSRD</strong> completo</li>
                </ol>
            </div>
            <p style="text-align:center;"><a href="{login_url}" class="btn">Accedi alla Piattaforma</a></p>
            <p style="font-size:13px;color:#666;">Se non hai creato tu questo account, ignora questa email.</p>
            """
        )
        return EmailMessage(
            to=[],  # Set externally
            subject=f"Benvenuto in CSRD Comply, {name}!",
            html_body=html,
            text_body=f"Benvenuto in CSRD Comply! Accedi qui: {login_url}",
        )

    def build_password_reset_email(self, name: str, reset_url: str) -> EmailMessage:
        """Build password reset email."""
        html = self._build_base_html(
            "Reset della Password",
            f"""
            <p>Ciao <strong>{name}</strong>,</p>
            <p>Hai richiesto il reset della password per il tuo account CSRD Comply.</p>
            <p style="text-align:center;"><a href="{reset_url}" class="btn">Resetta la Password</a></p>
            <p>Questo link è valido per <strong>1 ora</strong>.</p>
            <p style="font-size:13px;color:#666;">Se non hai richiesto il reset, ignora questa email. La tua password è al sicuro.</p>
            """
        )
        return EmailMessage(
            to=[],
            subject="Reset della Password — CSRD Comply",
            html_body=html,
            text_body=f"Resetta la password qui: {reset_url}",
        )

    def build_report_ready_email(self, name: str, report_title: str, report_url: str) -> EmailMessage:
        """Build report ready notification."""
        html = self._build_base_html(
            "Report CSRD Pronto! 📄",
            f"""
            <p>Ciao <strong>{name}</strong>,</p>
            <p>Il tuo report <strong>{report_title}</strong> è pronto per la revisione.</p>
            <div style="background:#f0fff4;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #38a169;">
                <p style="margin:0;"><strong>✅ Report generato con successo</strong></p>
                <p style="margin:5px 0 0;font-size:13px;color:#666;">Controlla la validazione iXBRL prima del filing.</p>
            </div>
            <p style="text-align:center;"><a href="{report_url}" class="btn">Visualizza Report</a></p>
            """
        )
        return EmailMessage(
            to=[],
            subject=f"Report Pronto: {report_title}",
            html_body=html,
            text_body=f"Il report {report_title} è pronto: {report_url}",
        )

    def build_deadline_reminder_email(self, name: str, days_left: int, task: str) -> EmailMessage:
        """Build deadline reminder."""
        urgency_color = "#e53e3e" if days_left <= 7 else "#dd6b20" if days_left <= 14 else "#3182ce"
        html = self._build_base_html(
            "Promemoria Scadenza ⏰",
            f"""
            <p>Ciao <strong>{name}</strong>,</p>
            <div style="background:#fff5f5;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid {urgency_color};">
                <h3 style="margin-top:0;color:{urgency_color};">Scadenza imminente</h3>
                <p style="font-size:16px;"><strong>{task}</strong></p>
                <p style="font-size:14px;color:{urgency_color};font-weight:600;">Mancano {days_left} giorno{"i" if days_left != 1 else ""}</p>
            </div>
            <p style="text-align:center;"><a href="{settings.DEPLOYMENT_DOMAIN}/dashboard" class="btn">Vai alla Dashboard</a></p>
            """
        )
        return EmailMessage(
            to=[],
            subject=f"⏰ Scadenza tra {days_left} giorni: {task}",
            html_body=html,
            text_body=f"Promemoria: {task} scade tra {days_left} giorni.",
        )


# ── Singleton ────────────────────────────────────────────

_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_welcome_email(to_email: str, name: str, company_name: str, login_url: str) -> bool:
    """Helper: send welcome email."""
    service = get_email_service()
    msg = service.build_welcome_email(name, company_name, login_url)
    msg.to = [to_email]
    return service.send(msg)


def send_password_reset_email(to_email: str, name: str, reset_url: str) -> bool:
    """Helper: send password reset email."""
    service = get_email_service()
    msg = service.build_password_reset_email(name, reset_url)
    msg.to = [to_email]
    return service.send(msg)


def send_report_ready_email(to_email: str, name: str, report_title: str, report_url: str) -> bool:
    """Helper: send report ready notification."""
    service = get_email_service()
    msg = service.build_report_ready_email(name, report_title, report_url)
    msg.to = [to_email]
    return service.send(msg)


def send_deadline_reminder(to_email: str, name: str, days_left: int, task: str) -> bool:
    """Helper: send deadline reminder."""
    service = get_email_service()
    msg = service.build_deadline_reminder_email(name, days_left, task)
    msg.to = [to_email]
    return service.send(msg)
