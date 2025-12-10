"""Tests for log entry models."""

from datetime import datetime

import pytest

from src.models.log_entry import LogEntry, LogFileEntry, LogFilesPayload


class TestLogEntry:
    """Tests for LogEntry model."""

    def test_parse_valid_log_entry(self) -> None:
        """Test parsing a valid log entry."""
        data = {
            "message": "Test message",
            "timestamp": "2025-12-09 22:30:35",
            "level": "INFO",
            "logger": "test.logger",
            "client_ip": "172.17.0.1",
            "taskName": "Task-1",
            "cid": "abc123",
            "user": "user123",
            "schema_version": "1.0.0",
        }

        entry = LogEntry.model_validate(data)

        assert entry.message == "Test message"
        assert entry.level == "INFO"
        assert entry.task_name == "Task-1"
        assert entry.user == "user123"
        assert isinstance(entry.timestamp, datetime)

    def test_parse_null_task_name(self) -> None:
        """Test parsing log entry with null taskName."""
        data = {
            "message": "Test message",
            "timestamp": "2025-12-09 22:30:35",
            "level": "INFO",
            "logger": "test.logger",
            "client_ip": "172.17.0.1",
            "taskName": None,
            "cid": "abc123",
            "user": "-",
            "schema_version": "1.0.0",
        }

        entry = LogEntry.model_validate(data)

        assert entry.task_name is None
        assert entry.user == "-"

    def test_missing_required_field_raises(self) -> None:
        """Test that missing required fields raise validation error."""
        data = {
            "message": "Test message",
            "timestamp": "2025-12-09 22:30:35",
        }

        with pytest.raises(ValueError, match="validation error"):
            LogEntry.model_validate(data)


class TestLogFileEntry:
    """Tests for LogFileEntry model."""

    def test_parse_valid_file_entry(self) -> None:
        """Test parsing a valid log file entry."""
        data = {
            "name": "bt_servant.log",
            "size_bytes": 1024,
            "modified_at": "2025-12-09T22:30:35Z",
            "created_at": "2025-12-09T20:00:00Z",
        }

        entry = LogFileEntry.model_validate(data)

        assert entry.name == "bt_servant.log"
        assert entry.size_bytes == 1024
        assert isinstance(entry.modified_at, datetime)


class TestLogFilesPayload:
    """Tests for LogFilesPayload model."""

    def test_parse_valid_payload(self) -> None:
        """Test parsing a valid log files payload."""
        data = {
            "files": [
                {
                    "name": "bt_servant.log",
                    "size_bytes": 1024,
                    "modified_at": "2025-12-09T22:30:35Z",
                    "created_at": "2025-12-09T20:00:00Z",
                },
                {
                    "name": "bt_servant.log.1",
                    "size_bytes": 5000,
                    "modified_at": "2025-12-08T22:30:35Z",
                    "created_at": "2025-12-08T20:00:00Z",
                },
            ],
            "total_files": 2,
            "total_size_bytes": 6024,
        }

        payload = LogFilesPayload.model_validate(data)

        assert payload.total_files == 2
        assert payload.total_size_bytes == 6024
        assert len(payload.files) == 2
        assert payload.files[0].name == "bt_servant.log"

    def test_empty_files_list(self) -> None:
        """Test parsing payload with no files."""
        data = {
            "files": [],
            "total_files": 0,
            "total_size_bytes": 0,
        }

        payload = LogFilesPayload.model_validate(data)

        assert payload.total_files == 0
        assert len(payload.files) == 0
