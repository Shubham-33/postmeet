/**
 * Postmeet — frontend behavior.
 *
 * Wires up the input modes (text vs Doc URL), drives the /extract API,
 * renders the Trello board, and builds Google Calendar / Gmail prefill URLs
 * for per-card and bulk distribution.
 */
'use strict';

// ---------- Constants ----------

const SAMPLE_TRANSCRIPT = `Alice: Okay let's kick off. First, the migration deadline. Bob, can you finish the schema rewrite by Friday?
Bob: Yeah I'll have the schema rewrite done by Friday May 9. I'll also send Carol a draft for review on Wednesday.
Alice: Great. Carol, you'll need to update the API docs once Bob ships.
Carol: Got it. I'll update the API docs by next Monday.
Alice: Last thing — we agreed to deprecate the v1 endpoint by end of month. Bob will email customers about it tomorrow.
Bob: I can send carol@example.com and alice@example.com on the deprecation notice draft tonight.
Alice: Perfect. We also decided we're going to skip the staging environment for the v2 rollout — going straight to canary.
Carol: Sounds good.`;

const MIN_TRANSCRIPT_CHARS = 30;
const POPUP_STAGGER_MS = 80; // ms between bulk-open tabs (popup-blocker friendly)
const DEFAULT_DUE_OFFSET_DAYS = 7;
const STATUS_COLORS = {
  info: 'text-slate-300',
  success: 'text-emerald-300',
  error: 'text-rose-300',
};
const OWNER_PALETTES = [
  'bg-indigo-500/10 border-indigo-500/30',
  'bg-emerald-500/10 border-emerald-500/30',
  'bg-fuchsia-500/10 border-fuchsia-500/30',
  'bg-cyan-500/10 border-cyan-500/30',
  'bg-rose-500/10 border-rose-500/30',
];

// ---------- DOM helpers ----------

const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return (s || '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

function setStatus(msg, level) {
  $('status').textContent = msg;
  $('status').className = `text-xs flex-1 ${STATUS_COLORS[level] || STATUS_COLORS.info}`;
}

// ---------- App state ----------

let lastData = null; // last successful extraction, for distribute-all
let mode = 'text'; // 'text' or 'doc'

// ---------- Tabs ----------

function setMode(next) {
  mode = next;
  const isText = next === 'text';
  $('textPanel').classList.toggle('hidden', !isText);
  $('docPanel').classList.toggle('hidden', isText);
  $('tabText').setAttribute('aria-selected', String(isText));
  $('tabDoc').setAttribute('aria-selected', String(!isText));
  $('tabText').className = `text-xs px-3 py-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 ${isText ? 'bg-white/10 text-slate-100' : 'text-slate-300 hover:bg-white/5'}`;
  $('tabDoc').className = `text-xs px-3 py-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 ${!isText ? 'bg-white/10 text-slate-100' : 'text-slate-300 hover:bg-white/5'}`;
  (isText ? $('transcript') : $('docUrl')).focus();
}

function attachShortcut(el) {
  el.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      $('extractBtn').click();
    }
  });
}

// ---------- Extract flow ----------

async function handleExtract() {
  let body;
  if (mode === 'text') {
    const transcript = $('transcript').value.trim();
    if (transcript.length < MIN_TRANSCRIPT_CHARS) {
      setStatus(`Need at least ${MIN_TRANSCRIPT_CHARS} characters.`, 'error');
      return;
    }
    body = { transcript };
  } else {
    const docUrl = $('docUrl').value.trim();
    if (!docUrl.includes('docs.google.com/document/d/')) {
      setStatus("That doesn't look like a Google Doc URL.", 'error');
      return;
    }
    body = { doc_url: docUrl };
  }

  $('extractBtn').disabled = true;
  $('extractBtn').textContent = 'Extracting…';
  setStatus(mode === 'doc' ? 'Fetching Doc…' : 'Calling Gemini…', 'info');
  renderSkeleton();

  try {
    const t0 = Date.now();
    const res = await fetch('/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed');
    const dt = ((Date.now() - t0) / 1000).toFixed(1);
    const aiCount = (data.action_items || []).length;
    const decCount = (data.decisions || []).length;
    setStatus(
      `Extracted in ${dt}s · ${aiCount} action item${aiCount === 1 ? '' : 's'} · ${decCount} decision${decCount === 1 ? '' : 's'}`,
      'success'
    );
    lastData = data;
    renderBoard(data);
  } catch (err) {
    renderError(err.message);
  } finally {
    $('extractBtn').disabled = false;
    $('extractBtn').textContent = 'Extract →';
  }
}

// ---------- Distribute-all ----------

function openAll(kind) {
  if (!lastData || !(lastData.action_items || []).length) return;
  const items = lastData.action_items;
  const n = items.length;
  const ok = confirm(
    `Open ${n} ${kind === 'calendar' ? 'Calendar' : 'Email'} tab${n === 1 ? '' : 's'}? Your browser may ask to allow popups.`
  );
  if (!ok) return;
  items.forEach((item, i) => {
    const url = kind === 'calendar' ? calendarUrl(item) : mailUrl(item);
    setTimeout(() => window.open(url, '_blank', 'noopener'), i * POPUP_STAGGER_MS);
  });
  setStatus(`Opened ${n} ${kind} tab${n === 1 ? '' : 's'}.`, 'success');
}

// ---------- Rendering ----------

function renderSkeleton() {
  const board = $('board');
  board.innerHTML = '';
  for (let i = 0; i < 4; i++) {
    const col = document.createElement('div');
    col.className = 'flex-shrink-0 w-72 bg-white/5 border border-white/10 rounded-xl p-3 animate-pulse';
    col.innerHTML = `
      <div class="h-4 w-20 bg-white/10 rounded mb-3"></div>
      <div class="space-y-2">
        <div class="h-16 bg-white/5 rounded-lg"></div>
        <div class="h-16 bg-white/5 rounded-lg"></div>
      </div>
    `;
    board.appendChild(col);
  }
}

function renderError(msg) {
  $('summarySection').classList.add('hidden');
  const board = $('board');
  board.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'w-full text-center py-16';
  wrap.innerHTML = `
    <p class="text-rose-300 text-sm mb-4">Something went wrong: ${escapeHtml(msg)}</p>
    <button id="retryBtn" type="button" class="text-sm px-4 py-2 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-100 focus:outline-none focus:ring-2 focus:ring-rose-400">Try again</button>
  `;
  board.appendChild(wrap);
  document.getElementById('retryBtn').onclick = () => $('extractBtn').click();
  setStatus('Extraction failed.', 'error');
}

function renderBoard(data) {
  $('summarySection').classList.remove('hidden');
  $('summaryText').textContent = data.summary || '(no summary)';

  const byOwner = {};
  for (const a of data.action_items || []) {
    const key = a.owner || 'Unassigned';
    (byOwner[key] = byOwner[key] || []).push(a);
  }

  const board = $('board');
  board.innerHTML = '';

  board.appendChild(
    makeColumn(
      '📋 Decisions',
      'bg-amber-500/10 border-amber-500/30',
      (data.decisions || []).map((d) => makeDecisionCard(d)),
      (data.decisions || []).length
    )
  );

  const owners = Object.keys(byOwner).sort((a, b) => {
    if (a === 'Unassigned') return 1;
    if (b === 'Unassigned') return -1;
    return a.localeCompare(b);
  });

  owners.forEach((owner, i) => {
    const items = byOwner[owner];
    const palette =
      owner === 'Unassigned'
        ? 'bg-slate-500/10 border-slate-500/30'
        : OWNER_PALETTES[i % OWNER_PALETTES.length];
    const heading = owner === 'Unassigned' ? '❓ Unassigned' : `👤 ${owner}`;
    board.appendChild(makeColumn(heading, palette, items.map((it) => makeActionCard(it)), items.length));
  });

  if (!owners.length && !(data.decisions || []).length) {
    board.innerHTML =
      '<div class="w-full text-center text-slate-500 text-sm py-16">No decisions or action items detected.</div>';
  }
}

function makeColumn(title, paletteClass, cardEls, count) {
  const col = document.createElement('section');
  col.setAttribute('role', 'group');
  col.setAttribute('aria-label', `${title}, ${count} item${count === 1 ? '' : 's'}`);
  col.className = `flex-shrink-0 w-72 ${paletteClass} border rounded-xl p-3`;
  col.innerHTML = `
    <div class="flex items-center justify-between mb-3 px-1">
      <h3 class="text-sm font-semibold text-slate-100">${title}</h3>
      <span class="text-xs text-slate-300 bg-white/10 px-2 py-0.5 rounded-full" aria-hidden="true">${count}</span>
    </div>
    <div class="space-y-2"></div>
  `;
  const stack = col.querySelector('div.space-y-2');
  cardEls.forEach((el) => stack.appendChild(el));
  return col;
}

function makeDecisionCard(text) {
  const card = document.createElement('article');
  card.className = 'card-hover bg-slate-900/70 border border-white/10 rounded-lg p-3 text-sm text-slate-100';
  card.textContent = text;
  return card;
}

function makeActionCard(item) {
  const card = document.createElement('article');
  card.setAttribute('aria-label', `Action: ${item.task}, owner ${item.owner || 'unassigned'}`);
  card.className = 'card-hover bg-slate-900/70 border border-white/10 rounded-lg p-3 space-y-2';
  const due = item.due_date
    ? `<span class="text-xs px-2 py-0.5 rounded bg-amber-400/20 text-amber-200">📅 ${item.due_date}</span>`
    : '';
  const email = item.owner_email
    ? `<span class="text-xs text-slate-300">${escapeHtml(item.owner_email)}</span>`
    : '';
  card.innerHTML = `
    <p class="text-sm text-slate-100 leading-snug">${escapeHtml(item.task)}</p>
    <div class="flex items-center gap-2 flex-wrap">${due}${email}</div>
    <div class="flex gap-2 pt-1">
      <a target="_blank" rel="noopener" href="${calendarUrl(item)}"
         aria-label="Open Calendar prefill for: ${escapeHtml(item.task)}"
         class="flex-1 text-center text-xs px-2 py-1.5 rounded bg-indigo-500/30 hover:bg-indigo-500/50 text-indigo-100 focus:outline-none focus:ring-2 focus:ring-indigo-400">📅 Calendar</a>
      <a target="_blank" rel="noopener" href="${mailUrl(item)}"
         aria-label="Open Gmail compose for: ${escapeHtml(item.task)}"
         class="flex-1 text-center text-xs px-2 py-1.5 rounded bg-fuchsia-500/30 hover:bg-fuchsia-500/50 text-fuchsia-100 focus:outline-none focus:ring-2 focus:ring-fuchsia-400">✉️ Email</a>
    </div>
  `;
  return card;
}

// ---------- URL builders (Google Calendar / Gmail prefill) ----------

function calendarUrl(item) {
  const date = item.due_date || defaultDate();
  const start = date.replace(/-/g, '') + 'T090000Z';
  const end = date.replace(/-/g, '') + 'T100000Z';
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: `[Postmeet] ${item.task}`,
    dates: `${start}/${end}`,
    details: `Action item assigned to ${item.owner || 'Unassigned'} via Postmeet.`,
  });
  if (item.owner_email) params.append('add', item.owner_email);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

function mailUrl(item) {
  const to = item.owner_email || '';
  const subject = `Action item: ${item.task}`;
  const body = `Hi ${item.owner || 'there'},\n\nFrom our meeting — you're on the hook for:\n\n  • ${item.task}${item.due_date ? `\n  • Due: ${item.due_date}` : ''}\n\nSent via Postmeet.`;
  const params = new URLSearchParams({ view: 'cm', fs: '1', tf: '1', to, su: subject, body });
  return `https://mail.google.com/mail/?${params.toString()}`;
}

function defaultDate() {
  const d = new Date();
  d.setDate(d.getDate() + DEFAULT_DUE_OFFSET_DAYS);
  return d.toISOString().slice(0, 10);
}

// ---------- Bootstrap ----------

document.addEventListener('DOMContentLoaded', () => {
  $('loadSample').onclick = () => {
    $('transcript').value = SAMPLE_TRANSCRIPT;
    $('transcript').focus();
  };
  $('tabText').onclick = () => setMode('text');
  $('tabDoc').onclick = () => setMode('doc');
  attachShortcut($('transcript'));
  attachShortcut($('docUrl'));
  $('extractBtn').onclick = handleExtract;
  $('distributeCalBtn').onclick = () => openAll('calendar');
  $('distributeMailBtn').onclick = () => openAll('mail');
});
