PR: auth-cookie-migrations

Summary
- Make refresh token cookie-only (httpOnly) and rotate refresh tokens on `/token/refresh`.
- Implement DB-backed refresh token persistence with revocation and rotation.
- Add single-refresh-in-flight client guard in teacher & student frontends.
- Make refresh cookie security attributes configurable via `PRODUCTION` or `COOKIE_SECURE` env vars.
- Add migration helper `scripts/migrate.py` and Alembic scaffold under `alembic/`.
- Add `scripts/run_all_tests.py` to run Option A–D smoke tests sequentially.

Files changed (high level)
- backend/app/auth.py (refresh token model, create/verify/revoke logic)
- backend/app/main.py (cookie-only refresh + cookie attribute hardening)
- frontend/*_dashboard/app.js (single-refresh-in-flight; cookie-based refresh)
- scripts/* (migrate, test runner, updated test_optionD_client.py)
- alembic/* (scaffold)

How to test locally
1. Ensure Python dependencies available (FastAPI, SQLModel, jwt, alembic optional).
2. Initialize DB schema (safe):

```bash
python scripts/migrate.py
```

3. Run tests:

```bash
python scripts/run_all_tests.py
```

Production notes
- Set `COOKIE_SECURE=1` or `PRODUCTION=1` in the environment to enable `Secure` on cookies over HTTPS.
- For production, prefer `SameSite='Lax'` or `Strict` depending on your cross-site needs and ensure proper CSRF protections.
- Replace localStorage token storage with an in-memory token + silent refresh pattern or use server-side sessions for SPA where feasible.

If you want, I can push this branch to a remote and open a PR (provide remote URL or set `origin`).
