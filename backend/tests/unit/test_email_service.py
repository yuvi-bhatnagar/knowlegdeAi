import pytest
from unittest.mock import MagicMock, patch
from app.core.exceptions import ConfigurationException
from app.services.email_service import (
    ConsoleEmailProvider,
    EmailService,
    MailinatorEmailProvider,
    SMTPEmailProvider,
    SendGridEmailProvider,
    get_email_provider,
)


def test_mailinator_inbox_detection():
    # Test valid mailinator domain
    url = EmailService.get_mailinator_inbox_url("alpha.user@mailinator.com")
    assert url == "https://www.mailinator.com/v4/public/inboxes.jsp?to=alpha.user"

    # Test non-mailinator domain
    url_non = EmailService.get_mailinator_inbox_url("alpha.user@gmail.com")
    assert url_non is None


def test_mailinator_provider_dispatch():
    provider = MailinatorEmailProvider()
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.has_extn.return_value = True

        success = provider.send(
            to_email="test1@mailinator.com",
            subject="Test Activation",
            html_content="<p>Test</p>",
            text_content="Test",
        )
        assert success is True
        mock_smtp.assert_called_with("mail.mailinator.com", 587, timeout=10)


def test_sendgrid_missing_api_key():
    provider = SendGridEmailProvider()
    with patch("app.services.email_service.settings.SENDGRID_API_KEY", None):
        success = provider.send(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test",
        )
        assert success is False


def test_sendgrid_successful_dispatch():
    provider = SendGridEmailProvider()
    mock_response = MagicMock()
    mock_response.status_code = 202

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__enter__.return_value = mock_client_instance

    with patch("app.services.email_service.settings.SENDGRID_API_KEY", "SG.test-fake-key-12345"), \
         patch("httpx.Client", return_value=mock_client_instance):
        success = provider.send(
            to_email="recipient@example.com",
            subject="Welcome to KnowledgeAI",
            html_content="<p>Set password</p>",
            text_content="Set password",
        )
        assert success is True
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        assert kwargs["json"]["personalizations"][0]["to"][0]["email"] == "recipient@example.com"
        assert kwargs["headers"]["Authorization"] == "Bearer SG.test-fake-key-12345"


def test_smtp_missing_host():
    provider = SMTPEmailProvider()
    with patch("app.services.email_service.settings.SMTP_HOST", None):
        success = provider.send(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test",
        )
        assert success is False


def test_console_provider():
    provider = ConsoleEmailProvider()
    success = provider.send(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>",
        text_content="Test",
    )
    assert success is True


def test_email_provider_factory():
    assert isinstance(get_email_provider("mailinator"), MailinatorEmailProvider)
    assert isinstance(get_email_provider("sendgrid"), SendGridEmailProvider)
    assert isinstance(get_email_provider("smtp"), SMTPEmailProvider)
    assert isinstance(get_email_provider("console"), ConsoleEmailProvider)

    with pytest.raises(ConfigurationException):
        get_email_provider("invalid_provider")


def test_email_service_send_set_password_email():
    sent, link, mailinator_url = EmailService.send_set_password_email("user@mailinator.com", "fake-token-123")
    assert sent is True
    assert "token=fake-token-123" in link
    assert mailinator_url == "https://www.mailinator.com/v4/public/inboxes.jsp?to=user"

