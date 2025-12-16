"""Report generator service orchestrating the full pipeline."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from src.models.config import AppConfig, ReportPeriod
from src.models.report_data import ReportData
from src.parsers.log_parser import extract_perf_reports, parse_log_lines
from src.parsers.metrics_aggregator import aggregate_metrics
from src.services.email_sender import EmailSender
from src.services.log_fetcher import LogFetcher
from src.services.pdf_generator import PdfGenerator


class ReportGenerator:
    """Orchestrates the full report generation and delivery pipeline."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the report generator.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._pdf_generator = PdfGenerator()
        self._email_sender = EmailSender(config)

    def generate_and_send(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        send_email: bool = True,
    ) -> Path:
        """Generate report and optionally send via email.

        Args:
            start_date: Report start date. Defaults based on period.
            end_date: Report end date. Defaults to yesterday.
            send_email: Whether to send the email.

        Returns:
            Path to the generated PDF file.
        """
        start_date, end_date = self.resolve_dates(start_date, end_date)
        log_content = self.fetch_logs(start_date, end_date)
        report_data = self.process_logs(log_content, start_date, end_date)
        pdf_path = self._generate_pdf(report_data, start_date, end_date)

        if send_email:
            self._send_email(report_data, pdf_path)

        return pdf_path

    def resolve_dates(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date, date]:
        """Resolve start and end dates based on configuration.

        Args:
            start_date: Optional explicit start date.
            end_date: Optional explicit end date.

        Returns:
            Tuple of (start_date, end_date).
        """
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)

        if end_date is None:
            end_date = yesterday

        if start_date is None:
            start_date = self._calculate_start_date(end_date)

        return start_date, end_date

    def _calculate_start_date(self, end_date: date) -> date:
        """Calculate start date based on report period.

        Args:
            end_date: The end date of the report.

        Returns:
            Calculated start date.
        """
        if self._config.report_period == ReportPeriod.DAILY:
            return end_date
        if self._config.report_period == ReportPeriod.WEEKLY:
            return end_date - timedelta(days=6)
        return end_date - timedelta(days=29)

    def fetch_logs(self, start_date: date, end_date: date) -> str:
        """Fetch logs from the API for the given date range.

        Args:
            start_date: Start date of the period.
            end_date: End date of the period.

        Returns:
            Concatenated log content.
        """
        with LogFetcher(self._config) as fetcher:
            return fetcher.fetch_logs_for_period(start_date, end_date)

    def process_logs(
        self,
        log_content: str,
        start_date: date,
        end_date: date,
    ) -> ReportData:
        """Process log content into aggregated report data.

        Args:
            log_content: Raw log content string.
            start_date: Report start date.
            end_date: Report end date.

        Returns:
            Aggregated ReportData.
        """
        log_entries = list(parse_log_lines(log_content))
        perf_reports = extract_perf_reports(iter(log_entries))
        return aggregate_metrics(perf_reports, log_entries, start_date, end_date)

    def _generate_pdf(
        self,
        report_data: ReportData,
        start_date: date,
        end_date: date,
    ) -> Path:
        """Generate PDF report.

        Args:
            report_data: Aggregated report data.
            start_date: Report start date.
            end_date: Report end date.

        Returns:
            Path to the generated PDF.
        """
        filename = f"bt-servant-report_{start_date}_{end_date}.pdf"
        output_path = self._config.report_output_dir / filename
        return self._pdf_generator.generate(report_data, output_path)

    def _send_email(self, report_data: ReportData, pdf_path: Path) -> None:
        """Send report via email.

        Args:
            report_data: Report data for email body.
            pdf_path: Path to PDF attachment.
        """
        html_body = self._pdf_generator.render_html_for_email(report_data)
        self._email_sender.send_report(report_data, html_body, pdf_path)
