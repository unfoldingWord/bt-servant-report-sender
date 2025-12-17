# AGENTS.md

Guidance for the Codex agent when working in this repository.

## Project Overview

bt-servant-report-sender generates and sends usage reports for the bt-servant-engine chatbot, which processes WhatsApp/Meta messages using OpenAI APIs for intent detection, language processing, and responses.

## Git Conventions (Codex)

- **Author flag is mandatory for every commit.** Always commit with `--author="Codex <noreply@anthropic.com>"`.
- **Commit messages must be meaningful.** Summarize what changed and why; no empty or generic titles.
- **Run pre-commit before committing.** `git add -A && pre-commit run --all-files` must pass. Do not skip with `--no-verify`; fix issues instead.

## Development Commands

```bash
pip install -r requirements.txt           # install deps
pre-commit install                       # install hooks
pre-commit run --all-files               # run hooks manually
ruff check .
ruff format --check .
pylint src tests
mypy src
PYTHONIOENCODING=utf-8 lint-imports
bandit -r src -c pyproject.toml
pytest
pytest --cov=src --cov-report=term-missing
```

## Code Quality Rules

- Functions should stay within 50 statements; refactor when longer.
- Respect layered imports: CLI → Services → Parsers → Models. Do not import outward.
- Keep full type hints; avoid `Any` and suppression comments (`noqa`, `type: ignore`, etc.).
- Fix security findings; do not bypass Bandit or other linters.
- Zero-warning policy for Ruff and Pylint; adjust code, not configs.

## Architecture Overview

```
src/
├── cli/                 # Command-line interface
├── services/            # Business logic
├── parsers/             # Log parsing and extraction
└── models/              # Data models and schemas

tests/                   # Mirrors src/ structure
docs/                    # Documentation and examples
```
