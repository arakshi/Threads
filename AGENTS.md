# AGENTS instructions for this repository

## Development defaults
- Keep primary ingestion mode public-only (no Threads login required).
- Treat official API as optional provider behind feature flag.
- Preserve PyCharm-friendly local run scripts.
- Prefer SQLite defaults; PostgreSQL optional.

## Quality gates
- Add/maintain pytest coverage for parsing, scoring, dedup, clustering.
- Keep modules decoupled through interfaces/adapters for collectors.
- If a field cannot be collected in public mode, store `null` and log reason.
