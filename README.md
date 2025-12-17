# bt-servant-report-sender

Utility to generate and email usage reports for the bt-servant-engine chatbot. It pulls log files from the bt-servant API, aggregates metrics (costs, performance, usage, system health), renders a PDF via WeasyPrint, and can send the report via SMTP.

## Features
- Fetches logs from bt-servant-engine admin API.
- Aggregates performance, cost, intent, language, and system health metrics.
- Renders a PDF report (Jinja2 + WeasyPrint).
- Sends the PDF via email.
- CLI flags to control period, dates, recipients, output path, and whether to skip PDF/email.
- GitHub Actions workflow for weekly scheduled runs (see `.github/workflows/weekly-report.yml`).

## Prerequisites
- Python 3.13+ (repo targets 3.12+; CI uses 3.13).
- WeasyPrint system deps if running locally (on macOS: `brew install pango gdk-pixbuf libffi gobject-introspection`).
- Access to bt-servant admin API and SMTP credentials.

## Installation
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration
Set env vars or a `.env` file. Expected keys (see `.env.template` in repo if present):
- `BT_SERVANT_API_URL`
- `BT_SERVANT_API_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO` (comma-separated list)
- Optional: `REPORT_OUTPUT_DIR`

## CLI Usage
Run via module:
```bash
python -m src.cli.main --period weekly --verbose
```
Common flags:
- `--period {daily,weekly,monthly,custom}`
- `--start-date YYYY-MM-DD` / `--end-date YYYY-MM-DD` (required for custom)
- `--no-email` (skip sending)
- `--skip-pdf` (process logs without generating PDF)
- `--email-to addr1 addr2` (override recipients)
- `--output-dir PATH`
- `--api-url URL`
- `-v/--verbose`

Examples:
```bash
# Weekly report for yesterday-6..yesterday
python -m src.cli.main --period weekly --verbose

# Custom window, no email, save PDF to /tmp/reports
python -m src.cli.main --period custom --start-date 2025-12-01 --end-date 2025-12-07 --no-email --output-dir /tmp/reports

# Test log processing only (no PDF)
python -m src.cli.main --period weekly --skip-pdf --verbose
```

## How metrics are derived
- **Total interactions**: count of `PerfReport` log entries in the date window.
- **Costs**: sum of per-report token costs (input/output; cached/audio currently hidden in the table).
- **Usage / unique users**: distinct `user` fields in log entries (excluding `"-"`), filtered by date.
- **Languages / intents**: parsed from log messages (`language code ... detected`, `extracted user intents: ...`).
- **System health**: counts of WARNING/ERROR log levels; success rate = `(total log entries - errors) / total log entries * 100`, shown to two decimals; recent warnings/errors list unique messages.

## Scheduled runs (GitHub Actions)
Workflow at `.github/workflows/weekly-report.yml` runs every Monday 03:00 UTC (and supports manual dispatch). Set repo secrets:
- `BT_SERVANT_API_URL`
- `BT_SERVANT_API_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`

It installs deps, runs the weekly report, and uploads the PDF artifact.

## Development
- Run pre-commit hooks: `pre-commit run --all-files`
- Tests: `pytest`
- Lint/type: `ruff check .`, `ruff format --check .`, `pylint src tests`, `mypy src`, `bandit -r src`

## Example logs
See `docs/example-bt-servant-log.txt` for sample log lines consumed by the parser.
