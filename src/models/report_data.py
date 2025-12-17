"""Aggregated report data models."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ExecutiveSummary(BaseModel):
    """Executive summary section of the report."""

    date_range_start: date
    date_range_end: date
    total_interactions: int
    total_cost_usd: Decimal
    avg_response_time_ms: Decimal
    unique_users: int


class CostBreakdown(BaseModel):
    """Cost breakdown by token type."""

    total_input_cost_usd: Decimal
    total_output_cost_usd: Decimal
    total_cached_cost_usd: Decimal
    total_audio_cost_usd: Decimal
    total_cost_usd: Decimal


class IntentCostEntry(BaseModel):
    """Cost breakdown for a specific intent."""

    intent_name: str
    total_cost_usd: Decimal
    interaction_count: int
    avg_cost_per_interaction: Decimal


class PerformanceMetrics(BaseModel):
    """Performance metrics section of the report."""

    avg_response_time_ms: Decimal
    p50_response_time_ms: Decimal
    p95_response_time_ms: Decimal
    p99_response_time_ms: Decimal
    slowest_spans: list[tuple[str, Decimal]]


class UsageAnalytics(BaseModel):
    """Usage analytics section of the report."""

    unique_users: int
    top_intents: list[tuple[str, int]]
    language_distribution: dict[str, int]


class SystemHealth(BaseModel):
    """System health section of the report."""

    total_requests: int
    warning_count: int
    error_count: int
    success_rate_percent: Decimal
    warning_messages: list[str]
    error_messages: list[str]


class ReportData(BaseModel):
    """Complete aggregated report data."""

    generated_at: datetime
    executive_summary: ExecutiveSummary
    cost_breakdown: CostBreakdown
    cost_by_intent: list[IntentCostEntry]
    performance: PerformanceMetrics
    usage: UsageAnalytics
    system_health: SystemHealth
