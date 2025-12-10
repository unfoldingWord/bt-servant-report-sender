"""Tests for log parser."""

from src.parsers.log_parser import (
    count_by_level,
    extract_intents,
    extract_languages,
    extract_perf_reports,
    extract_unique_users,
    extract_warnings,
    parse_log_lines,
)


class TestParseLogLines:
    """Tests for parse_log_lines function."""

    def test_parse_single_line(self, sample_log_line: str) -> None:
        """Test parsing a single log line."""
        entries = list(parse_log_lines(sample_log_line))

        assert len(entries) == 1
        assert entries[0].user == "kwlv1sXnUvYT9dnn"
        assert entries[0].level == "INFO"

    def test_parse_multiple_lines(self, sample_multi_line_logs: str) -> None:
        """Test parsing multiple log lines."""
        entries = list(parse_log_lines(sample_multi_line_logs))

        assert len(entries) == 4

    def test_skip_empty_lines(self, sample_log_line: str) -> None:
        """Test that empty lines are skipped."""
        content = f"\n\n{sample_log_line}\n\n"
        entries = list(parse_log_lines(content))

        assert len(entries) == 1

    def test_skip_invalid_json(self, sample_log_line: str) -> None:
        """Test that invalid JSON lines are skipped."""
        content = f"not valid json\n{sample_log_line}\nalso not valid"
        entries = list(parse_log_lines(content))

        assert len(entries) == 1


class TestExtractPerfReports:
    """Tests for extract_perf_reports function."""

    def test_extract_perf_report(self, sample_perf_report_log_line: str) -> None:
        """Test extracting PerfReport from log entries."""
        entries = list(parse_log_lines(sample_perf_report_log_line))
        reports = extract_perf_reports(iter(entries))

        assert len(reports) == 1
        assert reports[0].user_id == "kwlv1sXnUvYT9dnn"
        assert reports[0].total_tokens == 6384

    def test_no_perf_reports(self, sample_log_line: str) -> None:
        """Test when no PerfReport entries exist."""
        entries = list(parse_log_lines(sample_log_line))
        reports = extract_perf_reports(iter(entries))

        assert len(reports) == 0


class TestExtractIntents:
    """Tests for extract_intents function."""

    def test_extract_single_intent(self, sample_intent_log_line: str) -> None:
        """Test extracting a single intent."""
        entries = list(parse_log_lines(sample_intent_log_line))
        intents = extract_intents(entries)

        assert len(intents) == 1
        assert intents[0] == "clear-dev-agentic-mcp"

    def test_no_intents(self, sample_log_line: str) -> None:
        """Test when no intents are found."""
        entries = list(parse_log_lines(sample_log_line))
        intents = extract_intents(entries)

        assert len(intents) == 0


class TestExtractLanguages:
    """Tests for extract_languages function."""

    def test_extract_language(self, sample_language_log_line: str) -> None:
        """Test extracting language detection."""
        entries = list(parse_log_lines(sample_language_log_line))
        languages = extract_languages(entries)

        assert languages == {"en": 1}

    def test_no_languages(self, sample_log_line: str) -> None:
        """Test when no language detections are found."""
        entries = list(parse_log_lines(sample_log_line))
        languages = extract_languages(entries)

        assert not languages


class TestExtractWarnings:
    """Tests for extract_warnings function."""

    def test_extract_warning(self, sample_warning_log_line: str) -> None:
        """Test extracting warning messages."""
        entries = list(parse_log_lines(sample_warning_log_line))
        warnings = extract_warnings(entries)

        assert len(warnings) == 1
        assert "No follow-up question defined" in warnings[0]

    def test_no_warnings(self, sample_log_line: str) -> None:
        """Test when no warnings exist."""
        entries = list(parse_log_lines(sample_log_line))
        warnings = extract_warnings(entries)

        assert len(warnings) == 0


class TestCountByLevel:
    """Tests for count_by_level function."""

    def test_count_levels(self, sample_multi_line_logs: str) -> None:
        """Test counting log entries by level."""
        entries = list(parse_log_lines(sample_multi_line_logs))
        counts = count_by_level(entries)

        assert counts["INFO"] == 3
        assert counts["WARNING"] == 1


class TestExtractUniqueUsers:
    """Tests for extract_unique_users function."""

    def test_extract_users(self, sample_multi_line_logs: str) -> None:
        """Test extracting unique users."""
        entries = list(parse_log_lines(sample_multi_line_logs))
        users = extract_unique_users(entries)

        assert len(users) == 1
        assert "kwlv1sXnUvYT9dnn" in users

    def test_exclude_placeholder_user(self) -> None:
        """Test that '-' placeholder user is excluded."""
        log_line = (
            '{"message": "System init", "client_ip": "-", "taskName": "Task-1", '
            '"timestamp": "2025-12-09 22:30:30", "level": "INFO", '
            '"logger": "test", "cid": "-", "user": "-", "schema_version": "1.0.0"}'
        )
        entries = list(parse_log_lines(log_line))
        users = extract_unique_users(entries)

        assert len(users) == 0
