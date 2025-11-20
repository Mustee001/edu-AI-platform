# edu-AI-platform

## Overview
A secure education platform with JWT authentication, refresh token rotation, and frontend dashboards for teachers and students.

## Features
- FastAPI backend with SQLModel ORM
- JWT access and refresh tokens (DB-backed)
- Secure httpOnly cookie-based refresh flow
- In-memory access token storage on frontend
- Alembic migration scaffold
- Automated test scripts (Option A–D)

## Setup Instructions
1. Clone the repository:
   ```
   git clone git@github.com:Mustee001/edu-AI-platform.git
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run Alembic migrations:
   ```
   alembic upgrade head
   ```
4. Start the backend:
   ```
   uvicorn backend.app.main:app --reload
   ```
5. Open the frontend dashboards in your browser.

## Testing
Run all tests:
```
python scripts/run_all_tests.py
```

## Deployment Checklist
- [ ] Set up production database and environment variables
- [ ] Configure secure cookie flags (Secure, SameSite)
- [ ] Set up HTTPS for backend and frontend
- [ ] Add CI/CD pipeline for automated testing and deployment
- [ ] Monitor logs and error tracking

## API Documentation
See `backend/app/main.py` and `backend/app/auth.py` for endpoint details.

---
For more details, see PR_SUMMARY.md.