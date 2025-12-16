"""CLI entry point for bt-servant-report-sender."""

import argparse
import sys
from datetime import UTC, date, datetime

from src.models.config import AppConfig, ReportPeriod
from src.services.report_generator import ReportGenerator


def parse_date(value: str) -> date:
    """Parse date string in YYYY-MM-DD format.

    Args:
        value: Date string.

    Returns:
        Parsed date object.

    Raises:
        argparse.ArgumentTypeError: If date format is invalid.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC).date()
    except ValueError as err:
        msg = f"Invalid date format: {value}. Expected YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg) from err


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="bt-servant-report",
        description="Generate and send BT Servant usage reports.",
    )

    parser.add_argument(
        "--period",
        type=str,
        choices=["daily", "weekly", "monthly", "custom"],
        default=None,
        help="Report period (default: from config or daily)",
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=None,
        help="Start date for custom period (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=None,
        help="End date for custom period (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Override API base URL",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="PDF output directory",
    )

    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email",
    )

    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip PDF generation (for testing without WeasyPrint)",
    )

    parser.add_argument(
        "--email-to",
        type=str,
        nargs="+",
        default=None,
        help="Override email recipients",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser


def build_config_overrides(args: argparse.Namespace) -> dict:
    """Build configuration overrides from CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Dictionary of configuration overrides.
    """
    overrides: dict = {}

    if args.period:
        overrides["report_period"] = ReportPeriod(args.period)

    if args.api_url:
        overrides["bt_servant_api_url"] = args.api_url

    if args.output_dir:
        overrides["report_output_dir"] = args.output_dir

    if args.email_to:
        overrides["email_to"] = args.email_to

    return overrides


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI.

    Args:
        argv: Command line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.period == "custom" and (args.start_date is None or args.end_date is None):
        parser.error("--start-date and --end-date required for custom period")

    try:
        overrides = build_config_overrides(args)
        config = AppConfig(**overrides)

        if args.verbose:
            print(f"API URL: {config.bt_servant_api_url}")
            print(f"Report period: {config.report_period.value}")
            print(f"Output directory: {config.report_output_dir}")

        generator = ReportGenerator(config)

        if args.skip_pdf:
            # Test mode: just fetch and process logs
            start_date, end_date = generator.resolve_dates(args.start_date, args.end_date)
            print(f"Date range: {start_date} to {end_date}")
            print("Fetching logs...")
            log_content = generator.fetch_logs(start_date, end_date)
            print(f"Fetched {len(log_content)} bytes of log data")
            print("Processing logs...")
            report_data = generator.process_logs(log_content, start_date, end_date)
            print(f"Processed {report_data.executive_summary.total_interactions} interactions")
            print(f"Total cost: ${report_data.executive_summary.total_cost_usd:.4f}")
            print("Test complete (PDF generation skipped)")
            return 0

        pdf_path = generator.generate_and_send(
            start_date=args.start_date,
            end_date=args.end_date,
            send_email=not args.no_email,
        )

        print(f"Report generated: {pdf_path}")
        if not args.no_email:
            print(f"Email sent to: {', '.join(config.email_to)}")

        return 0

    except (ValueError, OSError, RuntimeError) as err:
        print(f"Error: {err}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
