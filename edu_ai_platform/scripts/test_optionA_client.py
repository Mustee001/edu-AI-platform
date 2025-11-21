import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print('Test Option A: Basic Login Flow')
print('=' * 50)

print('\n1. Test login with valid teacher credentials')
r = client.post('/token', data={'username': 'teacher', 'password': 'teacherpass'})
print(f'Login status: {r.status_code}')
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
token_data = r.json()
assert 'access_token' in token_data, "Missing access_token"
print(f'Access token received: {len(token_data["access_token"])} chars')

print('\n2. Test GET /me endpoint with valid token')
access_token = token_data['access_token']
r2 = client.get('/me', headers={'Authorization': f'Bearer {access_token}'})
print(f'GET /me status: {r2.status_code}')
assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
user = r2.json()
assert user['username'] == 'teacher', "Wrong username"
assert user['role'] == 'teacher', "Wrong role"
print(f'User: {user["username"]}, Role: {user["role"]}')

print('\n3. Test login with invalid credentials')
r3 = client.post('/token', data={'username': 'teacher', 'password': 'wrongpass'})
print(f'Invalid login status: {r3.status_code}')
assert r3.status_code == 400, f"Expected 400, got {r3.status_code}"

print('\n4. Test GET /me with invalid token')
r4 = client.get('/me', headers={'Authorization': 'Bearer invalid_token'})
print(f'GET /me with invalid token status: {r4.status_code}')
assert r4.status_code == 401, f"Expected 401, got {r4.status_code}"

print('\n5. Test access without token')
r5 = client.get('/me')
print(f'GET /me without token status: {r5.status_code}')
assert r5.status_code == 401, f"Expected 401, got {r5.status_code}"

print('\n✓ Test Option A: All basic login flow tests passed!')
sys.exit(0)
