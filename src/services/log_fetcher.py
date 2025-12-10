"""Log fetcher service for bt-servant-engine API."""

from datetime import date
from types import TracebackType

import httpx

from src.models.config import AppConfig
from src.models.log_entry import LogFilesPayload


class LogFetcher:
    """Client for fetching logs from bt-servant-engine API."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the log fetcher.

        Args:
            config: Application configuration with API URL and token.
        """
        self._config = config
        self._client: httpx.Client | None = None

    def __enter__(self) -> "LogFetcher":
        """Enter context manager, creating HTTP client."""
        self._client = httpx.Client(
            base_url=self._config.bt_servant_api_url,
            headers=self._build_auth_headers(),
            timeout=60.0,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager, closing HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers for API requests.

        Returns:
            Dictionary with Authorization header.
        """
        token = self._config.bt_servant_api_token.get_secret_value()
        return {"Authorization": f"Bearer {token}"}

    def _ensure_client(self) -> httpx.Client:
        """Ensure HTTP client is initialized.

        Returns:
            The HTTP client.

        Raises:
            RuntimeError: If used outside context manager.
        """
        if self._client is None:
            msg = "LogFetcher must be used as context manager"
            raise RuntimeError(msg)
        return self._client

    def list_log_files(self) -> LogFilesPayload:
        """List all available log files.

        Returns:
            LogFilesPayload with file metadata.

        Raises:
            httpx.HTTPStatusError: If API returns error status.
        """
        client = self._ensure_client()
        response = client.get("/admin/logs/files")
        response.raise_for_status()
        return LogFilesPayload.model_validate(response.json())

    def list_recent_files(self, days: int = 7, limit: int = 100) -> LogFilesPayload:
        """List recent log files.

        Args:
            days: Number of days to look back (1-90).
            limit: Maximum number of files to return (1-500).

        Returns:
            LogFilesPayload with file metadata.

        Raises:
            httpx.HTTPStatusError: If API returns error status.
        """
        client = self._ensure_client()
        response = client.get(
            "/admin/logs/recent",
            params={"days": days, "limit": limit},
        )
        response.raise_for_status()
        return LogFilesPayload.model_validate(response.json())

    def download_log_file(self, filename: str) -> str:
        """Download a specific log file.

        Args:
            filename: Name of the log file to download.

        Returns:
            Content of the log file as string.

        Raises:
            httpx.HTTPStatusError: If API returns error status.
        """
        client = self._ensure_client()
        response = client.get(f"/admin/logs/files/{filename}")
        response.raise_for_status()
        return response.text

    def fetch_logs_for_period(self, start_date: date, end_date: date) -> str:
        """Fetch and concatenate all log files for the given date range.

        Args:
            start_date: Start date of the period.
            end_date: End date of the period.

        Returns:
            Concatenated content of all relevant log files.
        """
        days = (end_date - start_date).days + 1
        files_payload = self.list_recent_files(days=min(days, 90), limit=500)

        all_content: list[str] = []
        for file_entry in files_payload.files:
            file_date = file_entry.modified_at.date()
            if start_date <= file_date <= end_date:
                content = self.download_log_file(file_entry.name)
                all_content.append(content)

        return "\n".join(all_content)
