// Backend base URL — prefer relative when served by the backend.
const API_BASE = window.API_BASE || ((window.location.port === '8000' || window.location.origin.includes('localhost:8000')) ? '/' : 'http://localhost:8000/');

// Persist token to localStorage so actions don't unexpectedly log out the user.
let token = localStorage.getItem('edu_token') || null;

function setAuthHeader(headers){ if(token) headers['Authorization'] = 'Bearer ' + token; }

async function authFetch(url, opts = {}){
  opts.headers = opts.headers || {};
  setAuthHeader(opts.headers);
  // Single-refresh-in-flight guard: if a refresh is already running, wait for it.
  let res = await fetch(url, opts);
  if(res.status === 401){
    try{
      if(window.__refreshPromise){
        await window.__refreshPromise;
      } else {
        window.__refreshPromise = (async ()=>{
          // cookie-based refresh
          const rres = await fetch(API_BASE + 'token/refresh', {method:'POST'});
          if(rres.ok){
            const rdata = await rres.json();
            token = rdata.access_token;
            try{ localStorage.setItem('edu_token', token); }catch(e){}
          } else {
            token = null; localStorage.removeItem('edu_token');
          }
        })();
        try{ await window.__refreshPromise; } finally { window.__refreshPromise = null; }
      }
      if(token){ opts.headers['Authorization'] = 'Bearer ' + token; res = await fetch(url, opts); return res; }
    }catch(e){ /* fallthrough to logout */ }
    token = null; localStorage.removeItem('edu_token'); localStorage.removeItem('edu_refresh'); document.getElementById('login').style.display = 'block'; document.getElementById('dashboard').style.display = 'none'; document.getElementById('loginMsg').innerText = 'Session expired — please login again.';
  }
  return res;
}

document.getElementById('loginForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const form = new URLSearchParams(); form.append('username', username); form.append('password', password);
  try{
    const res = await fetch(API_BASE + 'token', {method:'POST', body: form});
    if(!res.ok) throw new Error('Login failed');
    const data = await res.json(); token = data.access_token; try{ localStorage.setItem('edu_token', token); }catch(e){}
    document.getElementById('login').style.display = 'none'; document.getElementById('dashboard').style.display = 'block';
    loadAssignments();
  }catch(err){ document.getElementById('loginMsg').innerText = err.message; }
});

document.getElementById('logout').addEventListener('click', ()=>{ try{ fetch(API_BASE + 'logout', {method:'POST'}); }catch(e){} token = null; localStorage.removeItem('edu_token'); localStorage.removeItem('edu_refresh'); document.getElementById('login').style.display = 'block'; document.getElementById('dashboard').style.display = 'none'; });

async function loadAssignments(){
  // find current user
  const meRes = await authFetch(API_BASE + 'me');
  if(!meRes.ok) return;
  const me = await meRes.json();
  const studentId = me.student_id;
  const res = await authFetch(API_BASE + `teacher/student/${studentId}/assignments`);
  const ul = document.getElementById('assignments'); ul.innerHTML = '';
  if(res.ok){ const d = await res.json(); d.assignments.forEach(a=>{ const li = document.createElement('li'); li.textContent = `${a.item_id} — assigned ${a.assigned_at}`; ul.appendChild(li); }); }
}

document.getElementById('submit').addEventListener('click', async ()=>{
  const meRes = await authFetch(API_BASE + 'me');
  if(!meRes.ok){ document.getElementById('submitMsg').textContent = 'Not authenticated'; return }
  const me = await meRes.json();
  const studentId = me.student_id;
  const itemId = document.getElementById('itemId').value;
  const answer = document.getElementById('answer').value;
  const correct = document.getElementById('correct').checked;
  const res = await authFetch(API_BASE + `students/${studentId}/responses`, {method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({item_id: itemId, answer, correct})});
  const msg = document.getElementById('submitMsg');
  if(!res.ok){ msg.textContent = 'Submit failed'; return }
  const d = await res.json(); msg.textContent = 'Saved id=' + d.response_id; loadAssignments();
});

// Auto-load if token exists
if(token){ document.getElementById('login').style.display = 'none'; document.getElementById('dashboard').style.display = 'block'; loadAssignments(); }
