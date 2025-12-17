"""Tests for PDF generator service."""

# pylint: disable=protected-access

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


try:
    import weasyprint  # noqa: F401  # pylint: disable=unused-import

    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

from src.models.report_data import (
    CostBreakdown,
    ExecutiveSummary,
    PerformanceMetrics,
    ReportData,
    SystemHealth,
    UsageAnalytics,
)
from src.services.pdf_generator import PdfGenerator


@pytest.fixture
def sample_report_data() -> ReportData:
    """Create sample report data for testing."""
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
            slowest_spans=[("process_request", Decimal("1500"))],
        ),
        usage=UsageAnalytics(
            unique_users=10,
            top_intents=[("greeting", 50), ("help", 30)],
            language_distribution={"en": 80, "es": 20},
        ),
        system_health=SystemHealth(
            total_requests=100,
            success_rate_percent=Decimal("99.0"),
            warning_count=5,
            error_count=1,
            warning_messages=["Test warning"],
            error_messages=["Test error"],
        ),
    )


class TestPdfGeneratorInit:
    """Tests for PdfGenerator initialization."""

    def test_uses_default_template_dir(self) -> None:
        """Test default template directory is set correctly."""
        generator = PdfGenerator()
        # Normalize paths for comparison
        assert generator._template_dir.name == "templates"

    def test_accepts_custom_template_dir(self, tmp_path: Path) -> None:
        """Test custom template directory is accepted."""
        generator = PdfGenerator(template_dir=tmp_path)
        assert generator._template_dir == tmp_path


class TestPdfGeneratorHtmlRendering:
    """Tests for HTML rendering."""

    def test_renders_html_with_report_data(
        self,
        sample_report_data: ReportData,
    ) -> None:
        """Test HTML rendering includes report data."""
        generator = PdfGenerator()
        html = generator._render_html(sample_report_data)

        assert "BT Servant Usage Report" in html
        assert "100" in html  # total_interactions
        assert "$1.50" in html  # total_cost
        assert "10" in html  # unique_users

    def test_renders_html_for_email_with_inline_styles(
        self,
        sample_report_data: ReportData,
    ) -> None:
        """Test email HTML includes inline styles."""
        generator = PdfGenerator()
        html = generator.render_html_for_email(sample_report_data)

        # Email version should have inline styles
        assert "<style>" in html
        assert "font-family:" in html

    def test_renders_performance_metrics(
        self,
        sample_report_data: ReportData,
    ) -> None:
        """Test performance metrics are rendered."""
        generator = PdfGenerator()
        html = generator._render_html(sample_report_data)

        assert "Performance Metrics" in html
        assert "P50" in html
        assert "P95" in html
        assert "P99" in html

    def test_renders_usage_analytics(
        self,
        sample_report_data: ReportData,
    ) -> None:
        """Test usage analytics are rendered."""
        generator = PdfGenerator()
        html = generator._render_html(sample_report_data)

        assert "Usage Analytics" in html
        assert "greeting" in html
        assert "help" in html

    def test_renders_system_health(
        self,
        sample_report_data: ReportData,
    ) -> None:
        """Test system health is rendered."""
        generator = PdfGenerator()
        html = generator._render_html(sample_report_data)

        assert "System Health" in html
        assert "99.0%" in html
        assert "Test warning" in html


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="weasyprint not installed")
class TestPdfGeneratorPdfCreation:
    """Tests for PDF file creation."""

    def test_creates_output_directory(
        self,
        tmp_path: Path,
        sample_report_data: ReportData,
    ) -> None:
        """Test output directory is created if needed."""
        generator = PdfGenerator()
        output_path = tmp_path / "subdir" / "report.pdf"

        with patch("weasyprint.HTML") as mock_html_class:
            mock_html = MagicMock()
            mock_html_class.return_value = mock_html

            generator.generate(sample_report_data, output_path)

            assert output_path.parent.exists()

    def test_calls_weasyprint_with_html(
        self,
        tmp_path: Path,
        sample_report_data: ReportData,
    ) -> None:
        """Test WeasyPrint HTML class is called correctly."""
        generator = PdfGenerator()
        output_path = tmp_path / "report.pdf"

        with patch("weasyprint.HTML") as mock_html_class:
            mock_html = MagicMock()
            mock_html_class.return_value = mock_html

            generator.generate(sample_report_data, output_path)

            mock_html_class.assert_called_once()
            call_kwargs = mock_html_class.call_args[1]
            assert "string" in call_kwargs
            assert "BT Servant Usage Report" in call_kwargs["string"]

    def test_returns_output_path(
        self,
        tmp_path: Path,
        sample_report_data: ReportData,
    ) -> None:
        """Test generate returns the output path."""
        generator = PdfGenerator()
        output_path = tmp_path / "report.pdf"

        with patch("weasyprint.HTML") as mock_html_class:
            mock_html = MagicMock()
            mock_html_class.return_value = mock_html

            result = generator.generate(sample_report_data, output_path)

            assert result == output_path
