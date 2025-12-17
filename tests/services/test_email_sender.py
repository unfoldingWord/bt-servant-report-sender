"""Tests for email sender service."""

# pylint: disable=protected-access

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.config import AppConfig
from src.models.report_data import (
    CostBreakdown,
    ExecutiveSummary,
    PerformanceMetrics,
    ReportData,
    SystemHealth,
    UsageAnalytics,
)
from src.services.email_sender import EmailSender


@pytest.fixture
def mock_config() -> AppConfig:
    """Create mock configuration."""
    return AppConfig(
        bt_servant_api_url="https://api.example.com",
        bt_servant_api_token="test-token",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="smtp-password",
        email_from="reports@example.com",
        email_to=["recipient1@example.com", "recipient2@example.com"],
    )


@pytest.fixture
def sample_report_data() -> ReportData:
    """Create sample report data."""
    return ReportData(
        generated_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
        executive_summary=ExecutiveSummary(
            date_range_start=date(2024, 1, 15),
            date_range_end=date(2024, 1, 15),
            total_interactions=100,
            total_cost_usd=Decimal("1.50"),
            avg_response_time_ms=Decimal("2500"),
            unique_users=10,
        ),
        cost_breakdown=CostBreakdown(
            total_cost_usd=Decimal("1.50"),
            total_input_cost_usd=Decimal("0.80"),
            total_output_cost_usd=Decimal("0.60"),
            total_cached_cost_usd=Decimal("0.05"),
            total_audio_cost_usd=Decimal("0.05"),
        ),
        cost_by_intent=[],
        performance=PerformanceMetrics(
            avg_response_time_ms=Decimal("2500"),
            p50_response_time_ms=Decimal("2000"),
            p95_response_time_ms=Decimal("4500"),
            p99_response_time_ms=Decimal("6000"),
            slowest_spans=[],
        ),
        usage=UsageAnalytics(
            unique_users=10,
            top_intents=[],
            language_distribution={},
        ),
        system_health=SystemHealth(
            total_requests=100,
            success_rate_percent=Decimal("99.0"),
            warning_count=5,
            error_count=1,
            warning_messages=[],
            error_messages=[],
        ),
    )


@pytest.fixture
def temp_pdf_file(tmp_path: Path) -> Path:
    """Create a temporary PDF file."""
    pdf_path = tmp_path / "test_report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    return pdf_path


class TestEmailSenderSubjectGeneration:
    """Tests for subject line generation."""

    def test_generates_subject_from_report_data(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
    ) -> None:
        """Test subject generation includes date range."""
        sender = EmailSender(mock_config)
        subject = sender._generate_subject(sample_report_data)

        assert "BT Servant Usage Report" in subject
        assert "2024-01-15" in subject

    def test_subject_format_for_date_range(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
    ) -> None:
        """Test subject format for multi-day range."""
        sample_report_data.executive_summary.date_range_end = date(2024, 1, 21)
        sender = EmailSender(mock_config)
        subject = sender._generate_subject(sample_report_data)

        assert "2024-01-15 to 2024-01-21" in subject


class TestEmailSenderMessageCreation:
    """Tests for MIME message creation."""

    def test_creates_multipart_message(
        self,
        mock_config: AppConfig,
        temp_pdf_file: Path,
    ) -> None:
        """Test message is multipart/mixed."""
        sender = EmailSender(mock_config)
        message = sender._create_message(
            subject="Test Subject",
            html_body="<html><body>Test</body></html>",
            pdf_path=temp_pdf_file,
        )

        assert message["Subject"] == "Test Subject"
        assert message["From"] == "reports@example.com"
        assert message["To"] == "recipient1@example.com, recipient2@example.com"

    def test_includes_html_body(
        self,
        mock_config: AppConfig,
        temp_pdf_file: Path,
    ) -> None:
        """Test message includes HTML body."""
        sender = EmailSender(mock_config)
        html_content = "<html><body><h1>Report</h1></body></html>"
        message = sender._create_message(
            subject="Test",
            html_body=html_content,
            pdf_path=temp_pdf_file,
        )

        # Check that HTML part is present
        payloads = message.get_payload()
        html_parts = [p for p in payloads if p.get_content_type() == "text/html"]
        assert len(html_parts) == 1

    def test_includes_pdf_attachment(
        self,
        mock_config: AppConfig,
        temp_pdf_file: Path,
    ) -> None:
        """Test message includes PDF attachment."""
        sender = EmailSender(mock_config)
        message = sender._create_message(
            subject="Test",
            html_body="<html></html>",
            pdf_path=temp_pdf_file,
        )

        payloads = message.get_payload()
        pdf_parts = [p for p in payloads if p.get_content_type() == "application/pdf"]
        assert len(pdf_parts) == 1

        # Check filename header
        disposition = pdf_parts[0]["Content-Disposition"]
        assert "test_report.pdf" in disposition


class TestEmailSenderSmtp:
    """Tests for SMTP sending."""

    def test_sends_via_smtp_with_tls(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
        temp_pdf_file: Path,
    ) -> None:
        """Test SMTP connection uses TLS."""
        with patch("src.services.email_sender.smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

            sender = EmailSender(mock_config)
            sender.send_report(
                report_data=sample_report_data,
                html_body="<html></html>",
                pdf_path=temp_pdf_file,
            )

            mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("user@example.com", "smtp-password")
            mock_smtp.send_message.assert_called_once()

    def test_uses_custom_subject_when_provided(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
        temp_pdf_file: Path,
    ) -> None:
        """Test custom subject overrides generated subject."""
        with patch("src.services.email_sender.smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

            sender = EmailSender(mock_config)
            sender.send_report(
                report_data=sample_report_data,
                html_body="<html></html>",
                pdf_path=temp_pdf_file,
                subject="Custom Subject Line",
            )

            # Get the message that was sent
            call_args = mock_smtp.send_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["Subject"] == "Custom Subject Line"
