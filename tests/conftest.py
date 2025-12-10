"""Shared test fixtures for bt-servant-report-sender."""

import pytest


@pytest.fixture
def sample_log_line() -> str:
    """Return a single sample log line."""
    return (
        '{"message": "text message from kwlv1sXnUvYT9dnn received.", '
        '"client_ip": "172.17.0.1", "taskName": "Task-3", '
        '"timestamp": "2025-12-09 22:30:35", "level": "INFO", '
        '"logger": "bt_servant_engine.apps.api.routes.webhooks", '
        '"cid": "fa6e603bb0274d1990236920564b6e80", "user": "kwlv1sXnUvYT9dnn", '
        '"schema_version": "1.0.0"}'
    )


@pytest.fixture
def sample_warning_log_line() -> str:
    """Return a sample warning log line."""
    return (
        '{"message": "[followup] No follow-up question defined for intent=clear-dev-agentic-mcp", '
        '"client_ip": "172.17.0.1", "taskName": null, '
        '"timestamp": "2025-12-09 22:30:42", "level": "WARNING", '
        '"logger": "bt_servant_engine.services.intents.followup_questions", '
        '"cid": "fa6e603bb0274d1990236920564b6e80", "user": "kwlv1sXnUvYT9dnn", '
        '"schema_version": "1.0.0"}'
    )


@pytest.fixture
def sample_intent_log_line() -> str:
    """Return a sample intent detection log line."""
    return (
        '{"message": "extracted user intents: clear-dev-agentic-mcp", '
        '"client_ip": "172.17.0.1", "taskName": null, '
        '"timestamp": "2025-12-09 22:30:41", "level": "INFO", '
        '"logger": "bt_servant_engine.services.preprocessing", '
        '"cid": "fa6e603bb0274d1990236920564b6e80", "user": "kwlv1sXnUvYT9dnn", '
        '"schema_version": "1.0.0"}'
    )


@pytest.fixture
def sample_language_log_line() -> str:
    """Return a sample language detection log line."""
    return (
        '{"message": "language code en detected by gpt-4o.", '
        '"client_ip": "172.17.0.1", "taskName": null, '
        '"timestamp": "2025-12-09 22:30:37", "level": "INFO", '
        '"logger": "bt_servant_engine.services.preprocessing", '
        '"cid": "fa6e603bb0274d1990236920564b6e80", "user": "kwlv1sXnUvYT9dnn", '
        '"schema_version": "1.0.0"}'
    )


@pytest.fixture
def sample_perf_report_log_line() -> str:
    """Return a sample PerfReport log line."""
    return (
        '{"message": "PerfReport {\\"user_id\\":\\"kwlv1sXnUvYT9dnn\\",\\"trace_id\\":\\"test123\\",'
        '\\"total_ms\\":11780.07,\\"total_s\\":11.78,\\"total_input_tokens\\":6323,'
        '\\"total_output_tokens\\":61,\\"total_tokens\\":6384,\\"total_cached_input_tokens\\":0,'
        '\\"total_audio_input_tokens\\":0,\\"total_audio_output_tokens\\":0,'
        '\\"total_input_cost_usd\\":0.014433,\\"total_output_cost_usd\\":0.000497,'
        '\\"total_cached_input_cost_usd\\":0.0,\\"total_audio_input_cost_usd\\":0.0,'
        '\\"total_audio_output_cost_usd\\":0.0,\\"total_cost_usd\\":0.01493,'
        '\\"grouped_totals_by_intent\\":{},\\"spans\\":[]}", '
        '"client_ip": "172.17.0.1", "taskName": "Task-4", '
        '"timestamp": "2025-12-09 22:30:47", "level": "INFO", '
        '"logger": "bt_servant_engine.apps.api.routes.webhooks", '
        '"cid": "fa6e603bb0274d1990236920564b6e80", "user": "kwlv1sXnUvYT9dnn", '
        '"schema_version": "1.0.0"}'
    )


@pytest.fixture
def sample_multi_line_logs(
    sample_log_line: str,
    sample_warning_log_line: str,
    sample_intent_log_line: str,
    sample_language_log_line: str,
) -> str:
    """Return multiple log lines combined."""
    return "\n".join(
        [
            sample_log_line,
            sample_warning_log_line,
            sample_intent_log_line,
            sample_language_log_line,
        ]
    )
