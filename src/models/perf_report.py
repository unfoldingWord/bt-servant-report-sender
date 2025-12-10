"""Performance report models from bt-servant logs."""

from decimal import Decimal

from pydantic import BaseModel


class Span(BaseModel):
    """A processing span within a PerfReport."""

    name: str
    duration_ms: Decimal
    duration_se: Decimal
    duration_percentage: str
    start_offset_ms: Decimal
    token_percentage: str
    input_tokens_expended: int | None = None
    output_tokens_expended: int | None = None
    total_tokens_expended: int | None = None
    input_cost_usd: Decimal | None = None
    output_cost_usd: Decimal | None = None
    total_cost_usd: Decimal | None = None


class IntentTotals(BaseModel):
    """Token and cost totals for a specific intent."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_input_tokens: int
    audio_input_tokens: int
    audio_output_tokens: int
    input_cost_usd: Decimal
    output_cost_usd: Decimal
    cached_input_cost_usd: Decimal
    audio_input_cost_usd: Decimal
    audio_output_cost_usd: Decimal
    total_cost_usd: Decimal
    duration_percentage: str
    token_percentage: str


class PerfReport(BaseModel):
    """Performance report for a single user interaction."""

    user_id: str
    trace_id: str
    total_ms: Decimal
    total_s: Decimal
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cached_input_tokens: int
    total_audio_input_tokens: int
    total_audio_output_tokens: int
    total_input_cost_usd: Decimal
    total_output_cost_usd: Decimal
    total_cached_input_cost_usd: Decimal
    total_audio_input_cost_usd: Decimal
    total_audio_output_cost_usd: Decimal
    total_cost_usd: Decimal
    grouped_totals_by_intent: dict[str, IntentTotals]
    spans: list[Span]
