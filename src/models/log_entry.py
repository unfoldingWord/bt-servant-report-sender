"""Log entry models for bt-servant logs."""

from datetime import datetime

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """A single log entry from bt-servant-engine."""

    message: str
    timestamp: datetime
    level: str
    logger: str
    client_ip: str
    task_name: str | None = Field(default=None, alias="taskName")
    cid: str
    user: str
    schema_version: str


class LogFileEntry(BaseModel):
    """Metadata for a log file from the API."""

    name: str
    size_bytes: int
    modified_at: datetime
    created_at: datetime


class LogFilesPayload(BaseModel):
    """Response from the log files API endpoint."""

    files: list[LogFileEntry]
    total_files: int
    total_size_bytes: int
