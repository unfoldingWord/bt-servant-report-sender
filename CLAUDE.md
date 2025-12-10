# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

bt-servant-report-sender is a utility for sending reports from the bt-servant-engine system. The bt-servant-engine is a chatbot/AI assistant that processes messages via WhatsApp/Meta integration and uses OpenAI APIs for intent detection, language processing, and response generation.

## Log File Format

The example log file (`docs/example-bt-servant-log.txt`) contains JSON-formatted log entries with the following schema:
- `message`: Log content
- `client_ip`: Request source IP
- `taskName`: Async task identifier
- `timestamp`: ISO timestamp
- `level`: Log level (INFO, WARNING, etc.)
- `logger`: Python logger name (e.g., `bt_servant_engine.services.*`)
- `cid`: Correlation ID for request tracing
- `user`: User identifier
- `schema_version`: Log schema version (currently "1.0.0")

Key log events include `PerfReport` entries containing detailed performance metrics, token usage, and cost breakdowns.

## Git Conventions

When making commits, always use the author "Claude" with:
```
git commit --author="Claude <noreply@anthropic.com>"
```

**IMPORTANT:** Never commit with an empty description. All commits must have a meaningful message describing the changes.

### MANDATORY: Pre-commit Checks Before Every Commit

**Claude MUST run pre-commit and verify ALL checks pass before every commit.** This is non-negotiable.

**The single source of truth is pre-commit:**
```bash
git add -A && pre-commit run --all-files
```

**DO NOT proceed with the commit until ALL hooks show "Passed".** If ANY hook fails:
1. READ the error message carefully
2. FIX the code (not the config)
3. Re-run pre-commit
4. Repeat until ALL hooks pass
5. Only THEN commit

**NEVER:**
- Use `--no-verify` to skip hooks
- Modify tool configs to weaken rules
- Add suppression comments (noqa, type: ignore, etc.)
- Proceed if pre-commit shows ANY failures

**Commit workflow for Claude:**
1. Stage changes: `git add -A`
2. Run: `pre-commit run --all-files`
3. If ANY hook fails → FIX THE CODE → go to step 2
4. When ALL hooks pass: `git commit --author="Claude <noreply@anthropic.com>" -m "..."`
5. Verify the commit succeeded (hooks run again during commit)

## Development Commands

```bash
# Install dependencies (including dev)
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run all linters (same as CI)
ruff check .
ruff format --check .
pylint src tests
mypy src
PYTHONIOENCODING=utf-8 lint-imports
bandit -r src -c pyproject.toml

# Auto-fix formatting
ruff format .
ruff check --fix .

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```

## Code Quality Rules - NEVER SUPPRESS OR BYPASS

**CRITICAL: The following rules are non-negotiable. Do not add `# noqa`, `# type: ignore`, `# pylint: disable`, or any other suppression comments. Do not modify tool configurations to weaken these rules. If code violates these rules, fix the code.**

### 1. Function Size Limit: 50 Statements Maximum

Every function must have 50 or fewer statements. No exceptions.

**If a function exceeds 50 statements:**
- Extract helper functions
- Break into smaller logical units
- Refactor the design

**Do NOT:**
- Add `# pylint: disable=too-many-statements`
- Increase the limit in pylintrc
- Argue that "this function is special"

### 2. Layered Architecture - Import Boundaries

The codebase follows strict layered architecture. Imports must flow inward only:

```
CLI → Services → Parsers → Models
```

**Allowed imports:**
- `cli` → `services`, `parsers`, `models`
- `services` → `parsers`, `models` (NOT cli)
- `parsers` → `models` (NOT cli, services)
- `models` → only standard library, other models

**Do NOT:**
- Add `# import-linter: skip`
- Create "exceptions" to the architecture
- Move code to circumvent the rules

### 3. Type Safety - Full Type Hints Required

All functions must have complete type annotations. mypy runs in strict mode (with minor exceptions).

**Do NOT:**
- Add `# type: ignore` comments
- Use `Any` to avoid proper typing
- Leave functions untyped

### 4. Security - No Vulnerabilities

Bandit scans for security issues. All findings must be fixed.

**Do NOT:**
- Add `# nosec` comments
- Disable Bandit rules
- Introduce SQL injection, command injection, or other OWASP vulnerabilities

### 5. Linting - Zero Warnings Policy

Ruff and Pylint must pass with zero warnings. Warnings are treated as errors.

**Do NOT:**
- Add `# noqa` comments
- Disable rules in config
- Ignore warnings "because they're just warnings"

## Architecture Overview

```
src/
├── cli/                 # Command-line interface
├── services/            # Business logic layer
├── parsers/             # Log parsing and data extraction
└── models/              # Data models and schemas

tests/                   # Test files mirror src/ structure
docs/                    # Documentation and example files
```

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit. They will block commits that violate any rules.

To skip hooks in an emergency (STRONGLY discouraged):
```bash
git commit --no-verify
```

**Do not make `--no-verify` a habit. Fix the issues instead.**

## When You Think a Rule Should Be Bypassed

1. **Stop.** The rule exists for a reason.
2. **Refactor.** There is always a way to write compliant code.
3. **If truly stuck**, discuss with the team before ANY suppression.

The goal is clean, maintainable, secure code. These rules support that goal.
