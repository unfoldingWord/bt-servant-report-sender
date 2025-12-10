"""Email sender service for report delivery."""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.models.config import AppConfig
from src.models.report_data import ReportData


class EmailSender:
    """Sends email reports with HTML body and PDF attachment."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the email sender.

        Args:
            config: Application configuration with SMTP settings.
        """
        self._config = config

    def send_report(
        self,
        report_data: ReportData,
        html_body: str,
        pdf_path: Path,
        subject: str | None = None,
    ) -> None:
        """Send email with HTML body and PDF attachment.

        Args:
            report_data: Report data for subject generation.
            html_body: Rendered HTML content for email body.
            pdf_path: Path to PDF file to attach.
            subject: Optional custom subject line.
        """
        if subject is None:
            subject = self._generate_subject(report_data)

        message = self._create_message(subject, html_body, pdf_path)
        self._send_message(message)

    def _generate_subject(self, report_data: ReportData) -> str:
        """Generate email subject from report data.

        Args:
            report_data: Report data for date range.

        Returns:
            Email subject string.
        """
        start = report_data.executive_summary.date_range_start
        end = report_data.executive_summary.date_range_end
        return f"BT Servant Usage Report: {start} to {end}"

    def _create_message(
        self,
        subject: str,
        html_body: str,
        pdf_path: Path,
    ) -> MIMEMultipart:
        """Create MIME message with HTML body and PDF attachment.

        Args:
            subject: Email subject.
            html_body: HTML content for body.
            pdf_path: Path to PDF attachment.

        Returns:
            Constructed MIMEMultipart message.
        """
        message = MIMEMultipart("mixed")
        message["Subject"] = subject
        message["From"] = self._config.email_from
        message["To"] = ", ".join(self._config.email_to)

        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        with pdf_path.open("rb") as pdf_file:
            pdf_part = MIMEApplication(pdf_file.read(), _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition",
                "attachment",
                filename=pdf_path.name,
            )
            message.attach(pdf_part)

        return message

    def _send_message(self, message: MIMEMultipart) -> None:
        """Send email via SMTP.

        Args:
            message: Constructed email message.
        """
        with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as server:
            server.starttls()
            server.login(
                self._config.smtp_user,
                self._config.smtp_password.get_secret_value(),
            )
            server.send_message(message)
