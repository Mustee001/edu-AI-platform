import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print('Test Option C: Teacher Assignment Features')
print('=' * 50)

print('\n1. Login as teacher')
r = client.post('/token', data={'username': 'teacher', 'password': 'teacherpass'})
assert r.status_code == 200
teacher_token = r.json()['access_token']
print('Teacher logged in')

print('\n2. Get students list')
r = client.get('/teacher/students', headers={'Authorization': f'Bearer {teacher_token}'})
print(f'GET /teacher/students status: {r.status_code}')
assert r.status_code == 200
students_data = r.json()
print(f'Students count: {len(students_data["students"])}')
assert len(students_data['students']) > 0, "No students found"
first_student_id = students_data['students'][0]['id']
print(f'First student: {first_student_id}')

print('\n3. Get lessons list')
r = client.get('/teacher/lessons', headers={'Authorization': f'Bearer {teacher_token}'})
print(f'GET /teacher/lessons status: {r.status_code}')
assert r.status_code == 200
lessons_data = r.json()
print(f'Lessons count: {len(lessons_data["lessons"])}')

if len(lessons_data['lessons']) > 0:
    first_lesson = lessons_data['lessons'][0]
    first_item_id = first_lesson['item_id']
    print(f'First lesson item_id: {first_item_id}')

    print('\n4. Assign a lesson to a student')
    r = client.post('/teacher/assign',
        headers={'Authorization': f'Bearer {teacher_token}'},
        json={'student_id': first_student_id, 'item_id': first_item_id}
    )
    print(f'POST /teacher/assign status: {r.status_code}')
    assert r.status_code == 200
    assignment_data = r.json()
    assert 'assignment_id' in assignment_data
    assignment_id = assignment_data['assignment_id']
    print(f'Assignment created: {assignment_id}')

    print('\n5. Get student assignments')
    r = client.get(f'/teacher/student/{first_student_id}/assignments',
        headers={'Authorization': f'Bearer {teacher_token}'}
    )
    print(f'GET /teacher/student/{first_student_id}/assignments status: {r.status_code}')
    assert r.status_code == 200
    assignments = r.json()['assignments']
    print(f'Student assignments count: {len(assignments)}')
    assert len(assignments) > 0, "No assignments found"
else:
    print('No lessons available for testing assignment creation')

print('\n6. Test bulk assignment')
if len(students_data['students']) > 1 and len(lessons_data['lessons']) > 0:
    r = client.post('/teacher/assign_bulk',
        headers={'Authorization': f'Bearer {teacher_token}'},
        json={
            'student_ids': [s['id'] for s in students_data['students'][:2]],
            'item_id': lessons_data['lessons'][0]['item_id']
        }
    )
    print(f'POST /teacher/assign_bulk status: {r.status_code}')
    assert r.status_code == 200
    bulk_data = r.json()
    print(f'Bulk assignment created: {len(bulk_data["assigned_ids"])} assignments')

print('\n✓ Test Option C: All teacher assignment tests passed!')
sys.exit(0)
