# Email Providers & Configuration Guide

KnowledgeAI uses a decoupled, provider-agnostic architecture for email delivery, matching the pattern used for AI providers. You can switch between **Mailinator** (for instant zero-setup development/testing) and **SendGrid** (for production transactional delivery) simply by updating environment variables in `.env`.

---

## ⚙️ Environment Variables

Add the following to your `.env` file:

```env
# ==============================================================================
# Email Service Configuration (mailinator | sendgrid | smtp | console)
# ==============================================================================
EMAIL_PROVIDER=mailinator

# Mailinator Configuration (Free instant public testing)
MAILINATOR_API_KEY=
MAILINATOR_DOMAIN=mailinator.com

# SendGrid Configuration (Production delivery)
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# SMTP Configuration (Optional custom relay)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_TLS=true
EMAILS_FROM_EMAIL=noreply@knowledgeai.local

# Frontend Application URL (Used in activation emails)
FRONTEND_URL=http://localhost:5173
```

---

## 📬 Supported Providers

### 1. Mailinator (`EMAIL_PROVIDER=mailinator`) — Default
- **Use Case**: Local development, manual testing, and automated integration tests without external email setup.
- **How it works**:
  - Anyone can register with any `@mailinator.com` email address (e.g. `jane.doe@mailinator.com`).
  - The backend logs the activation link with full preview headers.
  - The API and UI generate direct links to the public inbox at:  
    `https://www.mailinator.com/v4/public/inboxes.jsp?to=jane.doe`
  - If `SMTP_HOST` is configured, it will also deliver the actual email message via SMTP.

### 2. SendGrid (`EMAIL_PROVIDER=sendgrid`)
- **Use Case**: Production transactional delivery.
- **How it works**:
  - Uses the official SendGrid Mail Send v3 REST API (`https://api.sendgrid.com/v3/mail/send`).
  - No extra heavy SDKs required; uses high-performance, asynchronous-capable `httpx`.
  - Dispatches multipart messages (plain text + branded HTML).
  - Handles HTTP 202 responses and provides structured logging on failures.

#### How to Switch to SendGrid:
1. Obtain an API key from [SendGrid](https://app.sendgrid.com/settings/api_keys) with Mail Send permissions.
2. In `.env`:
   ```env
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.xxx_your_actual_key_xxx
   SENDGRID_FROM_EMAIL=verified_sender@yourdomain.com
   ```
3. Restart the backend service. That's it!

### 3. Standard SMTP (`EMAIL_PROVIDER=smtp`)
- **Use Case**: Self-hosted mail servers (Postfix, Haraka, AWS SES SMTP, Mailgun SMTP, etc.).
- **How it works**:
  - Connects using standard `smtplib` with STARTTLS and optional authentication.

### 4. Console Logger (`EMAIL_PROVIDER=console`)
- **Use Case**: Offline environments, CI/CD runners, and headless unit tests.
- **How it works**:
  - Prints email metadata directly to application logs without sending network packets.

---

## 🏗️ Architecture & Extensibility

All email providers implement the `BaseEmailProvider` abstract class:

```python
class BaseEmailProvider(abc.ABC):
    @abc.abstractmethod
    def send(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        pass
```

The factory `get_email_provider()` instantiates the configured provider on demand, ensuring complete separation of concerns and zero tight coupling between routes, business logic, and third-party delivery APIs.

