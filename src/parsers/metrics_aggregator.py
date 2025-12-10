"""Metrics aggregation for report generation."""

from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal

from src.models.log_entry import LogEntry
from src.models.perf_report import PerfReport
from src.models.report_data import (
    CostBreakdown,
    ExecutiveSummary,
    IntentCostEntry,
    PerformanceMetrics,
    ReportData,
    SystemHealth,
    UsageAnalytics,
)
from src.parsers.log_parser import (
    count_by_level,
    extract_intents,
    extract_languages,
    extract_unique_users,
    extract_warnings,
)


def aggregate_metrics(
    perf_reports: list[PerfReport],
    log_entries: list[LogEntry],
    start_date: date,
    end_date: date,
) -> ReportData:
    """Aggregate all metrics into final report data structure.

    Args:
        perf_reports: List of PerfReport objects from logs.
        log_entries: List of LogEntry objects from logs.
        start_date: Start date of the report period.
        end_date: End date of the report period.

    Returns:
        Complete ReportData with all sections populated.
    """
    return ReportData(
        generated_at=datetime.now(UTC),
        executive_summary=calculate_executive_summary(
            perf_reports, log_entries, start_date, end_date
        ),
        cost_breakdown=calculate_cost_breakdown(perf_reports),
        cost_by_intent=calculate_cost_by_intent(perf_reports),
        performance=calculate_performance_metrics(perf_reports),
        usage=calculate_usage_analytics(log_entries),
        system_health=calculate_system_health(log_entries),
    )


def calculate_executive_summary(
    perf_reports: list[PerfReport],
    log_entries: list[LogEntry],
    start_date: date,
    end_date: date,
) -> ExecutiveSummary:
    """Calculate executive summary metrics.

    Args:
        perf_reports: List of PerfReport objects.
        log_entries: List of LogEntry objects.
        start_date: Report period start date.
        end_date: Report period end date.

    Returns:
        ExecutiveSummary with aggregated metrics.
    """
    total_interactions = len(perf_reports)
    total_cost = sum((r.total_cost_usd for r in perf_reports), Decimal("0"))
    unique_users = extract_unique_users(log_entries)

    avg_response_time = Decimal("0")
    if total_interactions > 0:
        total_time = sum((r.total_ms for r in perf_reports), Decimal("0"))
        avg_response_time = total_time / total_interactions

    return ExecutiveSummary(
        date_range_start=start_date,
        date_range_end=end_date,
        total_interactions=total_interactions,
        total_cost_usd=total_cost,
        avg_response_time_ms=avg_response_time,
        unique_users=len(unique_users),
    )


def calculate_cost_breakdown(perf_reports: list[PerfReport]) -> CostBreakdown:
    """Calculate cost breakdown by token type.

    Args:
        perf_reports: List of PerfReport objects.

    Returns:
        CostBreakdown with costs by token type.
    """
    total_input = sum((r.total_input_cost_usd for r in perf_reports), Decimal("0"))
    total_output = sum((r.total_output_cost_usd for r in perf_reports), Decimal("0"))
    total_cached = sum((r.total_cached_input_cost_usd for r in perf_reports), Decimal("0"))
    total_audio_in = sum((r.total_audio_input_cost_usd for r in perf_reports), Decimal("0"))
    total_audio_out = sum((r.total_audio_output_cost_usd for r in perf_reports), Decimal("0"))
    total_audio = total_audio_in + total_audio_out
    total_cost = sum((r.total_cost_usd for r in perf_reports), Decimal("0"))

    return CostBreakdown(
        total_input_cost_usd=total_input,
        total_output_cost_usd=total_output,
        total_cached_cost_usd=total_cached,
        total_audio_cost_usd=total_audio,
        total_cost_usd=total_cost,
    )


def calculate_cost_by_intent(perf_reports: list[PerfReport]) -> list[IntentCostEntry]:
    """Calculate cost breakdown by intent.

    Args:
        perf_reports: List of PerfReport objects.

    Returns:
        List of IntentCostEntry sorted by total cost descending.
    """
    intent_costs: dict[str, Decimal] = {}
    intent_counts: dict[str, int] = {}

    for report in perf_reports:
        for intent_name, totals in report.grouped_totals_by_intent.items():
            intent_costs[intent_name] = (
                intent_costs.get(intent_name, Decimal("0")) + totals.total_cost_usd
            )
            intent_counts[intent_name] = intent_counts.get(intent_name, 0) + 1

    entries = []
    for intent_name, total_cost in intent_costs.items():
        count = intent_counts[intent_name]
        avg_cost = total_cost / count if count > 0 else Decimal("0")
        entries.append(
            IntentCostEntry(
                intent_name=intent_name,
                total_cost_usd=total_cost,
                interaction_count=count,
                avg_cost_per_interaction=avg_cost,
            )
        )

    return sorted(entries, key=lambda x: x.total_cost_usd, reverse=True)


def calculate_performance_metrics(perf_reports: list[PerfReport]) -> PerformanceMetrics:
    """Calculate response time statistics and identify bottlenecks.

    Args:
        perf_reports: List of PerfReport objects.

    Returns:
        PerformanceMetrics with response time stats and slowest spans.
    """
    if not perf_reports:
        return PerformanceMetrics(
            avg_response_time_ms=Decimal("0"),
            p50_response_time_ms=Decimal("0"),
            p95_response_time_ms=Decimal("0"),
            p99_response_time_ms=Decimal("0"),
            slowest_spans=[],
        )

    response_times = sorted(r.total_ms for r in perf_reports)
    avg_time = sum(response_times, Decimal("0")) / len(response_times)

    return PerformanceMetrics(
        avg_response_time_ms=avg_time,
        p50_response_time_ms=calculate_percentile(response_times, 50),
        p95_response_time_ms=calculate_percentile(response_times, 95),
        p99_response_time_ms=calculate_percentile(response_times, 99),
        slowest_spans=identify_bottleneck_spans(perf_reports),
    )


def calculate_percentile(values: list[Decimal], percentile: int) -> Decimal:
    """Calculate the given percentile of a sorted list of values.

    Args:
        values: Sorted list of Decimal values.
        percentile: Percentile to calculate (0-100).

    Returns:
        The value at the given percentile.
    """
    if not values:
        return Decimal("0")

    index = (len(values) - 1) * percentile // 100
    return values[index]


def identify_bottleneck_spans(
    perf_reports: list[PerfReport], top_n: int = 5
) -> list[tuple[str, Decimal]]:
    """Identify the slowest spans by average duration.

    Args:
        perf_reports: List of PerfReport objects.
        top_n: Number of top spans to return.

    Returns:
        List of (span_name, avg_duration_ms) tuples, sorted by duration descending.
    """
    span_totals: dict[str, Decimal] = {}
    span_counts: dict[str, int] = {}

    for report in perf_reports:
        for span in report.spans:
            span_totals[span.name] = span_totals.get(span.name, Decimal("0")) + span.duration_ms
            span_counts[span.name] = span_counts.get(span.name, 0) + 1

    span_avgs = []
    for name, total in span_totals.items():
        avg = total / span_counts[name]
        span_avgs.append((name, avg))

    return sorted(span_avgs, key=lambda x: x[1], reverse=True)[:top_n]


def calculate_usage_analytics(log_entries: list[LogEntry]) -> UsageAnalytics:
    """Calculate usage analytics from log entries.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        UsageAnalytics with user counts, intent distribution, and languages.
    """
    unique_users = extract_unique_users(log_entries)
    intents = extract_intents(log_entries)
    languages = extract_languages(log_entries)

    intent_counter = Counter(intents)
    top_intents = intent_counter.most_common(10)

    return UsageAnalytics(
        unique_users=len(unique_users),
        top_intents=top_intents,
        language_distribution=languages,
    )


def calculate_system_health(log_entries: list[LogEntry]) -> SystemHealth:
    """Calculate system health metrics from log entries.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        SystemHealth with error/warning counts and success rate.
    """
    level_counts = count_by_level(log_entries)
    warnings = extract_warnings(log_entries)

    total_requests = sum(level_counts.values())
    warning_count = level_counts.get("WARNING", 0)
    error_count = level_counts.get("ERROR", 0)

    success_count = total_requests - error_count
    success_rate = Decimal("100")
    if total_requests > 0:
        success_rate = Decimal(success_count) / Decimal(total_requests) * 100

    return SystemHealth(
        total_requests=total_requests,
        warning_count=warning_count,
        error_count=error_count,
        success_rate_percent=success_rate.quantize(Decimal("0.01")),
        warning_messages=warnings[:10],
    )
