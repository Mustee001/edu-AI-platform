import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print('Test Option B: Role-Based Access Control (RBAC)')
print('=' * 50)

print('\n1. Login as teacher')
r = client.post('/token', data={'username': 'teacher', 'password': 'teacherpass'})
assert r.status_code == 200, f"Teacher login failed: {r.status_code}"
teacher_token = r.json()['access_token']
print(f'Teacher token: {len(teacher_token)} chars')

print('\n2. Login as student')
r = client.post('/token', data={'username': 'student', 'password': 'studentpass'})
assert r.status_code == 200, f"Student login failed: {r.status_code}"
student_token = r.json()['access_token']
print(f'Student token: {len(student_token)} chars')

print('\n3. Login as admin')
r = client.post('/token', data={'username': 'admin', 'password': 'adminpass'})
assert r.status_code == 200, f"Admin login failed: {r.status_code}"
admin_token = r.json()['access_token']
print(f'Admin token: {len(admin_token)} chars')

print('\n4. Test teacher-only endpoint /teacher-only')
r = client.get('/teacher-only', headers={'Authorization': f'Bearer {teacher_token}'})
print(f'Teacher access to /teacher-only: {r.status_code}')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert 'teacher' in r.json()['msg'].lower(), "Wrong response"

print('\n5. Test student access to /teacher-only (should fail)')
r = client.get('/teacher-only', headers={'Authorization': f'Bearer {student_token}'})
print(f'Student access to /teacher-only: {r.status_code}')
assert r.status_code == 403, f"Expected 403, got {r.status_code}"

print('\n6. Test student-only endpoint /student-only')
r = client.get('/student-only', headers={'Authorization': f'Bearer {student_token}'})
print(f'Student access to /student-only: {r.status_code}')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"

print('\n7. Test teacher access to /student-only (should fail)')
r = client.get('/student-only', headers={'Authorization': f'Bearer {teacher_token}'})
print(f'Teacher access to /student-only: {r.status_code}')
assert r.status_code == 403, f"Expected 403, got {r.status_code}"

print('\n8. Test admin-only endpoint /admin-only')
r = client.get('/admin-only', headers={'Authorization': f'Bearer {admin_token}'})
print(f'Admin access to /admin-only: {r.status_code}')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"

print('\n9. Test teacher access to /admin-only (should fail)')
r = client.get('/admin-only', headers={'Authorization': f'Bearer {teacher_token}'})
print(f'Teacher access to /admin-only: {r.status_code}')
assert r.status_code == 403, f"Expected 403, got {r.status_code}"

print('\n✓ Test Option B: All RBAC tests passed!')
sys.exit(0)
