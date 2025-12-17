"""Tests for metrics aggregator."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.models.log_entry import LogEntry
from src.models.perf_report import IntentTotals, PerfReport, Span
from src.parsers.metrics_aggregator import (
    aggregate_metrics,
    calculate_cost_breakdown,
    calculate_cost_by_intent,
    calculate_executive_summary,
    calculate_percentile,
    calculate_performance_metrics,
    calculate_system_health,
    calculate_usage_analytics,
    identify_bottleneck_spans,
)


@pytest.fixture
def sample_perf_report() -> PerfReport:
    """Create a sample PerfReport for testing."""
    return PerfReport(
        user_id="user1",
        trace_id="trace1",
        total_ms=Decimal("10000"),
        total_s=Decimal("10"),
        total_input_tokens=1000,
        total_output_tokens=100,
        total_tokens=1100,
        total_cached_input_tokens=50,
        total_audio_input_tokens=0,
        total_audio_output_tokens=0,
        total_input_cost_usd=Decimal("0.01"),
        total_output_cost_usd=Decimal("0.001"),
        total_cached_input_cost_usd=Decimal("0.0001"),
        total_audio_input_cost_usd=Decimal("0"),
        total_audio_output_cost_usd=Decimal("0"),
        total_cost_usd=Decimal("0.0111"),
        grouped_totals_by_intent={
            "test-intent": IntentTotals(
                input_tokens=500,
                output_tokens=50,
                total_tokens=550,
                cached_input_tokens=0,
                audio_input_tokens=0,
                audio_output_tokens=0,
                input_cost_usd=Decimal("0.005"),
                output_cost_usd=Decimal("0.0005"),
                cached_input_cost_usd=Decimal("0"),
                audio_input_cost_usd=Decimal("0"),
                audio_output_cost_usd=Decimal("0"),
                total_cost_usd=Decimal("0.0055"),
                duration_percentage="50%",
                token_percentage="50%",
            )
        },
        spans=[
            Span(
                name="process_message",
                duration_ms=Decimal("9000"),
                duration_se=Decimal("9"),
                duration_percentage="90%",
                start_offset_ms=Decimal("0"),
                token_percentage="0%",
            ),
            Span(
                name="send_response",
                duration_ms=Decimal("1000"),
                duration_se=Decimal("1"),
                duration_percentage="10%",
                start_offset_ms=Decimal("9000"),
                token_percentage="0%",
            ),
        ],
    )


@pytest.fixture
def sample_log_entries() -> list[LogEntry]:
    """Create sample log entries for testing."""
    base_time = datetime(2025, 12, 9, 22, 30, 0, tzinfo=UTC)
    return [
        LogEntry(
            message="extracted user intents: test-intent",
            timestamp=base_time,
            level="INFO",
            logger="test",
            client_ip="127.0.0.1",
            cid="cid1",
            user="user1",
            schema_version="1.0.0",
        ),
        LogEntry(
            message="language code en detected by gpt-4o.",
            timestamp=base_time,
            level="INFO",
            logger="test",
            client_ip="127.0.0.1",
            cid="cid1",
            user="user1",
            schema_version="1.0.0",
        ),
        LogEntry(
            message="Warning: something happened",
            timestamp=base_time,
            level="WARNING",
            logger="test",
            client_ip="127.0.0.1",
            cid="cid1",
            user="user1",
            schema_version="1.0.0",
        ),
    ]


class TestCalculatePercentile:
    """Tests for calculate_percentile function."""

    def test_empty_list(self) -> None:
        """Test percentile of empty list returns zero."""
        result = calculate_percentile([], 50)
        assert result == Decimal("0")

    def test_single_value(self) -> None:
        """Test percentile of single value."""
        result = calculate_percentile([Decimal("100")], 50)
        assert result == Decimal("100")

    def test_p50(self) -> None:
        """Test 50th percentile calculation."""
        values = [Decimal(i) for i in range(1, 101)]
        result = calculate_percentile(values, 50)
        assert result == Decimal("50")

    def test_p95(self) -> None:
        """Test 95th percentile calculation."""
        values = [Decimal(i) for i in range(1, 101)]
        result = calculate_percentile(values, 95)
        assert result == Decimal("95")


class TestCalculateCostBreakdown:
    """Tests for calculate_cost_breakdown function."""

    def test_empty_reports(self) -> None:
        """Test cost breakdown with no reports."""
        result = calculate_cost_breakdown([])
        assert result.total_cost_usd == Decimal("0")

    def test_single_report(self, sample_perf_report: PerfReport) -> None:
        """Test cost breakdown with single report."""
        result = calculate_cost_breakdown([sample_perf_report])
        assert result.total_input_cost_usd == Decimal("0.01")
        assert result.total_output_cost_usd == Decimal("0.001")
        assert result.total_cost_usd == Decimal("0.0111")


class TestCalculateCostByIntent:
    """Tests for calculate_cost_by_intent function."""

    def test_empty_reports(self) -> None:
        """Test cost by intent with no reports."""
        result = calculate_cost_by_intent([])
        assert result == []

    def test_single_report_with_intent(self, sample_perf_report: PerfReport) -> None:
        """Test cost by intent with single report."""
        result = calculate_cost_by_intent([sample_perf_report])
        assert len(result) == 1
        assert result[0].intent_name == "test-intent"
        assert result[0].total_cost_usd == Decimal("0.0055")
        assert result[0].interaction_count == 1


class TestCalculatePerformanceMetrics:
    """Tests for calculate_performance_metrics function."""

    def test_empty_reports(self) -> None:
        """Test performance metrics with no reports."""
        result = calculate_performance_metrics([])
        assert result.avg_response_time_ms == Decimal("0")
        assert result.slowest_spans == []

    def test_single_report(self, sample_perf_report: PerfReport) -> None:
        """Test performance metrics with single report."""
        result = calculate_performance_metrics([sample_perf_report])
        assert result.avg_response_time_ms == Decimal("10000")
        assert len(result.slowest_spans) == 2
        assert result.slowest_spans[0][0] == "process_message"


class TestIdentifyBottleneckSpans:
    """Tests for identify_bottleneck_spans function."""

    def test_empty_reports(self) -> None:
        """Test bottleneck identification with no reports."""
        result = identify_bottleneck_spans([])
        assert result == []

    def test_returns_top_n(self, sample_perf_report: PerfReport) -> None:
        """Test that only top_n spans are returned."""
        result = identify_bottleneck_spans([sample_perf_report], top_n=1)
        assert len(result) == 1
        assert result[0][0] == "process_message"


class TestCalculateUsageAnalytics:
    """Tests for calculate_usage_analytics function."""

    def test_empty_entries(self) -> None:
        """Test usage analytics with no entries."""
        result = calculate_usage_analytics([])
        assert result.unique_users == 0
        assert result.top_intents == []

    def test_with_entries(self, sample_log_entries: list[LogEntry]) -> None:
        """Test usage analytics with sample entries."""
        result = calculate_usage_analytics(sample_log_entries)
        assert result.unique_users == 1
        assert ("test-intent", 1) in result.top_intents
        assert result.language_distribution == {"en": 1}


class TestCalculateSystemHealth:
    """Tests for calculate_system_health function."""

    def test_empty_entries(self) -> None:
        """Test system health with no entries."""
        result = calculate_system_health([])
        assert result.total_requests == 0
        assert result.success_rate_percent == Decimal("100")
        assert result.error_messages == []

    def test_with_entries(self, sample_log_entries: list[LogEntry]) -> None:
        """Test system health with sample entries."""
        result = calculate_system_health(sample_log_entries)
        assert result.total_requests == 3
        assert result.warning_count == 1
        assert result.error_count == 0
        assert result.success_rate_percent == Decimal("100.00")
        assert result.error_messages == []


class TestCalculateExecutiveSummary:
    """Tests for calculate_executive_summary function."""

    def test_empty_data(self) -> None:
        """Test executive summary with no data."""
        result = calculate_executive_summary([], [], date(2025, 12, 1), date(2025, 12, 7))
        assert result.total_interactions == 0
        assert result.total_cost_usd == Decimal("0")
        assert result.unique_users == 0

    def test_with_data(
        self,
        sample_perf_report: PerfReport,
        sample_log_entries: list[LogEntry],
    ) -> None:
        """Test executive summary with sample data."""
        result = calculate_executive_summary(
            [sample_perf_report],
            sample_log_entries,
            date(2025, 12, 1),
            date(2025, 12, 7),
        )
        assert result.total_interactions == 1
        assert result.total_cost_usd == Decimal("0.0111")
        assert result.unique_users == 1
        assert result.avg_response_time_ms == Decimal("10000")


class TestAggregateMetrics:
    """Tests for aggregate_metrics function."""

    def test_full_aggregation(
        self,
        sample_perf_report: PerfReport,
        sample_log_entries: list[LogEntry],
    ) -> None:
        """Test full metrics aggregation."""
        result = aggregate_metrics(
            [sample_perf_report],
            sample_log_entries,
            date(2025, 12, 1),
            date(2025, 12, 7),
        )

        assert result.executive_summary.total_interactions == 1
        assert result.cost_breakdown.total_cost_usd == Decimal("0.0111")
        assert len(result.cost_by_intent) == 1
        assert result.performance.avg_response_time_ms == Decimal("10000")
        assert result.usage.unique_users == 1
        assert result.system_health.warning_count == 1
        assert result.system_health.error_messages == []
