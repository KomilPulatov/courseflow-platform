# Changelog

All notable changes to CRSP are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Student frontend (`frontend-student/`): React 18 + TypeScript + Vite + Tailwind CSS app covering all student routes — catalog browsing, section detail with live seat count (WebSocket), registration with idempotency, drop, waitlist, timetable grid, profile, and notifications.
- `POST /auth/student/manual-login`: email + password login for returning manual-profile students.
- CORS middleware on the backend allowing `localhost:5173` in local dev.
- `CLAUDE.md`: codebase guidance for Claude Code covering commands, architecture, and key business rules.
- Komil registration slice: SQLAlchemy/Alembic schema foundation, `/api/v1/registrations` APIs, eligibility preview, idempotency, waitlist, audit/event records, and focused tests.
- Integrated auth slice with JWT login routes, shared ORM models, mock INS login, and API tests.
- Initial project baseline: monorepo skeleton, `uv`-managed backend, ruff + pre-commit + GitHub Actions CI, README, CONTRIBUTING, `.env.example`.
- MIT license (© 2026 Celion).

### Changed
- Project acronym standardized to **CRSP** (Course Registration and Scheduling Platform). Team name is **Celion**.
