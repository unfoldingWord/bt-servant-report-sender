"""Application configuration model."""

import json
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings
from pydantic_settings.sources import (
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class ReportPeriod(str, Enum):
    """Report period options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config: ClassVar[Any] = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

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

    @field_validator("email_to", mode="before")
    @classmethod
    def _parse_email_to(cls, value: object) -> object:
        """Allow comma- or semicolon-delimited strings for email_to."""
        if isinstance(value, str):
            return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return value

    @classmethod
    # pylint: disable=too-many-positional-arguments
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Use lenient env sources that don't force JSON parsing on complex fields."""
        _ = env_settings

        class LenientEnvSettingsSource(EnvSettingsSource):
            def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:
                try:
                    return super().decode_complex_value(field_name, field, value)
                except json.JSONDecodeError:
                    return value

        class LenientDotEnvSettingsSource(DotEnvSettingsSource):
            def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:
                try:
                    return super().decode_complex_value(field_name, field, value)
                except json.JSONDecodeError:
                    return value

        return (
            init_settings,
            LenientEnvSettingsSource(settings_cls),
            LenientDotEnvSettingsSource(settings_cls, getattr(dotenv_settings, "env_file", None)),
            file_secret_settings,
        )
