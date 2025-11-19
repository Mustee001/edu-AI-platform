// Backend base URL — prefer relative when served by the backend.
// If you still run the frontend from Live Server, this falls back to the
// local backend at port 8000. You can override by setting `window.API_BASE`.
const API_BASE = window.API_BASE || ((window.location.port === '8000' || window.location.origin.includes('localhost:8000')) ? '/' : 'http://localhost:8000/');

// Persist token to localStorage so actions don't unexpectedly "log out" the user.
let token = localStorage.getItem('edu_token') || null;

function setAuthHeader(headers){
  if(token) headers['Authorization'] = 'Bearer ' + token;
}

// helper for authenticated fetches. Adds auth header and handles 401 centrally.
async function authFetch(url, opts = {}){
  opts.headers = opts.headers || {};
  setAuthHeader(opts.headers);
  // default credentials mode: omit (we rely on Authorization header)
  // Single-refresh-in-flight guard: if a refresh is already running, wait for it.
  opts.headers = opts.headers || {};
  let res = await fetch(url, opts);
  if(res.status === 401){
    try{
        // If a refresh is in progress, await it. Otherwise start one.
        if(window.__refreshPromise){
          await window.__refreshPromise;
        } else {
          window.__refreshPromise = (async ()=>{
            // cookie-based refresh: server stores refresh token in an httpOnly cookie
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
        // if we have a token now, retry the request
        if(token){ opts.headers['Authorization'] = 'Bearer ' + token; res = await fetch(url, opts); return res; }
        }catch(e){ /* fallthrough to logout */ }
    // token invalid or expired — clear and show login
    token = null; localStorage.removeItem('edu_token');
    document.getElementById('login').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginMsg').innerText = 'Session expired — please login again.';
  }
  return res;
}

document.getElementById('loginForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  try{
    const res = await fetch(API_BASE + 'token', {method:'POST', body: form});
    if(!res.ok) throw new Error('Login failed');
    const data = await res.json();
    token = data.access_token;
    // persist access token to localStorage; refresh token is stored in an httpOnly cookie
    try{ localStorage.setItem('edu_token', token); }catch(e){}
    document.getElementById('login').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    loadStudents();
    loadLessons();
  }catch(err){
    document.getElementById('loginMsg').innerText = err.message;
  }
});

document.getElementById('logout').addEventListener('click', ()=>{
  // attempt to revoke refresh token on server (cookie-based)
  try{ fetch(API_BASE + 'logout', {method:'POST'}); }catch(e){}
  token = null; localStorage.removeItem('edu_token'); localStorage.removeItem('edu_refresh');
  document.getElementById('login').style.display = 'block';
  document.getElementById('dashboard').style.display = 'none';
});

async function loadStudents(){
  const res = await authFetch(API_BASE + 'teacher/students');
  if(!res.ok){ document.getElementById('students').innerHTML = '<li>Error loading students</li>'; return }
  const data = await res.json();
  const ul = document.getElementById('students'); ul.innerHTML = '';
  data.students.forEach(s=>{
    const li = document.createElement('li');
    li.textContent = `${s.id} — ${s.name} (Grade ${s.grade})`;
    li.style.cursor = 'pointer';
    li.addEventListener('click', ()=>{
      onStudentSelect(s.id, s.name);
    });
    ul.appendChild(li);
    // also add to assign dropdown
    const option = document.createElement('option');
    option.value = s.id;
    option.textContent = `${s.name} (${s.id})`;
    document.getElementById('assignStudent').appendChild(option);
  });
}

async function loadLessons(){
  const res = await authFetch(API_BASE + 'teacher/lessons');
  if(!res.ok){ document.getElementById('lessons').innerHTML = '<li>Error loading lessons</li>'; return }
  const data = await res.json();
  const ul = document.getElementById('lessons'); ul.innerHTML = '';
  data.lessons.slice(0,30).forEach(l=>{
    const li = document.createElement('li');
    li.textContent = `[${l.source}] ${l.item_id} — ${l.subject}: ${l.prompt}`;
    ul.appendChild(li);
    // add to assign lesson dropdown
    const opt = document.createElement('option');
    opt.value = l.item_id;
    opt.textContent = `[${l.source}] ${l.item_id} — ${l.subject}`;
    document.getElementById('assignLesson').appendChild(opt);
  });
}

document.getElementById('getProgress').addEventListener('click', async ()=>{
  const studentId = document.getElementById('progressStudentId').value;
  const res = await authFetch(API_BASE + `students/${studentId}/progress`);
  const out = document.getElementById('progressOutput');
  if(!res.ok){ out.textContent = `Error: ${res.status}`; return }
  const data = await res.json();
  out.textContent = JSON.stringify(data, null, 2);
});

document.getElementById('assignBtn').addEventListener('click', async ()=>{
  const studentId = document.getElementById('assignStudent').value;
  const itemId = document.getElementById('assignLesson').value;
  const res = await authFetch(API_BASE + 'teacher/assign', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({student_id: studentId, item_id: itemId})});
  const msg = document.getElementById('assignMsg');
  if(!res.ok){ msg.textContent = 'Assign failed: ' + res.status; return }
  const data = await res.json();
  msg.textContent = 'Assigned, id=' + data.assignment_id;
});

document.getElementById('exportAssignments').addEventListener('click', async ()=>{
  const res = await authFetch(API_BASE + 'teacher/export_assignments');
  if(!res.ok){ alert('Export failed'); return }
  const text = await res.text();
  const blob = new Blob([text], {type:'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'assignments.csv'; document.body.appendChild(a); a.click(); a.remove();
});

async function onStudentSelect(studentId, studentName){
  document.getElementById('selectedStudent').textContent = studentName + ' ('+studentId+')';
  // load assignments
  const res = await authFetch(API_BASE + `teacher/student/${studentId}/assignments`);
  const al = document.getElementById('studentAssignments'); al.innerHTML = '';
  if(res.ok){
    const d = await res.json();
    d.assignments.forEach(a=>{
      const li = document.createElement('li'); li.textContent = `${a.item_id} — assigned ${a.assigned_at}`; al.appendChild(li);
    });
  } else { al.innerHTML = '<li>Unable to load assignments</li>' }

  // load responses
  const rres = await authFetch(API_BASE + `students/${studentId}/responses`);
  const rl = document.getElementById('studentResponses'); rl.innerHTML = '';
  if(rres.ok){
    const rd = await rres.json();
    rd.responses.forEach(r=>{
      const li = document.createElement('li'); li.textContent = `${r.item_id} — answer: ${r.answer} (correct: ${r.correct}) at ${r.submitted_at}`; rl.appendChild(li);
    });
  } else { rl.innerHTML = '<li>Unable to load responses</li>' }
}

document.getElementById('assignAllBtn')?.addEventListener('click', async ()=>{
  // assign selected lesson to all students via bulk endpoint
  const itemId = document.getElementById('assignLesson').value;
  if(!itemId){ alert('Pick a lesson first'); return }
  const res = await authFetch(API_BASE + 'teacher/assign_bulk', {method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({all:true, item_id: itemId})});
  if(!res.ok){ alert('Bulk assign failed'); return }
  const d = await res.json(); alert('Assigned to ' + d.assigned_ids.length + ' records');
});

document.getElementById('submitResponse').addEventListener('click', async ()=>{
  const student = document.getElementById('selectedStudent').textContent;
  if(!student || student === 'No student selected'){ alert('Select a student first'); return }
  const studentId = student.match(/\(([^)]+)\)$/)[1];
  const itemId = document.getElementById('respItemId').value;
  const answer = document.getElementById('respAnswer').value;
  const correct = document.getElementById('respCorrect').checked;
  if(!itemId){ alert('Enter item id'); return }
  const res = await authFetch(API_BASE + `students/${studentId}/responses`, {method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({item_id: itemId, answer, correct})});
  const msg = document.getElementById('respMsg');
  if(!res.ok){ msg.textContent = 'Submit failed'; return }
  const d = await res.json(); msg.textContent = 'Response saved id=' + d.response_id;
  // refresh responses
  onStudentSelect(studentId, student.split(' (')[0]);
});
// end of script

// If a token exists from a previous session, show dashboard and load data.
if(token){
  document.getElementById('login').style.display = 'none';
  document.getElementById('dashboard').style.display = 'block';
  loadStudents();
  loadLessons();
}
