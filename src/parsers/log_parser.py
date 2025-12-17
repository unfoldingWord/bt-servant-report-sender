"""Log parsing utilities for bt-servant logs."""

import json
import re
from collections.abc import Iterator

from src.models.log_entry import LogEntry
from src.models.perf_report import PerfReport


PERF_REPORT_PREFIX = "PerfReport "


def parse_log_lines(content: str) -> Iterator[LogEntry]:
    """Parse JSON lines format into LogEntry objects.

    Args:
        content: Raw log file content with one JSON object per line.

    Yields:
        LogEntry objects for each valid log line.
    """
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            yield LogEntry.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            continue


def extract_perf_reports(log_entries: Iterator[LogEntry]) -> list[PerfReport]:
    """Extract PerfReport entries from log messages.

    PerfReport entries are JSON objects embedded in the message field,
    prefixed with "PerfReport ".

    Args:
        log_entries: Iterator of LogEntry objects.

    Returns:
        List of PerfReport objects extracted from the logs.
    """
    perf_reports: list[PerfReport] = []

    for entry in log_entries:
        if not entry.message.startswith(PERF_REPORT_PREFIX):
            continue

        json_str = entry.message[len(PERF_REPORT_PREFIX) :]
        try:
            data = json.loads(json_str)
            perf_report = PerfReport.model_validate(data)
            perf_reports.append(perf_report)
        except (json.JSONDecodeError, ValueError):
            continue

    return perf_reports


def extract_intents(log_entries: list[LogEntry]) -> list[str]:
    """Extract detected intents from log messages.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        List of intent names detected in the logs.
    """
    intents: list[str] = []
    pattern = re.compile(r"extracted user intents: (.+)")

    for entry in log_entries:
        match = pattern.search(entry.message)
        if match:
            intent_str = match.group(1)
            for intent in intent_str.split(", "):
                intents.append(intent.strip())

    return intents


def extract_languages(log_entries: list[LogEntry]) -> dict[str, int]:
    """Extract language distribution from log messages.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        Dictionary mapping language codes to occurrence counts.
    """
    languages: dict[str, int] = {}
    pattern = re.compile(r"language code (\w+) detected")

    for entry in log_entries:
        match = pattern.search(entry.message)
        if match:
            lang_code = match.group(1)
            languages[lang_code] = languages.get(lang_code, 0) + 1

    return languages


def extract_warnings(log_entries: list[LogEntry]) -> list[str]:
    """Extract warning messages from logs.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        List of unique warning messages.
    """
    warnings: list[str] = []

    for entry in log_entries:
        if entry.level == "WARNING" and entry.message not in warnings:
            warnings.append(entry.message)

    return warnings


def extract_errors(log_entries: list[LogEntry]) -> list[str]:
    """Extract error messages from logs.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        List of unique error messages.
    """
    errors: list[str] = []

    for entry in log_entries:
        if entry.level == "ERROR" and entry.message not in errors:
            errors.append(entry.message)

    return errors


def count_by_level(log_entries: list[LogEntry]) -> dict[str, int]:
    """Count log entries by level.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        Dictionary mapping log levels to counts.
    """
    counts: dict[str, int] = {}

    for entry in log_entries:
        counts[entry.level] = counts.get(entry.level, 0) + 1

    return counts


def extract_unique_users(log_entries: list[LogEntry]) -> set[str]:
    """Extract unique user IDs from logs.

    Args:
        log_entries: List of LogEntry objects.

    Returns:
        Set of unique user IDs (excluding "-" placeholder).
    """
    users: set[str] = set()

    for entry in log_entries:
        if entry.user and entry.user != "-":
            users.add(entry.user)

    return users
