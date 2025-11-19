"""
Main FastAPI app with authentication and RBAC endpoints.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, create_refresh_token, verify_refresh_token, revoke_refresh_token, Token, TokenWithRefresh, get_current_user, require_role, User
from pathlib import Path
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import Request
from .auth_log import record_event, recent_events
from .database import init_db, get_session
from .models import Student, Lesson
from .models import Assignment, StudentResponse, Classroom
from sqlmodel import select
from fastapi import Response, Request
from .models import Assignment, StudentResponse
from datetime import datetime

# load sample students from backend/data/students.json if present
DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
STUDENTS_FILE = DATA_ROOT / "students.json"

def load_students():
    if STUDENTS_FILE.exists():
        with STUDENTS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    # fallback sample
    return [
        {"id": "s1", "name": "Amina", "grade": 4},
        {"id": "s2", "name": "Chinedu", "grade": 4},
    ]

def load_lessons():
    root = Path(__file__).resolve().parents[2]
    lessons = []
    for p in root.glob("item_banks/*/grade4_items.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                lessons.append({
                    "item_id": it.get("item_id"),
                    "subject": it.get("subject"),
                    "prompt": it.get("prompt"),
                    "source": p.parent.name,
                })
        except Exception:
            continue
    return lessons

app = FastAPI()


@app.middleware("http")
async def auth_logging_middleware(request: Request, call_next):
    # capture auth header for debugging (don't log secrets in production)
    auth_hdr = request.headers.get('authorization')
    resp = await call_next(request)
    if resp.status_code in (401, 403):
        try:
            record_event({
                'path': str(request.url.path),
                'method': request.method,
                'status': resp.status_code,
                'auth_header_present': bool(auth_hdr),
            })
        except Exception:
            pass
    return resp

# initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()
    # seed DB if empty
    with get_session() as sess:
        stmt = select(Student)
        if not sess.exec(stmt).first():
            sess.add_all([
                Student(student_id="s1", name="Amina", grade=4),
                Student(student_id="s2", name="Chinedu", grade=4),
                Student(student_id="s3", name="Ngozi", grade=4),
            ])
            sess.commit()
        # seed classroom if empty
        stmtc = select(Classroom)
        if not sess.exec(stmtc).first():
            sess.add_all([Classroom(name="Class 4A", teacher_id="t1"), Classroom(name="Class 4B")])
            sess.commit()
        # seed lessons from existing item banks
        stmt2 = select(Lesson)
        if not sess.exec(stmt2).first():
            root = Path(__file__).resolve().parents[2]
            for p in root.glob("item_banks/*/grade4_items.json"):
                try:
                    with p.open("r", encoding="utf-8") as f:
                        items = json.load(f)
                    for it in items:
                        lesson = Lesson(item_id=it.get("item_id"), subject=it.get("subject"), prompt=it.get("prompt"), source=p.parent.name)
                        sess.add(lesson)
                    sess.commit()
                except Exception:
                    continue

# allow frontend hosted elsewhere to call API during prototyping
# Use permissive CORS for prototyping but avoid wildcard + credentials simultaneously.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static dashboard files so you can open http://localhost:8000/dashboard/
root = Path(__file__).resolve().parents[2] / "frontend"
# Mount teacher dashboard on /dashboard
root_teacher = root / "teacher_dashboard"
if root_teacher.exists():
    app.mount("/dashboard", StaticFiles(directory=str(root_teacher)), name="dashboard")
# Mount student dashboard on /student_dashboard
root_student = root / "student_dashboard"
if root_student.exists():
    app.mount("/student_dashboard", StaticFiles(directory=str(root_student)), name="student_dashboard")

# Redirect root to the teacher dashboard for convenience when visiting the API server
@app.get("/")
def root_redirect():
    return RedirectResponse(url='/dashboard/')

@app.post("/token", response_model=Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # include student_id and teacher_id in token so clients and /me can access them
    payload = {"sub": user.username, "role": user.role, "student_id": user.student_id, "teacher_id": user.teacher_id}
    access_token = create_access_token(payload, expires_delta=3600 * 24)  # default 24h for prototype
    refresh_token = create_refresh_token(payload, expires_delta=60 * 60 * 24 * 7)  # 7 days
    # set httpOnly cookie for refresh token (prototype: secure=False for local dev)
    try:
        response.set_cookie(key='edu_refresh', value=refresh_token, httponly=True, path='/', max_age=60 * 60 * 24 * 7)
    except Exception:
        pass
    # return access token only (refresh token delivered in httpOnly cookie)
    return Token(access_token=access_token, token_type="bearer")


@app.post('/token/refresh')
def token_refresh(payload: dict, request: Request, response: Response):
    """Exchange a valid refresh token for a new access token.
    Payload: {"refresh_token": "..."}
    """
    rt = payload.get('refresh_token') or request.cookies.get('edu_refresh')
    if not rt:
        raise HTTPException(status_code=400, detail='refresh_token required')
    info = verify_refresh_token(rt)
    if not info:
        raise HTTPException(status_code=401, detail='Invalid or revoked refresh token')
    # rotate refresh token: revoke old one, issue new refresh + access token
    payload = {"sub": info.get('sub'), "role": info.get('role'), "student_id": info.get('student_id'), "teacher_id": info.get('teacher_id')}
    # revoke old
    revoke_refresh_token(rt)
    new_refresh = create_refresh_token(payload, expires_delta=60 * 60 * 24 * 7)
    access_token = create_access_token(payload, expires_delta=3600 * 24)
    try:
        response.set_cookie(key='edu_refresh', value=new_refresh, httponly=True, path='/', max_age=60 * 60 * 24 * 7)
    except Exception:
        pass
    # return access token only; refresh token is rotated in cookie
    return {"access_token": access_token, "token_type": "bearer"}


@app.post('/logout')
def logout(payload: dict = None, request: Request = None, response: Response = None):
    """Revoke a refresh token (prototype). Accepts JSON payload or cookie."""
    rt = None
    if payload and isinstance(payload, dict):
        rt = payload.get('refresh_token')
    if not rt and request:
        rt = request.cookies.get('edu_refresh')
    if not rt:
        raise HTTPException(status_code=400, detail='refresh_token required')
    revoke_refresh_token(rt)
    # delete cookie
    try:
        if response:
            response.delete_cookie('edu_refresh', path='/')
    except Exception:
        pass
    return {"status": "ok"}

@app.get("/me", response_model=User)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/admin-only")
def admin_only(user: User = Depends(require_role("admin"))):
    return {"msg": f"Hello, {user.username} (admin)"}


@app.get('/admin/auth_logs')
def get_auth_logs(user: User = Depends(require_role("admin")), limit: int = 100):
    """Return recent auth-related logs (admin only)."""
    logs = recent_events(limit)
    return {"count": len(logs), "logs": logs}

@app.get("/teacher-only")
def teacher_only(user: User = Depends(require_role("teacher"))):
    return {"msg": f"Hello, {user.username} (teacher)"}

@app.get("/student-only")
def student_only(user: User = Depends(require_role("student"))):
    return {"msg": f"Hello, {user.username} (student)"}


@app.get("/teacher/students")
def teacher_students(user: User = Depends(require_role("teacher"))):
    """Return a list of students for the teacher dashboard (prototype)."""
    # prefer DB students
    with get_session() as sess:
        rows = sess.exec(select(Student)).all()
        students = [{"id": r.student_id, "name": r.name, "grade": r.grade, "class_id": r.class_id} for r in rows]
    return {"students": students}


@app.get("/teacher/lessons")
def teacher_lessons(user: User = Depends(require_role("teacher"))):
    """Return a simple flattened lessons list (reads grade4 item banks)."""
    # prefer DB lessons
    with get_session() as sess:
        rows = sess.exec(select(Lesson)).all()
        lessons = [{"item_id": r.item_id, "subject": r.subject, "prompt": r.prompt, "source": r.source} for r in rows]
    return {"lessons": lessons}


@app.post("/teacher/assign")
def teacher_assign(payload: dict, user: User = Depends(require_role("teacher"))):
    """Assign a lesson item to a student. Payload: {student_id, item_id}"""
    student_id = payload.get("student_id")
    item_id = payload.get("item_id")
    if not student_id or not item_id:
        raise HTTPException(status_code=400, detail="student_id and item_id required")
    from .models import Assignment
    with get_session() as sess:
        assign = Assignment(student_id=student_id, item_id=item_id, assigned_at=datetime.utcnow().isoformat())
        sess.add(assign)
        sess.commit()
        sess.refresh(assign)
    return {"status": "ok", "assignment_id": assign.id}


@app.post("/teacher/assign_bulk")
def teacher_assign_bulk(payload: dict, user: User = Depends(require_role("teacher"))):
    """Assign an item to multiple students. Payload: {student_ids: [...], item_id, all: bool}
    If all=true, assign to all students in DB.
    """
    student_ids = payload.get("student_ids") or []
    item_id = payload.get("item_id")
    all_flag = payload.get("all", False)
    if not item_id:
        raise HTTPException(status_code=400, detail="item_id required")
    class_id = payload.get("class_id")
    with get_session() as sess:
        if all_flag:
            students = sess.exec(select(Student)).all()
            student_ids = [s.student_id for s in students]
        elif class_id:
            students = sess.exec(select(Student).where(Student.class_id == int(class_id))).all()
            student_ids = [s.student_id for s in students]
        assigned = []
        for sid in student_ids:
            a = Assignment(student_id=sid, item_id=item_id, assigned_at=datetime.utcnow().isoformat())
            sess.add(a)
            sess.commit()
            sess.refresh(a)
            assigned.append(a.id)
    return {"status": "ok", "assigned_ids": assigned}


@app.get("/teacher/student/{student_id}/assignments")
def teacher_student_assignments(student_id: str, user: User = Depends(require_role("teacher"))):
    with get_session() as sess:
        rows = sess.exec(select(Assignment).where(Assignment.student_id == student_id)).all()
    return {"assignments": [ {"id": r.id, "item_id": r.item_id, "assigned_at": r.assigned_at} for r in rows ] }


@app.post("/students/{student_id}/responses")
def post_student_response(student_id: str, payload: dict, user: User = Depends(get_current_user)):
    # allow teacher to record responses for any student, or allow a student to record their own responses
    if not (user.role == "teacher" or (user.role == "student" and user.student_id == student_id)):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item_id = payload.get("item_id")
    answer = payload.get("answer")
    correct = payload.get("correct")
    if not item_id:
        raise HTTPException(status_code=400, detail="item_id required")
    with get_session() as sess:
        resp = StudentResponse(student_id=student_id, item_id=item_id, answer=answer, correct=bool(correct), submitted_at=datetime.utcnow().isoformat())
        sess.add(resp)
        sess.commit()
        sess.refresh(resp)
    return {"status":"ok", "response_id": resp.id}


@app.get('/students/{student_id}/assignments')
def students_assignments(student_id: str, user: User = Depends(get_current_user)):
    # allow teacher to view any student's assignments, or a student to view their own
    if not (user.role == 'teacher' or (user.role == 'student' and user.student_id == student_id)):
        raise HTTPException(status_code=403, detail='Insufficient permissions')
    with get_session() as sess:
        rows = sess.exec(select(Assignment).where(Assignment.student_id == student_id)).all()
    return {"assignments": [ {"id": r.id, "item_id": r.item_id, "assigned_at": r.assigned_at} for r in rows ] }


@app.get("/students/{student_id}/responses")
def get_student_responses(student_id: str, user: User = Depends(require_role("teacher"))):
    with get_session() as sess:
        rows = sess.exec(select(StudentResponse).where(StudentResponse.student_id == student_id)).all()
    return {"responses": [ {"id": r.id, "item_id": r.item_id, "answer": r.answer, "correct": r.correct, "submitted_at": r.submitted_at} for r in rows ] }


@app.get("/teacher/export_assignments")
def export_assignments(user: User = Depends(require_role("teacher"))):
    """Export all assignments as CSV (download)."""
    import csv
    from io import StringIO
    from .models import Assignment
    # optional filters: student_id, class_id, since, until
    from fastapi import Query
    import datetime as _dt

    def _parse_date(s):
        try:
            return _dt.datetime.fromisoformat(s)
        except Exception:
            return None

    # read possible query params
    # note: FastAPI Query cannot be used directly here (we're in normal function)
    from fastapi import Request
    # get request object from context
    # simple approach: use global environ via Starlette request: uvicorn passes Request via dependency normally
    # fallback: export without filters
    with get_session() as sess:
        rows = sess.exec(select(Assignment)).all()
        student_map = {s.student_id: s.name for s in sess.exec(select(Student)).all()}
        lesson_map = {l.item_id: (l.subject, l.source) for l in sess.exec(select(Lesson)).all()}

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id", "student_name", "item_id", "subject", "source", "assigned_at"])
    for r in rows:
        name = student_map.get(r.student_id, "")
        subject, source = lesson_map.get(r.item_id, ("", ""))
        writer.writerow([r.student_id, name, r.item_id, subject, source, r.assigned_at])

    return Response(content=buf.getvalue(), media_type="text/csv")


@app.get("/students/{student_id}/progress")
def student_progress(student_id: str, user: User = Depends(get_current_user)):
    """Prototype student progress endpoint. Teachers can view any student's progress."""
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # mock progress data
    progress = {
        "student_id": student_id,
        "skill_scores": {
            "numeracy": 0.56,
            "literacy": 0.62
        },
        "recent_responses": [
            {"item_id": "g4-num-001", "correct": True},
            {"item_id": "g4-lit-002", "correct": False}
        ]
    }
    return progress
