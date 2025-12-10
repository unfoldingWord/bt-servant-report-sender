"""Tests for log fetcher service."""

# pylint: disable=protected-access

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.config import AppConfig
from src.models.log_entry import LogFileEntry, LogFilesPayload
from src.services.log_fetcher import LogFetcher


@pytest.fixture
def mock_config() -> AppConfig:
    """Create mock configuration."""
    return AppConfig(
        bt_servant_api_url="https://api.example.com",
        bt_servant_api_token="test-token",
        smtp_user="test@example.com",
        smtp_password="password",
        email_from="test@example.com",
        email_to=["recipient@example.com"],
    )


@pytest.fixture
def log_files_payload() -> LogFilesPayload:
    """Create sample log files payload."""
    return LogFilesPayload(
        files=[
            LogFileEntry(
                name="app-2024-01-15.log",
                size_bytes=1024,
                modified_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
                created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            ),
            LogFileEntry(
                name="app-2024-01-14.log",
                size_bytes=2048,
                modified_at=datetime(2024, 1, 14, 12, 0, 0, tzinfo=UTC),
                created_at=datetime(2024, 1, 14, 10, 0, 0, tzinfo=UTC),
            ),
        ],
        total_files=2,
        total_size_bytes=3072,
    )


class TestLogFetcherContextManager:
    """Tests for context manager behavior."""

    def test_enters_context_successfully(self, mock_config: AppConfig) -> None:
        """Test context manager entry creates client."""
        with (
            patch("src.services.log_fetcher.httpx.Client") as mock_client_class,
            LogFetcher(mock_config) as fetcher,
        ):
            assert fetcher._client is not None
            mock_client_class.assert_called_once()

    def test_exits_context_closes_client(self, mock_config: AppConfig) -> None:
        """Test context manager exit closes client."""
        with patch("src.services.log_fetcher.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with LogFetcher(mock_config):
                pass

            mock_client.close.assert_called_once()

    def test_auth_headers_included(self, mock_config: AppConfig) -> None:
        """Test authorization headers are set correctly."""
        with (
            patch("src.services.log_fetcher.httpx.Client") as mock_client_class,
            LogFetcher(mock_config),
        ):
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"


class TestLogFetcherRequiresContext:
    """Tests for context manager requirement."""

    def test_list_log_files_requires_context(self, mock_config: AppConfig) -> None:
        """Test list_log_files raises error outside context."""
        fetcher = LogFetcher(mock_config)
        with pytest.raises(RuntimeError, match="must be used as context manager"):
            fetcher.list_log_files()

    def test_download_log_file_requires_context(self, mock_config: AppConfig) -> None:
        """Test download_log_file raises error outside context."""
        fetcher = LogFetcher(mock_config)
        with pytest.raises(RuntimeError, match="must be used as context manager"):
            fetcher.download_log_file("test.log")


class TestLogFetcherApiCalls:
    """Tests for API method calls."""

    def test_list_log_files_calls_api(
        self,
        mock_config: AppConfig,
        log_files_payload: LogFilesPayload,
    ) -> None:
        """Test list_log_files makes correct API call."""
        with patch("src.services.log_fetcher.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = log_files_payload.model_dump()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with LogFetcher(mock_config) as fetcher:
                result = fetcher.list_log_files()

            mock_client.get.assert_called_with("/admin/logs/files")
            assert result.total_files == 2

    def test_list_recent_files_with_params(self, mock_config: AppConfig) -> None:
        """Test list_recent_files passes parameters correctly."""
        with patch("src.services.log_fetcher.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "files": [],
                "total_files": 0,
                "total_size_bytes": 0,
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with LogFetcher(mock_config) as fetcher:
                fetcher.list_recent_files(days=14, limit=50)

            mock_client.get.assert_called_with(
                "/admin/logs/recent",
                params={"days": 14, "limit": 50},
            )

    def test_download_log_file_returns_content(self, mock_config: AppConfig) -> None:
        """Test download_log_file returns file content."""
        with patch("src.services.log_fetcher.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '{"message": "test log entry"}'
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with LogFetcher(mock_config) as fetcher:
                content = fetcher.download_log_file("app-2024-01-15.log")

            mock_client.get.assert_called_with("/admin/logs/files/app-2024-01-15.log")
            assert content == '{"message": "test log entry"}'


class TestFetchLogsForPeriod:
    """Tests for fetch_logs_for_period method."""

    def test_fetches_files_in_date_range(self, mock_config: AppConfig) -> None:
        """Test only files within date range are fetched."""
        from datetime import date

        with patch("src.services.log_fetcher.httpx.Client") as mock_client_class:
            mock_client = MagicMock()

            # Mock list_recent_files response
            list_response = MagicMock()
            list_response.json.return_value = {
                "files": [
                    {
                        "name": "app-2024-01-15.log",
                        "size_bytes": 100,
                        "modified_at": "2024-01-15T12:00:00Z",
                        "created_at": "2024-01-15T10:00:00Z",
                    },
                    {
                        "name": "app-2024-01-14.log",
                        "size_bytes": 100,
                        "modified_at": "2024-01-14T12:00:00Z",
                        "created_at": "2024-01-14T10:00:00Z",
                    },
                    {
                        "name": "app-2024-01-13.log",
                        "size_bytes": 100,
                        "modified_at": "2024-01-13T12:00:00Z",
                        "created_at": "2024-01-13T10:00:00Z",
                    },
                ],
                "total_files": 3,
                "total_size_bytes": 300,
            }

            # Mock download responses
            download_response = MagicMock()
            download_response.text = '{"message": "log"}'

            def get_side_effect(url: str, **_kwargs: Any) -> MagicMock:
                if url == "/admin/logs/recent":
                    return list_response
                return download_response

            mock_client.get.side_effect = get_side_effect
            mock_client_class.return_value = mock_client

            with LogFetcher(mock_config) as fetcher:
                content = fetcher.fetch_logs_for_period(
                    start_date=date(2024, 1, 14),
                    end_date=date(2024, 1, 15),
                )

            # Should download 2 files (14th and 15th)
            download_calls = [
                c for c in mock_client.get.call_args_list if "/admin/logs/files/" in c[0][0]
            ]
            assert len(download_calls) == 2
            assert '{"message": "log"}' in content
