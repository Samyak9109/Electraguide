/* ═══════════════════════════════════════════════════════════
   ELECTRAGUIDE — Frontend App JS
   Communicates with Flask backend via REST API
════════════════════════════════════════════════════════════ */

'use strict';

/* ── CONFIG ─────────────────────────────────────────────── */
const BASE_URL = '';  // same-origin; change for separate backend
const SESSION_ID = 'eg_' + Math.random().toString(36).slice(2, 10);

/* ── STATE ──────────────────────────────────────────────── */
const State = {
  user: { name: 'Voter', state: '', firstTime: false },
  checklist: [],
  score: 40,
  currentTab: 'home',
  quizStep: 0,
  tipIndex: 0,
  chatHistory: [],
  glossary: [],
};

/* ── API HELPERS ────────────────────────────────────────── */
async function api(path, opts = {}) {
  try {
    const res = await fetch(BASE_URL + path, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });
    return await res.json();
  } catch (e) {
    console.error('API error:', path, e);
    return null;
  }
}

const get = path => api(path);
const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) });

/* ── SCREEN NAVIGATION ──────────────────────────────────── */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) setTimeout(() => el.classList.add('active'), 20);
}

/* ── TAB NAVIGATION ─────────────────────────────────────── */
function switchTab(tabId) {
  State.currentTab = tabId;

  // Main tab content
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  const tab = document.getElementById('tab-' + tabId);
  if (tab) tab.classList.add('active');

  // Sidebar items
  document.querySelectorAll('.sb-item').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabId);
  });

  // Mobile nav
  document.querySelectorAll('.mn-item').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabId);
  });

  // Tab-specific init
  if (tabId === 'home') refreshHome();
  if (tabId === 'checklist') renderChecklist();
  if (tabId === 'glossary') loadGlossary();
}

/* ── SPLASH / ONBOARDING ────────────────────────────────── */
function initSplash() {
  document.getElementById('start-btn').addEventListener('click', () => {
    showScreen('onboard');
    renderQuizStep();
  });

  document.getElementById('skip-link').addEventListener('click', e => {
    e.preventDefault();
    loadSavedUser();
    showScreen('app');
    initApp();
  });

  document.getElementById('ob-back').addEventListener('click', () => {
    if (State.quizStep > 0) {
      State.quizStep--;
      renderQuizStep();
    } else {
      showScreen('splash');
    }
  });
}

const QUIZ = [
  {
    emoji: '👋',
    q: 'Are you a first-time voter?',
    opts: [
      { icon: '🌱', label: 'Yes, first time!' },
      { icon: '🔁', label: 'Voted before' },
      { icon: '🏠', label: 'Recently relocated' },
    ],
  },
  {
    emoji: '📍',
    q: 'Which state are you voting in?',
    opts: [
      { icon: '🏙️', label: 'Maharashtra' },
      { icon: '🌆', label: 'Delhi' },
      { icon: '🌇', label: 'Karnataka' },
      { icon: '🗺️', label: 'Other state' },
    ],
  },
  {
    emoji: '🪪',
    q: 'Do you have a Voter ID card (EPIC)?',
    opts: [
      { icon: '✅', label: 'Yes, I have it' },
      { icon: '⏳', label: 'Applied, pending' },
      { icon: '❌', label: 'Not yet applied' },
    ],
  },
];

function renderQuizStep() {
  updateDots();
  const stage = document.getElementById('quiz-stage');

  if (State.quizStep < QUIZ.length) {
    const q = QUIZ[State.quizStep];
    stage.innerHTML = `
      <div class="quiz-card">
        <div class="qz-emoji">${q.emoji}</div>
        <div class="qz-q">${q.q}</div>
        <div class="qz-opts">
          ${q.opts.map((o, i) => `
            <button class="qz-opt" data-idx="${i}">
              <span class="oi">${o.icon}</span>${o.label}
            </button>
          `).join('')}
        </div>
      </div>`;

    stage.querySelectorAll('.qz-opt').forEach(btn => {
      btn.addEventListener('click', () => handleQuizAnswer(parseInt(btn.dataset.idx)));
    });
  } else {
    // Name step
    stage.innerHTML = `
      <div class="quiz-card">
        <div class="qz-emoji">🎉</div>
        <div class="qz-q">Almost done! What should we call you?</div>
        <div class="name-wrap">
          <input class="field-lg" id="name-input" type="text" placeholder="Your first name" maxlength="24" autocomplete="given-name">
          <button class="btn-primary full" id="finish-btn">Start My Journey →</button>
        </div>
      </div>`;

    document.getElementById('name-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') finishOnboard();
    });
    document.getElementById('finish-btn').addEventListener('click', finishOnboard);
    setTimeout(() => document.getElementById('name-input')?.focus(), 100);
  }
}

function handleQuizAnswer(idx) {
  if (State.quizStep === 0) State.user.firstTime = idx === 0;
  if (State.quizStep === 1) State.user.state = QUIZ[1].opts[idx].label;

  const btns = document.querySelectorAll('.qz-opt');
  btns.forEach(b => b.classList.remove('sel'));
  btns[idx].classList.add('sel');

  setTimeout(() => {
    State.quizStep++;
    renderQuizStep();
  }, 280);
}

function finishOnboard() {
  const nameEl = document.getElementById('name-input');
  State.user.name = nameEl?.value.trim() || 'Voter';
  saveUser();
  showScreen('app');
  initApp();
}

function updateDots() {
  const total = QUIZ.length + 1; // +1 for name step
  document.getElementById('step-dots').innerHTML = Array.from({ length: total }, (_, i) => {
    const cls = i < State.quizStep ? 'done' : i === State.quizStep ? 'active' : '';
    return `<div class="sdot ${cls}"></div>`;
  }).join('');
}

/* ── USER PERSISTENCE ───────────────────────────────────── */
function saveUser() {
  localStorage.setItem('eg_user', JSON.stringify(State.user));
  post('/api/session', { session: SESSION_ID, user: State.user });
}

function loadSavedUser() {
  try {
    const stored = localStorage.getItem('eg_user');
    if (stored) State.user = JSON.parse(stored);
  } catch (_) {}
}

/* ── APP INIT ───────────────────────────────────────────── */
async function initApp() {
  updateUserUI();
  await loadChecklist();
  await loadTip();
  await loadGlossary();
  switchTab('home');
  bindNavigation();
  bindChecklist();
  bindChat();
  bindBooth();
  bindGlossary();
  bindDownload();
}

function bindNavigation() {
  // Sidebar
  document.querySelectorAll('[data-tab]').forEach(el => {
    el.addEventListener('click', () => switchTab(el.dataset.tab));
  });
}

function updateUserUI() {
  const name = State.user.name || 'Voter';
  const initial = name[0].toUpperCase();
  const hour = new Date().getHours();
  const greet = hour < 12 ? 'Good morning,' : hour < 17 ? 'Good afternoon,' : 'Good evening,';

  document.getElementById('home-greeting').textContent = greet;
  document.getElementById('home-username').textContent = name;
  document.getElementById('home-avatar').textContent = initial;
  document.getElementById('sb-uname').textContent = name;
  document.getElementById('sb-avatar').textContent = initial;
}

/* ── HOME ───────────────────────────────────────────────── */
function refreshHome() {
  const done = State.checklist.filter(i => i.done).length;
  const total = State.checklist.length || 5;
  const pct = Math.round((done / total) * 100);
  State.score = pct;

  // Ring
  const circumference = 2 * Math.PI * 58; // r=58
  const offset = circumference - (pct / 100) * circumference;
  const ring = document.getElementById('ring-path');
  if (ring) ring.setAttribute('stroke-dashoffset', offset.toFixed(1));

  const pctEl = document.getElementById('ring-pct');
  if (pctEl) pctEl.textContent = pct;

  // Score bar
  const fill = document.getElementById('score-fill');
  if (fill) fill.style.width = pct + '%';

  const tasksEl = document.getElementById('score-tasks');
  if (tasksEl) tasksEl.textContent = `${done}/${total} tasks done`;
  const pctSmEl = document.getElementById('score-pct-sm');
  if (pctSmEl) pctSmEl.textContent = pct + '%';

  const qaSubEl = document.getElementById('qa-checklist-sub');
  if (qaSubEl) qaSubEl.textContent = `${done}/${total} done`;

  const sbStatusEl = document.getElementById('sb-ustatus');
  if (sbStatusEl) sbStatusEl.textContent = pct + '% ready to vote';

  updateUserUI();
}

/* ── CHECKLIST ──────────────────────────────────────────── */
async function loadChecklist() {
  const stored = localStorage.getItem('eg_checklist');
  if (stored) {
    State.checklist = JSON.parse(stored);
    return;
  }
  const data = await get('/api/checklist?session=' + SESSION_ID);
  if (data?.checklist) {
    State.checklist = data.checklist;
    localStorage.setItem('eg_checklist', JSON.stringify(State.checklist));
  }
}

function renderChecklist() {
  const list = document.getElementById('checklist-list');
  if (!list) return;

  const done = State.checklist.filter(i => i.done).length;
  const badge = document.getElementById('cl-badge');
  if (badge) badge.textContent = `${done}/${State.checklist.length}`;

  list.innerHTML = State.checklist.map(item => `
    <div class="cl-item ${item.done ? 'done' : ''}" data-id="${item.id}">
      <div class="cl-check ${item.done ? 'done' : ''}">${item.done ? '✓' : ''}</div>
      <div class="cl-body">
        <div class="cl-title ${item.done ? 'done' : ''}">${item.title}</div>
        <div class="cl-meta">${item.meta}</div>
      </div>
      <span class="cl-tag tag-${item.done ? 'done' : item.tag}">${item.done ? 'Done' : item.tag === 'urgent' ? 'Urgent' : 'Pending'}</span>
    </div>
  `).join('');

  list.querySelectorAll('.cl-item:not(.done)').forEach(el => {
    el.addEventListener('click', () => toggleItem(parseInt(el.dataset.id)));
  });
}

function bindChecklist() {
  renderChecklist();
}

async function toggleItem(id) {
  const item = State.checklist.find(i => i.id === id);
  if (!item || item.done) return;

  item.done = true;
  item.tag = 'done';
  localStorage.setItem('eg_checklist', JSON.stringify(State.checklist));

  renderChecklist();
  refreshHome();

  const data = await post('/api/checklist/toggle', { session: SESSION_ID, id });
  if (data?.score !== undefined) {
    showToast(`✓ Marked done! ${data.score}% ready`);
  }
}

function bindDownload() {
  document.getElementById('download-btn')?.addEventListener('click', downloadPlan);
}

function downloadPlan() {
  const done = State.checklist.filter(i => i.done);
  const pending = State.checklist.filter(i => !i.done);
  const pct = Math.round((done.length / State.checklist.length) * 100);
  const date = new Date().toLocaleDateString('en-IN', { dateStyle: 'long' });

  const content = [
    '╔════════════════════════════════════╗',
    '║      ELECTRAGUIDE — MY VOTING PLAN  ║',
    '╚════════════════════════════════════╝',
    '',
    `Voter: ${State.user.name}`,
    `State: ${State.user.state || 'Not specified'}`,
    `Date:  ${date}`,
    `Progress: ${done.length}/${State.checklist.length} tasks · ${pct}% ready`,
    '',
    '─── COMPLETED ──────────────────────────',
    ...done.map(i => `  [✓] ${i.title}`),
    '',
    '─── PENDING ────────────────────────────',
    ...pending.map(i => `  [ ] ${i.title}  (${i.meta})`),
    '',
    '─── OFFICIAL RESOURCES ─────────────────',
    '  • voters.eci.gov.in   — ECI portal',
    '  • nvsp.in             — Registration',
    '  • voterportal.eci.gov.in — Voter ID',
    '  • 1950                — Helpline (toll-free)',
    '',
    'Generated by ElectraGuide v2.0',
    'Non-partisan · Verified ECI data',
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain' });
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: `ElectraGuide_VotingPlan_${State.user.name}.txt`,
  });
  a.click();
  showToast('📄 Plan downloaded!');
}

/* ── TIPS ───────────────────────────────────────────────── */
async function loadTip() {
  const data = await get('/api/tip');
  if (data?.tip) {
    const el = document.getElementById('tip-text');
    if (el) el.textContent = data.tip;
  }
  document.getElementById('tip-btn')?.addEventListener('click', loadTip);
}

/* ── CHAT ───────────────────────────────────────────────── */
function bindChat() {
  document.querySelectorAll('.cpill').forEach(btn => {
    btn.addEventListener('click', () => sendQuestion(btn.dataset.q));
  });

  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');

  sendBtn?.addEventListener('click', () => {
    const q = input.value.trim();
    if (q) sendQuestion(q);
  });

  input?.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = input.value.trim();
      if (q) sendQuestion(q);
    }
  });
}

async function sendQuestion(question) {
  const input = document.getElementById('chat-input');
  if (input) input.value = '';

  // Hide pills after first question
  const pills = document.getElementById('chat-pills');
  if (pills) pills.style.display = 'none';

  appendBubble(question, 'user');

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  appendTyping(typingId);

  const data = await post('/api/chat', { question });

  document.getElementById(typingId)?.remove();

  if (data?.answer) {
    appendBubble(data.answer, 'ai');
  } else {
    appendBubble('Sorry, I couldn\'t reach the server. Check your connection and try again.', 'ai');
  }
}

function appendBubble(text, role) {
  const msgs = document.getElementById('chat-msgs');
  if (!msgs) return;

  const div = document.createElement('div');
  div.className = `bubble-row ${role}`;

  const formatted = text.replace(/\n/g, '<br>');

  if (role === 'ai') {
    div.innerHTML = `
      <div class="bubble-av">⚡</div>
      <div class="bubble-txt">${formatted}</div>`;
  } else {
    div.innerHTML = `<div class="bubble-txt">${formatted}</div>`;
  }

  msgs.appendChild(div);
  scrollChat();
}

function appendTyping(id) {
  const msgs = document.getElementById('chat-msgs');
  if (!msgs) return;

  const div = document.createElement('div');
  div.className = 'bubble-row ai';
  div.id = id;
  div.innerHTML = `
    <div class="bubble-av">⚡</div>
    <div class="bubble-txt"><span class="typing-dots">● ● ●</span></div>`;
  msgs.appendChild(div);
  scrollChat();
}

function scrollChat() {
  const body = document.getElementById('chat-body');
  if (body) setTimeout(() => body.scrollTop = body.scrollHeight, 50);
}

/* ── BOOTH FINDER ───────────────────────────────────────── */
function bindBooth() {
  document.getElementById('booth-search-btn')?.addEventListener('click', findBooth);
  document.getElementById('booth-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') findBooth();
  });
}

async function findBooth() {
  const input = document.getElementById('booth-input');
  const query = input?.value.trim();
  if (!query) { showToast('Enter a Voter ID, pincode, or city name'); return; }

  const area = document.getElementById('booth-result-area');
  area.innerHTML = '<div class="empty-state"><div class="es-icon">🔍</div><p>Searching ECI database…</p></div>';

  const data = await post('/api/booth', { query });

  if (data?.booth) {
    const b = data.booth;
    area.innerHTML = `
      <div class="booth-card">
        <h4>📍 ${b.name}</h4>
        <p>${b.address}</p>
        <p class="booth-meta">${b.ward}</p>
        <div class="booth-dist">📏 ${b.distance}</div>
        <div class="booth-verified">✓ ECI Verified Data</div>
        <div class="booth-actions">
          <button class="btn-ghost" onclick="showToast('Opening directions…')">🗺️ Get Directions</button>
          <button class="btn-ghost" onclick="showToast('⏰ Reminder set for Election Day!')">⏰ Set Reminder</button>
          <button class="btn-ghost" onclick="showToast('📋 Booth saved to checklist!')">📋 Save to Checklist</button>
        </div>
      </div>`;
  } else {
    area.innerHTML = '<div class="empty-state"><div class="es-icon">⚠️</div><p>Could not fetch booth data. Try again or visit voters.eci.gov.in</p></div>';
  }
}

/* ── GLOSSARY ───────────────────────────────────────────── */
async function loadGlossary() {
  if (State.glossary.length) { renderGlossary(); return; }
  const data = await get('/api/glossary');
  if (data?.glossary) {
    State.glossary = data.glossary;
    const countEl = document.getElementById('gloss-count');
    if (countEl) countEl.textContent = State.glossary.length + ' terms';
    renderGlossary();
  }
}

function renderGlossary(filter = '') {
  const list = document.getElementById('gloss-list');
  if (!list) return;

  const items = filter
    ? State.glossary.filter(g =>
        g.term.toLowerCase().includes(filter.toLowerCase()) ||
        g.def.toLowerCase().includes(filter.toLowerCase()))
    : State.glossary;

  list.innerHTML = items.length
    ? items.map(g => `
        <div class="gloss-card">
          <div class="gloss-term">${g.term}</div>
          <div class="gloss-def">${g.def}</div>
          <div class="gloss-source">✓ ${g.source} Verified</div>
        </div>`).join('')
    : '<p style="color:var(--muted);padding:1.5rem;text-align:center">No terms found.</p>';
}

function bindGlossary() {
  document.getElementById('gloss-input')?.addEventListener('input', e => {
    renderGlossary(e.target.value);
  });
}

/* ── TOAST ──────────────────────────────────────────────── */
let toastTimer;
function showToast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}

/* ── DEADLINE COUNTDOWN ─────────────────────────────────── */
function updateDeadline() {
  // Demo: fixed 12 days — in production, fetch from API
  const el = document.getElementById('dl-count');
  if (el) el.textContent = '12 days';
}

/* ── BOOT ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initSplash();
  updateDeadline();

  // If returning user, skip to app
  const saved = localStorage.getItem('eg_user');
  if (saved) {
    try {
      State.user = JSON.parse(saved);
      // Still show splash but "skip" is pre-populated
    } catch (_) {}
  }
});
