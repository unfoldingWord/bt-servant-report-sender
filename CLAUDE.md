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

## Git Commit Guidelines

- **Author**: Use "Claude" as the commit author
- **Commit messages are mandatory**: Never commit without a quality commit description. Every commit must have a clear, meaningful message that explains:
  - What changed
  - Why it changed
  - Any relevant context for reviewers
