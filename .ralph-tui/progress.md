# Gainpath Ralph Progress

## Mission
- Build Gainpath into a production-grade training app with stronger UX, safer backend behavior, clearer architecture, and better AI reliability.
- Prefer concrete improvements to the existing app over generic audits.
- For review tasks, leave behind a written artifact with prioritized findings and explicit follow-up actions.

## Codebase Patterns
- Frontend is a Next.js 15 app under `frontend/` with App Router pages in `frontend/app` and most product UI in `frontend/components`.
- The root route redirects to `/today`; the real daily user experience starts in `frontend/components/today/TodayView.tsx`.
- Frontend data access is centralized in `frontend/lib/api.ts`, which currently uses HTTP Basic auth via a password stored in `localStorage`.
- Backend is a FastAPI app under `backend/app` with routers in `backend/app/routers`, models in `backend/app/models`, and domain logic in `backend/app/services`.
- Backend route protection is applied centrally in `backend/app/main.py` via `Depends(verify_password)` on each router registration.
- Configuration defaults in `backend/app/config.py` are permissive and should be treated as a security-sensitive area.
- AI traffic flows through `backend/app/services/ai_client.py` and coaching logic in `backend/app/services/coaching_engine.py`.
- Session completion side effects are triggered from `backend/app/routers/sessions.py` and include PR detection, streak updates, XP grants, achievements, and post-workout coaching.
- Background tasks **must** create their own `SessionLocal()` DB session — the request-scoped `Depends(get_db)` session is closed after the response, before `BackgroundTasks` run.
- Local development uses `docker-compose.yml` with Postgres, backend on `:8000`, and frontend on `:3000`.

- `backend/app/config.py` **now validates** `app_password` and `secret_key` at startup — refuses to boot with defaults in production (`APP_ENV != "development"`).
- `frontend/lib/api.ts` clears stored password on 401 and exports `clearPassword()` for future logout flows.
- The frontend proxy (`frontend/app/api/proxy/[...path]/route.ts`) strips `WWW-Authenticate` from backend responses, preventing browser-native Basic auth prompts that could leak credential structure.
- **`tenacity` `reraise` default**: `tenacity`'s default `reraise=False` silently swallows the last exception after retries are exhausted. Always use `reraise=True` when you need callers to see the real failure cause.
- **No input validation at ORM boundary**: Several endpoints spread `payload.model_dump(exclude_unset=True)` directly into `setattr()` loops without field-level validation. Offline sync's `_apply_action` spreads arbitrary payload keys into ORM models. Pydantic schemas need explicit constraints and allowed-field allowlists.
- **Background task failures are silent**: The session completion pipeline logs exceptions but has no retry or user-facing feedback. A `/sessions/{id}/reprocess` endpoint would allow re-running the pipeline for failed sessions.
- **httpx client per-request**: `AIClient._http_post` creates a new `httpx.AsyncClient` per call, discarding it after one request. Connection reuse would reduce latency for frequent AI calls.

## High-Value Hot Paths
- `frontend/components/today/TodayView.tsx`
- `frontend/components/today/ActiveWorkout.tsx`
- `frontend/components/today/QuickLogSheet.tsx`
- `frontend/lib/api.ts`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/routers/sessions.py`
- `backend/app/routers/coaching.py`
- `backend/app/services/ai_client.py`
- `backend/app/services/coaching_engine.py`

## Working Rules
- Prefer shipping one useful change per story rather than broad, shallow edits.
- For UI stories, preserve the existing visual language unless you intentionally improve it across the touched surface.
- For security stories, prioritize removing insecure defaults, tightening validation, and making failure modes explicit.
- For architecture review stories, create a concise report under `.ralph-tui/reviews/` with severity-ranked findings and practical next actions.
- For implementation stories, run the smallest relevant verification available and record what was checked.

## Output Expectations
- If a task is review-heavy, leave a markdown artifact in `.ralph-tui/reviews/`.
- If a task changes behavior, update code and note the affected user flow in the completion entry.
- If a task uncovers a reusable pattern or hidden risk, add it to `## Codebase Patterns`.

---

## 2026-04-18 - US-005
- Created a comprehensive architecture review covering frontend boundaries, backend layering, data flow, auth boundaries, and deployment assumptions. Identified 16 severity-ranked findings (4 High, 7 Medium, 5 Low) with specific file references, data flow diagrams, and a prioritized recommendation matrix. Top findings: localStorage XSS exposure (H-1), missing input validation at ORM boundary (H-2), silent background task failures (H-3), and no migration safety in deployment (H-4).
- Files changed: `.ralph-tui/reviews/US-005.md`
- Verification: Traced all hot paths end-to-end (Today flow, session completion pipeline, AI coaching, plan generation, offline sync); reviewed all backend routers, services, models, and frontend components; cross-referenced with prior US-001 and US-002 findings for consistency
- Learnings: The `GET /sessions/today` endpoint has a side effect (auto-creating session stubs from planned sessions), violating idempotency. The coaching chat endpoint stores the user message before generating the AI response, creating orphan rows on failure. `httpx.AsyncClient` is created per-request when it should be reused. `datetime.utcnow()` is deprecated in Python 3.12+ and appears in 6+ files.
---

## 2026-04-18 - US-001
- Hardened backend config to refuse startup with default `app_password` in production; added startup warnings for insecure `secret_key` and `app_password` defaults. Frontend now clears `localStorage` password on 401, exports `clearPassword()`, and documents the localStorage XSS trade-off. Added `APP_ENV` to `.env.example` and `docker-compose.yml`. Created full severity-ranked review.
- Files changed: `backend/app/config.py`, `backend/app/main.py`, `frontend/lib/api.ts`, `.env.example`, `docker-compose.yml`, `.ralph-tui/reviews/US-001.md`
- Verification: loaded `Settings()` with real `.env` (passes); set `APP_ENV=production` + `APP_PASSWORD=changeme` (correctly raises `ValidationError`); confirmed `.env` is gitignored; reviewed proxy header handling
- Learnings: The biggest remaining risk is localStorage password exposure to XSS (C-1). Migrating to HttpOnly cookie + login endpoint is the single most impactful next hardening step. The `APP_ENV` pattern (dev allows defaults, prod blocks them) is reusable for any self-hosted app with permissive local-developer ergonomics.
---

## 2026-04-18 - US-002
- Stabilized session completion pipeline: fixed three bugs in the background task that fires when a session is marked completed. (1) The background task now creates its own DB session instead of receiving the request-scoped session, which would be closed before the task runs. (2) Each completion step (PR detection, streak, XP, achievements, coaching) is now isolated in its own try/except so one failure doesn't block the rest. (3) `completed_at` is now auto-set to `datetime.utcnow()` when transitioning to "completed" status, ensuring the early_bird achievement and coaching prompts have a timestamp.
- Files changed: `backend/app/routers/sessions.py`, `.ralph-tui/reviews/US-002.md`
- Verification: syntax check passes; reviewed full pipeline end-to-end (sessions.py → pr_detector.py → streak_engine.py → achievement_engine.py → coaching_engine.py → ai_client.py); confirmed background task DB lifecycle matches scheduler pattern in `main.py`
- Learnings: FastAPI's `BackgroundTasks` run after the response, so any dependency-injected DB session is already closed. The pattern in `main.py`'s scheduler (`SessionLocal()` with `try/finally: db.close()`) is the correct one to follow for any async background work. A concurrent double-completion race exists but is low risk for a single-user app; a `SELECT FOR UPDATE` guard would be the production fix.
---

## 2026-04-18 - US-003
- Improved Today flow for mobile-first usability with three material UX changes. (1) Added "Next up" section heading above pending sessions so users immediately see what to act on without scanning. (2) Collapsed completed/skipped sessions into a compact "Done" section with a minimal `DoneCard` (single-line row) instead of full-height cards, reducing scroll and keeping actionable sessions above the fold. (3) Added a skip confirmation dialog that intercepts the previously one-tap destructive skip action, with a destructive-styled confirm button and neutral cancel.
- Files changed: `frontend/components/today/TodayView.tsx`
- Verification: TypeScript compilation passes (no new errors from changes); confirmed TodayView is only consumed by `frontend/app/today/page.tsx`; all session actions (Start, Log, Skip) remain functional; section headings and DoneCard use existing design tokens and responsive patterns; skip confirmation uses `bg-destructive` which is a standard shadcn semantic token
- Learnings: The "Next up" / "Done" split pattern is a mobile-first convention that reduces cognitive load when the user has multiple sessions. The skip confirmation pattern (state-driven modal with destructive confirm) should be reused for any irreversible action in the app. Collapsing finished items is especially impactful on small screens where vertical space is scarce.
---

## 2026-04-18 - US-004
- Hardened AI client fallback behavior with seven fixes. (1) Fixed `reraise=False` on tenacity decorator that swallowed retryable network errors — changed to `reraise=True` and added explicit `except _RETRYABLE: raise`. (2) Added tenacity retry to `generate_text()` path (coaching chat) which previously had no retry, only fallback. (3) Added `AIEmptyResponseError` guard for empty/whitespace model responses. (4) Added `strip_json_fences()` to handle models returning markdown-fenced JSON. (5) Fixed `generate_text()` usage logging to capture real token counts and request IDs. (6) Fixed coaching background tasks that passed request-scoped DB sessions to `BackgroundTasks` — each task now creates its own `SessionLocal()`. (7) Added exception isolation to scheduler jobs so failures don't crash the scheduler thread.
- Files changed: `backend/app/services/ai_client.py`, `backend/app/routers/coaching.py`, `backend/app/main.py`
- Verification: Python syntax check passes for all three files; traced complete request lifecycle for both `generate()` and `generate_text()` paths confirming retry → fallback → usage-log for success and failure; confirmed background task DB lifecycle matches `SessionLocal()` pattern; confirmed `strip_json_fences` handles fenced and bare JSON inputs
- Learnings: The `tenacity` `reraise=False` default is dangerous — it silently swallows the last exception after retries are exhausted instead of re-raising it, making transient network errors invisible. For background tasks in FastAPI, any function scheduled via `BackgroundTasks.add_task()` must create its own DB session because the request-scoped `Depends(get_db)` session is closed before the task runs. The `ai_max_retries` config setting exists but was not referenced by the tenacity decorator (hardcoded `3`); now uses `settings.ai_max_retries`.
---
