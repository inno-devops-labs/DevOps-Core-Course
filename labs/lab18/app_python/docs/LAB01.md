# Lab 01 — DevOps Info Service

This document tracks decisions, implementation details, and evidence for Lab 01.

## Task Log
- Task 1.1: Project structure — completed
- Task 1.2: Framework selection — completed (FastAPI chosen)
- Task 1.3: Main endpoint — completed
- Task 1.4: Health check — completed
- Task 1.5: Configuration — completed

## Framework Decision (Task 1.2)
- **Choice:** FastAPI 0.115.x
- **Rationale:** Modern async-first framework with automatic docs and strong typing support; quick to build JSON APIs with minimal boilerplate while still enabling production patterns. Django is heavier than needed for this lightweight info service, and Flask lacks built-in schema/docs conveniences FastAPI provides.

## Implementation Notes
- `app.py` (FastAPI) exposes `GET /` with service/system/runtime/request info and `GET /health` for probes.
- Uptime is calculated from application start, with both seconds and human-readable format.
- Configuration via env vars: `HOST` (default `0.0.0.0`), `PORT` (default `5000`), `DEBUG` (default `False`).

## Notes
Add screenshots to `docs/screenshots/` as tasks are validated.
