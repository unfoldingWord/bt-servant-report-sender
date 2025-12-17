"""Tests for report generator orchestration service."""

# pylint: disable=protected-access

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.config import AppConfig, ReportPeriod
from src.models.report_data import (
    CostBreakdown,
    ExecutiveSummary,
    PerformanceMetrics,
    ReportData,
    SystemHealth,
    UsageAnalytics,
)
from src.services.report_generator import ReportGenerator


@pytest.fixture
def mock_config() -> AppConfig:
    """Create mock configuration."""
    return AppConfig(
        bt_servant_api_url="https://api.example.com",
        bt_servant_api_token="test-token",
        smtp_user="user@example.com",
        smtp_password="smtp-password",
        email_from="reports@example.com",
        email_to=["recipient@example.com"],
        report_period=ReportPeriod.DAILY,
        report_output_dir=Path("/tmp/reports"),
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
        ),
    )


class TestReportGeneratorDateResolution:
    """Tests for date resolution logic."""

    def test_daily_period_uses_single_day(self, mock_config: AppConfig) -> None:
        """Test daily period resolves to single day."""
        mock_config.report_period = ReportPeriod.DAILY
        generator = ReportGenerator(mock_config)

        end_date = date(2024, 1, 15)
        start_date = generator._calculate_start_date(end_date)

        assert start_date == end_date

    def test_weekly_period_uses_seven_days(self, mock_config: AppConfig) -> None:
        """Test weekly period resolves to 7 days."""
        mock_config.report_period = ReportPeriod.WEEKLY
        generator = ReportGenerator(mock_config)

        end_date = date(2024, 1, 15)
        start_date = generator._calculate_start_date(end_date)

        assert start_date == date(2024, 1, 9)
        assert (end_date - start_date).days == 6

    def test_monthly_period_uses_thirty_days(self, mock_config: AppConfig) -> None:
        """Test monthly period resolves to 30 days."""
        mock_config.report_period = ReportPeriod.MONTHLY
        generator = ReportGenerator(mock_config)

        end_date = date(2024, 1, 30)
        start_date = generator._calculate_start_date(end_date)

        assert start_date == date(2024, 1, 1)
        assert (end_date - start_date).days == 29

    def test_explicit_dates_override_period(self, mock_config: AppConfig) -> None:
        """Test explicit dates override configured period."""
        generator = ReportGenerator(mock_config)

        start, end = generator._resolve_dates(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_default_end_date_is_yesterday(self, mock_config: AppConfig) -> None:
        """Test default end date is yesterday."""
        generator = ReportGenerator(mock_config)

        with patch("src.services.report_generator.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 16, 12, 0, tzinfo=UTC)
            mock_datetime.side_effect = datetime

            _, end = generator._resolve_dates(None, None)

            assert end == date(2024, 1, 15)


class TestReportGeneratorPipeline:
    """Tests for full pipeline execution."""

    def test_generate_and_send_full_pipeline(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
        tmp_path: Path,
    ) -> None:
        """Test full pipeline executes all steps."""
        mock_config.report_output_dir = tmp_path

        with (
            patch.object(ReportGenerator, "fetch_logs") as mock_fetch,
            patch.object(ReportGenerator, "process_logs") as mock_process,
            patch.object(ReportGenerator, "_generate_pdf") as mock_pdf,
            patch.object(ReportGenerator, "_send_email") as mock_email,
        ):
            mock_fetch.return_value = "log content"
            mock_process.return_value = sample_report_data
            mock_pdf.return_value = tmp_path / "report.pdf"

            generator = ReportGenerator(mock_config)
            result = generator.generate_and_send(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 15),
            )

            mock_fetch.assert_called_once()
            mock_process.assert_called_once()
            mock_pdf.assert_called_once()
            mock_email.assert_called_once()
            assert result == tmp_path / "report.pdf"

    def test_generate_without_email(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
        tmp_path: Path,
    ) -> None:
        """Test pipeline can skip email sending."""
        mock_config.report_output_dir = tmp_path

        with (
            patch.object(ReportGenerator, "fetch_logs") as mock_fetch,
            patch.object(ReportGenerator, "process_logs") as mock_process,
            patch.object(ReportGenerator, "_generate_pdf") as mock_pdf,
            patch.object(ReportGenerator, "_send_email") as mock_email,
        ):
            mock_fetch.return_value = "log content"
            mock_process.return_value = sample_report_data
            mock_pdf.return_value = tmp_path / "report.pdf"

            generator = ReportGenerator(mock_config)
            generator.generate_and_send(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 15),
                send_email=False,
            )

            mock_email.assert_not_called()


class TestReportGeneratorLogFetching:
    """Tests for log fetching."""

    def test_fetches_logs_for_date_range(
        self,
        mock_config: AppConfig,
    ) -> None:
        """Test logs are fetched for correct date range."""
        with patch("src.services.report_generator.LogFetcher") as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_logs_for_period.return_value = "log content"
            mock_fetcher_class.return_value.__enter__ = MagicMock(return_value=mock_fetcher)
            mock_fetcher_class.return_value.__exit__ = MagicMock(return_value=False)

            generator = ReportGenerator(mock_config)
            content = generator.fetch_logs(date(2024, 1, 15), date(2024, 1, 15))

            mock_fetcher.fetch_logs_for_period.assert_called_once_with(
                date(2024, 1, 15),
                date(2024, 1, 15),
            )
            assert content == "log content"


class TestReportGeneratorLogProcessing:
    """Tests for log processing."""

    def test_processes_logs_into_report_data(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
    ) -> None:
        """Test logs are processed into ReportData."""
        with (
            patch("src.services.report_generator.parse_log_lines") as mock_parse,
            patch("src.services.report_generator.extract_perf_reports") as mock_extract,
            patch("src.services.report_generator.aggregate_metrics") as mock_aggregate,
        ):
            log_content = "irrelevant"
            in_range = MagicMock()
            in_range.timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
            out_of_range = MagicMock()
            out_of_range.timestamp = datetime(2024, 2, 1, 12, 0, 0, tzinfo=UTC)
            mock_parse.return_value = iter([in_range, out_of_range])
            mock_extract.return_value = []
            mock_aggregate.return_value = sample_report_data

            generator = ReportGenerator(mock_config)
            result = generator.process_logs(
                log_content,
                date(2024, 1, 15),
                date(2024, 1, 15),
            )

            assert result == sample_report_data
            mock_aggregate.assert_called_once()
            filtered_entries = mock_aggregate.call_args[0][1]
            assert filtered_entries == [in_range]


class TestReportGeneratorPdfGeneration:
    """Tests for PDF generation."""

    def test_generates_pdf_with_correct_filename(
        self,
        mock_config: AppConfig,
        sample_report_data: ReportData,
        tmp_path: Path,
    ) -> None:
        """Test PDF filename includes date range."""
        mock_config.report_output_dir = tmp_path

        with patch.object(
            ReportGenerator,
            "_pdf_generator",
            create=True,
        ) as mock_pdf_gen:
            mock_pdf_gen.generate.return_value = tmp_path / "report.pdf"

            generator = ReportGenerator(mock_config)
            generator._pdf_generator = mock_pdf_gen

            generator._generate_pdf(
                sample_report_data,
                date(2024, 1, 15),
                date(2024, 1, 21),
            )

            call_args = mock_pdf_gen.generate.call_args
            output_path = call_args[0][1]
            assert "2024-01-15" in str(output_path)
            assert "2024-01-21" in str(output_path)
