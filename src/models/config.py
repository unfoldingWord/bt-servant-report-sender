"""Application configuration model."""

from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReportPeriod(str, Enum):
    """Report period options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    bt_servant_api_url: str = Field(description="bt-servant-engine API base URL")
    bt_servant_api_token: SecretStr = Field(description="Admin API token")

    # Report Period
    report_period: ReportPeriod = Field(default=ReportPeriod.DAILY)
    report_start_date: date | None = Field(default=None)
    report_end_date: date | None = Field(default=None)

    # SMTP Configuration
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(description="SMTP username")
    smtp_password: SecretStr = Field(description="SMTP password")
    email_from: EmailStr = Field(description="Sender email address")
    email_to: list[EmailStr] = Field(description="Recipient email addresses")

    # Output
    report_output_dir: Path = Field(default=Path("./reports"))
