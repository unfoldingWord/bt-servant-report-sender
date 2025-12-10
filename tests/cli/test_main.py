"""Tests for CLI entry point."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.main import build_config_overrides, create_parser, main, parse_date
from src.models.config import ReportPeriod


class TestParseDate:
    """Tests for date parsing."""

    def test_parses_valid_date(self) -> None:
        """Test parsing valid date string."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_raises_on_invalid_format(self) -> None:
        """Test invalid date format raises error."""
        with pytest.raises(Exception, match="Invalid date format"):
            parse_date("01-15-2024")

    def test_raises_on_invalid_date(self) -> None:
        """Test invalid date raises error."""
        with pytest.raises(Exception, match="Invalid date format"):
            parse_date("2024-13-45")


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_parser_has_period_option(self) -> None:
        """Test parser includes period option."""
        parser = create_parser()
        args = parser.parse_args(["--period", "weekly"])
        assert args.period == "weekly"

    def test_parser_has_date_options(self) -> None:
        """Test parser includes date options."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-31",
            ]
        )
        assert args.start_date == date(2024, 1, 1)
        assert args.end_date == date(2024, 1, 31)

    def test_parser_has_api_url_option(self) -> None:
        """Test parser includes API URL option."""
        parser = create_parser()
        args = parser.parse_args(["--api-url", "https://custom.api.com"])
        assert args.api_url == "https://custom.api.com"

    def test_parser_has_output_dir_option(self) -> None:
        """Test parser includes output directory option."""
        parser = create_parser()
        args = parser.parse_args(["--output-dir", "/custom/path"])
        assert args.output_dir == "/custom/path"

    def test_parser_has_no_email_flag(self) -> None:
        """Test parser includes no-email flag."""
        parser = create_parser()
        args = parser.parse_args(["--no-email"])
        assert args.no_email is True

    def test_parser_has_email_to_option(self) -> None:
        """Test parser includes email-to option."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--email-to",
                "user1@test.com",
                "user2@test.com",
            ]
        )
        assert args.email_to == ["user1@test.com", "user2@test.com"]

    def test_parser_has_verbose_flag(self) -> None:
        """Test parser includes verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose is True

    def test_default_values(self) -> None:
        """Test parser default values."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.period is None
        assert args.start_date is None
        assert args.end_date is None
        assert args.no_email is False
        assert args.verbose is False


class TestBuildConfigOverrides:
    """Tests for config override building."""

    def test_builds_period_override(self) -> None:
        """Test period override is built correctly."""
        parser = create_parser()
        args = parser.parse_args(["--period", "weekly"])
        overrides = build_config_overrides(args)
        assert overrides["report_period"] == ReportPeriod.WEEKLY

    def test_builds_api_url_override(self) -> None:
        """Test API URL override is built correctly."""
        parser = create_parser()
        args = parser.parse_args(["--api-url", "https://custom.api.com"])
        overrides = build_config_overrides(args)
        assert overrides["bt_servant_api_url"] == "https://custom.api.com"

    def test_builds_output_dir_override(self) -> None:
        """Test output directory override is built correctly."""
        parser = create_parser()
        args = parser.parse_args(["--output-dir", "/custom/path"])
        overrides = build_config_overrides(args)
        assert overrides["report_output_dir"] == "/custom/path"

    def test_builds_email_to_override(self) -> None:
        """Test email-to override is built correctly."""
        parser = create_parser()
        args = parser.parse_args(["--email-to", "user@test.com"])
        overrides = build_config_overrides(args)
        assert overrides["email_to"] == ["user@test.com"]

    def test_empty_overrides_for_defaults(self) -> None:
        """Test no overrides for default values."""
        parser = create_parser()
        args = parser.parse_args([])
        overrides = build_config_overrides(args)
        assert not overrides


class TestMain:
    """Tests for main function."""

    def test_successful_execution_returns_zero(self, tmp_path: Path) -> None:
        """Test successful execution returns exit code 0."""
        with (
            patch("src.cli.main.AppConfig") as mock_config_class,
            patch("src.cli.main.ReportGenerator") as mock_generator_class,
        ):
            mock_config = MagicMock()
            mock_config.bt_servant_api_url = "https://api.test.com"
            mock_config.report_period.value = "daily"
            mock_config.report_output_dir = tmp_path
            mock_config.email_to = ["user@test.com"]
            mock_config_class.return_value = mock_config

            mock_generator = MagicMock()
            mock_generator.generate_and_send.return_value = tmp_path / "report.pdf"
            mock_generator_class.return_value = mock_generator

            result = main([])

            assert result == 0

    def test_error_returns_nonzero(self) -> None:
        """Test error returns non-zero exit code."""
        with patch("src.cli.main.AppConfig") as mock_config_class:
            mock_config_class.side_effect = ValueError("Config error")

            result = main([])

            assert result == 1

    def test_no_email_flag_skips_email(self, tmp_path: Path) -> None:
        """Test --no-email flag skips email sending."""
        with (
            patch("src.cli.main.AppConfig") as mock_config_class,
            patch("src.cli.main.ReportGenerator") as mock_generator_class,
        ):
            mock_config = MagicMock()
            mock_config.bt_servant_api_url = "https://api.test.com"
            mock_config.report_period.value = "daily"
            mock_config.report_output_dir = tmp_path
            mock_config_class.return_value = mock_config

            mock_generator = MagicMock()
            mock_generator.generate_and_send.return_value = tmp_path / "report.pdf"
            mock_generator_class.return_value = mock_generator

            main(["--no-email"])

            mock_generator.generate_and_send.assert_called_once()
            call_kwargs = mock_generator.generate_and_send.call_args[1]
            assert call_kwargs["send_email"] is False

    def test_custom_period_requires_dates(self) -> None:
        """Test custom period requires start and end dates."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--period", "custom"])
        assert exc_info.value.code == 2

    def test_verbose_prints_config(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test verbose flag prints configuration info."""
        with (
            patch("src.cli.main.AppConfig") as mock_config_class,
            patch("src.cli.main.ReportGenerator") as mock_generator_class,
        ):
            mock_config = MagicMock()
            mock_config.bt_servant_api_url = "https://api.test.com"
            mock_config.report_period.value = "daily"
            mock_config.report_output_dir = tmp_path
            mock_config.email_to = ["user@test.com"]
            mock_config_class.return_value = mock_config

            mock_generator = MagicMock()
            mock_generator.generate_and_send.return_value = tmp_path / "report.pdf"
            mock_generator_class.return_value = mock_generator

            main(["-v"])

            captured = capsys.readouterr()
            assert "API URL:" in captured.out
            assert "Report period:" in captured.out
