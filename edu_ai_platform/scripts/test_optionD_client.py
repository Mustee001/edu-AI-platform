import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print('Login as teacher to get refresh token')
r = client.post('/token', data={'username':'teacher','password':'teacherpass'})
print('login status', r.status_code, r.json())
if r.status_code != 200:
    raise SystemExit(1)
# server sets refresh token in httpOnly cookie; TestClient stores cookies automatically
refresh = client.cookies.get('edu_refresh')
print('refresh token len', len(refresh) if refresh else 0)

print('\nCall /token/refresh with refresh token (should rotate)')
# Provide the old refresh explicitly via JSON to simulate reuse testing; server will also accept cookie.
r2 = client.post('/token/refresh', json={'refresh_token': refresh})
print('refresh status', r2.status_code, r2.json())
if r2.status_code != 200:
    raise SystemExit(1)
# new refresh token is set as cookie by server
new_refresh = client.cookies.get('edu_refresh')
print('new_refresh len', len(new_refresh) if new_refresh else 0)

print('\nCalling /token/refresh again with old refresh should fail (revoked)')
r3 = client.post('/token/refresh', json={'refresh_token': refresh})
print('old refresh reuse status', r3.status_code, r3.text)

print('\nUsing new refresh to get another access token')
# Use the cookie-set refresh token (or provide it explicitly)
r4 = client.post('/token/refresh', json={'refresh_token': new_refresh})
print('new refresh reuse status', r4.status_code, r4.json())
