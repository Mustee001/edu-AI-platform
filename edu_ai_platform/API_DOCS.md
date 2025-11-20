# API Documentation

## Authentication Endpoints
- `POST /login` — Login and receive access/refresh tokens (refresh in httpOnly cookie)
- `POST /refresh` — Rotate refresh token, receive new access token
- `POST /logout` — Revoke refresh token and clear cookie

## User Dashboards
- Teacher: `frontend/teacher_dashboard/app.js`
- Student: `frontend/student_dashboard/app.js`

## Migration & Testing
- Alembic migrations: `alembic/`
- Test scripts: `scripts/test_optionA_client.py` ... `test_optionD_client.py`
- Test runner: `scripts/run_all_tests.py`

## Security Notes
- Refresh tokens stored in httpOnly cookies
- Access tokens stored in-memory only
- Single refresh-in-flight guard on frontend

---
For more details, see README.md and PR_SUMMARY.md.