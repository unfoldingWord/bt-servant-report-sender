"""Tests for performance report models."""

from decimal import Decimal

from src.models.perf_report import IntentTotals, PerfReport, Span


class TestSpan:
    """Tests for Span model."""

    def test_parse_span_without_tokens(self) -> None:
        """Test parsing a span without token information."""
        data = {
            "name": "bt_servant:verify_facebook_signature",
            "duration_ms": 0.05,
            "duration_se": 0.0,
            "duration_percentage": "0.0%",
            "start_offset_ms": 0.0,
            "token_percentage": "0.0%",
        }

        span = Span.model_validate(data)

        assert span.name == "bt_servant:verify_facebook_signature"
        assert span.duration_ms == Decimal("0.05")
        assert span.input_tokens_expended is None

    def test_parse_span_with_tokens(self) -> None:
        """Test parsing a span with token information."""
        data = {
            "name": "brain:determine_query_language_node",
            "duration_ms": 1180.85,
            "duration_se": 1.18,
            "duration_percentage": "10.0%",
            "start_offset_ms": 991.65,
            "token_percentage": "4.6%",
            "input_tokens_expended": 290,
            "output_tokens_expended": 6,
            "total_tokens_expended": 296,
            "input_cost_usd": 0.000044,
            "output_cost_usd": 0.000004,
            "total_cost_usd": 0.000047,
        }

        span = Span.model_validate(data)

        assert span.input_tokens_expended == 290
        assert span.total_cost_usd == Decimal("0.000047")


class TestIntentTotals:
    """Tests for IntentTotals model."""

    def test_parse_intent_totals(self) -> None:
        """Test parsing intent totals."""
        data = {
            "input_tokens": 1375,
            "output_tokens": 150,
            "total_tokens": 1525,
            "cached_input_tokens": 0,
            "audio_input_tokens": 0,
            "audio_output_tokens": 0,
            "input_cost_usd": 0.003437,
            "output_cost_usd": 0.0015,
            "cached_input_cost_usd": 0.0,
            "audio_input_cost_usd": 0.0,
            "audio_output_cost_usd": 0.0,
            "total_cost_usd": 0.004937,
            "duration_percentage": "17.6%",
            "token_percentage": "20.0%",
        }

        totals = IntentTotals.model_validate(data)

        assert totals.total_tokens == 1525
        assert totals.total_cost_usd == Decimal("0.004937")


class TestPerfReport:
    """Tests for PerfReport model."""

    def test_parse_minimal_perf_report(self) -> None:
        """Test parsing a PerfReport with minimal data."""
        data = {
            "user_id": "kwlv1sXnUvYT9dnn",
            "trace_id": "wamid.test123",
            "total_ms": 11780.07,
            "total_s": 11.78,
            "total_input_tokens": 6323,
            "total_output_tokens": 61,
            "total_tokens": 6384,
            "total_cached_input_tokens": 0,
            "total_audio_input_tokens": 0,
            "total_audio_output_tokens": 0,
            "total_input_cost_usd": 0.014433,
            "total_output_cost_usd": 0.000497,
            "total_cached_input_cost_usd": 0.0,
            "total_audio_input_cost_usd": 0.0,
            "total_audio_output_cost_usd": 0.0,
            "total_cost_usd": 0.01493,
            "grouped_totals_by_intent": {},
            "spans": [],
        }

        report = PerfReport.model_validate(data)

        assert report.user_id == "kwlv1sXnUvYT9dnn"
        assert report.total_ms == Decimal("11780.07")
        assert report.total_cost_usd == Decimal("0.01493")
        assert len(report.spans) == 0

    def test_parse_full_perf_report(self) -> None:
        """Test parsing a full PerfReport with spans and intents."""
        data = {
            "user_id": "kwlv1sXnUvYT9dnn",
            "trace_id": "wamid.test123",
            "total_ms": 13343.4,
            "total_s": 13.34,
            "total_input_tokens": 7398,
            "total_output_tokens": 217,
            "total_tokens": 7615,
            "total_cached_input_tokens": 0,
            "total_audio_input_tokens": 0,
            "total_audio_output_tokens": 0,
            "total_input_cost_usd": 0.017113,
            "total_output_cost_usd": 0.002057,
            "total_cached_input_cost_usd": 0.0,
            "total_audio_input_cost_usd": 0.0,
            "total_audio_output_cost_usd": 0.0,
            "total_cost_usd": 0.01917,
            "grouped_totals_by_intent": {
                "retrieve-system-information": {
                    "input_tokens": 1375,
                    "output_tokens": 150,
                    "total_tokens": 1525,
                    "cached_input_tokens": 0,
                    "audio_input_tokens": 0,
                    "audio_output_tokens": 0,
                    "input_cost_usd": 0.003437,
                    "output_cost_usd": 0.0015,
                    "cached_input_cost_usd": 0.0,
                    "audio_input_cost_usd": 0.0,
                    "audio_output_cost_usd": 0.0,
                    "total_cost_usd": 0.004937,
                    "duration_percentage": "17.6%",
                    "token_percentage": "20.0%",
                },
            },
            "spans": [
                {
                    "name": "bt_servant:process_message",
                    "duration_ms": 13342.66,
                    "duration_se": 13.34,
                    "duration_percentage": "100.0%",
                    "start_offset_ms": 0.74,
                    "token_percentage": "0.0%",
                },
            ],
        }

        report = PerfReport.model_validate(data)

        assert report.total_cost_usd == Decimal("0.01917")
        assert len(report.grouped_totals_by_intent) == 1
        assert "retrieve-system-information" in report.grouped_totals_by_intent
        assert len(report.spans) == 1
        assert report.spans[0].name == "bt_servant:process_message"
