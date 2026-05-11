# Changelog

All notable changes to CRSP are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Registration/waitlist hardening: direct waitlist APIs, FIFO auto-promotion on drop, skipped ineligible waitlist entries, JWT or `X-Student-Id` student identity, and repeatable registration demo seed data.
- Komil registration slice: SQLAlchemy/Alembic schema foundation, `/api/v1/registrations` APIs, eligibility preview, idempotency, waitlist, audit/event records, and focused tests.
- Integrated auth slice with JWT login routes, shared ORM models, mock INS login, and API tests.
- Initial project baseline: monorepo skeleton, `uv`-managed backend, ruff + pre-commit + GitHub Actions CI, README, CONTRIBUTING, `.env.example`.
- MIT license (© 2026 Celion).

### Changed
- Project acronym standardized to **CRSP** (Course Registration and Scheduling Platform). Team name is **Celion**.
