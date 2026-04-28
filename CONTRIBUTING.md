# Contributing to CRSS

Welcome — this guide keeps our 5-person team's git history clean and our PRs reviewable. Read it once before your first push.

---

## Branching — trunk-based

We work directly off `main` with **short-lived feature branches**. No `develop`, no `release/*`, no long-lived integration branches.

- Branch from latest `main`
- Keep branches small (1–3 days max). If a feature is bigger, split it.
- Branch names: `<type>/<short-slug>`
  - `feat/registration-seat-lock`
  - `fix/timetable-overlap-edge-case`
  - `docs/architecture-diagram`
  - `chore/update-ruff`
  - `refactor/repository-base-class`
  - `test/registration-concurrency`
  - `ci/cache-uv-deps`

```bash
git checkout main
git pull
git checkout -b feat/<your-slug>
```

---

## Commits — Conventional Commits

Every commit message follows:

```
<type>(<scope>): <subject>

<optional body — wrap at 72 chars>
```

**Types** (limited set):

| Type | Use for |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Tooling, deps, config (no app behavior change) |
| `refactor` | Code restructure without behavior change |
| `test` | Adding/fixing tests |
| `ci` | CI / build pipeline changes |
| `perf` | Performance improvement |

**Scope** = the module touched (`auth`, `registration`, `waitlist`, `timetable`, `db`, `api`, `worker`, `infra`, etc.).

Examples:

```
feat(registration): add SELECT FOR UPDATE seat lock
fix(timetable): treat midnight-crossing slots as conflicts
docs(architecture): add Mermaid request-flow diagram
chore(deps): bump fastapi 0.136 -> 0.137
test(registration): add 50-concurrent-request capacity test
```

**Subject rules:** imperative mood ("add", not "added"), no period, lowercase first letter, ≤72 chars.

---

## Pull requests

1. Push your branch and open a PR against `main`.
2. The PR template auto-fills — complete every section.
3. **Require ≥1 approval** from a teammate before merging.
4. **CI must pass** (ruff lint, ruff format check, pytest).
5. **Squash-merge only.** The squash commit message must itself be a valid Conventional Commit (GitHub uses your PR title — make it match the format above).
6. Delete the branch after merge.

### Before pushing — local checks

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Or let pre-commit do it automatically:

```bash
# one-time
uv tool install pre-commit
pre-commit install

# on every commit, hooks now run automatically
```

---

## Code review expectations

As a reviewer:
- Read the PR description first — does it match the diff?
- Block on correctness, security, race conditions, and test coverage gaps.
- Comment on style only if it's not catchable by ruff.
- Approve when you'd be comfortable maintaining the code yourself.

As an author:
- Respond to every comment (resolve, push fix, or argue with reason).
- Don't force-push after review starts; add fixup commits, then squash on merge.
- Re-request review after addressing comments.

---

## Module ownership

| Module | Primary owner |
|---|---|
| `modules/registration`, `modules/waitlist` | TBD |
| `modules/auth`, `modules/students` | TBD |
| `modules/courses`, `modules/sections`, `modules/timetable` | TBD |
| `worker/`, `modules/audit`, observability | TBD |
| `frontend/`, API docs, report screenshots | TBD |

(Fill in once the team confirms assignments — see spec §24.)

Anyone can submit PRs to any module; the owner is the default reviewer.

---

## When in doubt

- Read the spec (`docs/CRSS_Technical_Specification.md`).
- Ask in the team chat before doing something architecturally big.
- Open a draft PR early to get feedback on direction.
