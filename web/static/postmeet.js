/**
 * Postmeet — frontend behavior.
 *
 * Wires up the input modes (paste / Doc URL / file upload), drives the
 * /extract API, renders an editable Trello board, and builds Google
 * Calendar / Gmail prefill URLs for per-card and bulk distribution.
 *
 * Features:
 *   • Paste text · Google Doc URL · file upload (txt/md, drag-drop)
 *   • Inline editing of every action-item field
 *   • localStorage persistence with restore prompt
 *   • Per-card and bulk Calendar/Gmail prefill
 *   • MOM (Minutes of Meeting) email + clipboard copy
 *   • Toast notifications for non-blocking confirmations
 *   • Keyboard shortcuts (⌘+Enter, ?, Esc)
 */
'use strict';

// ---------- Constants ----------

const SAMPLE_TRANSCRIPTS = {
  standup: {
    label: 'Standup',
    text: `Priya: Quick standup, let's go around. Marcus, what's on you?
Marcus: I'm closing out the auth refactor. I'll have the PR ready by Friday May 22 — marcus@example.com if anyone wants to review early.
Priya: Great. Tara, you?
Tara: I'm blocked on the design-system tokens. I'll ping Jamie about merging that branch today.
Jamie: Yeah I can get to that this afternoon. I'll merge by end of day and tag Tara on Slack.
Priya: Perfect. I noticed we're falling behind on QA — I'll set up a dedicated QA channel by tomorrow and pull Jamie in to triage open bugs.
Tara: We also need to decide if we're shipping the dark mode toggle in this release.
Marcus: I'd say yes — it's only two days of work.
Priya: Agreed. We'll include dark mode in the v3 release.
Jamie: Cool, I can take that. I'll have it ready by Wednesday May 27.
Priya: One more thing — we're moving the demo to Friday afternoon instead of Thursday morning. I'll send out the calendar update.`,
  },
  planning: {
    label: 'Planning',
    text: `Sarah: Let's talk Q3 priorities. Top of the list is the customer health score. Diego, where are we?
Diego: We have three drafts. I'll narrow it down to one by Wednesday June 3 and circulate to the team. diego@example.com is best for direct feedback.
Sarah: Good. Once we agree on the metric, Lin needs to wire it into the dashboard.
Lin: Yeah, I'll have the dashboard implementation done within two weeks of the metric being finalized.
Sarah: Second priority — onboarding. We're losing 40% of users in the first 7 days. We agreed last week to rebuild the empty-state experience. Karim, that's yours.
Karim: I'll have a clickable Figma prototype ready by Friday June 5, then hand off to Lin for implementation.
Sarah: Lin, can you commit to shipping the new onboarding by end of June?
Lin: Tight but doable. I'll commit to June 30. lin@example.com if anyone needs to file bugs.
Sarah: Perfect. Third priority — the SOC 2 audit. Diego will lead that.
Diego: I'll start the kickoff with the auditor next Monday June 8.
Sarah: We also decided we're delaying the API v2 launch from July to August so we can focus on these three priorities.`,
  },
  retro: {
    label: 'Retro',
    text: `Avi: Sprint retro. What went well, what didn't, what to change?
Mei: The new CI pipeline cut deploy time from 12 to 4 minutes. Big win.
Daniel: Agreed. But we had two hotfixes this sprint that should have been caught in QA.
Avi: I'll write up a postmortem on the hotfix patterns by Thursday May 28 — daniel@example.com let me know if I miss anything.
Mei: I'll add a regression test for the auth bug specifically by next Tuesday.
Daniel: We agreed last sprint to start using feature flags for risky changes — but no one used them. Avi, can we make this a hard requirement?
Avi: Yes. We're now requiring feature flags for any change touching billing or auth. I'll update the team handbook by end of week.
Mei: One more thing — I want to propose pair programming Wednesdays. Two hours, optional.
Daniel: I'm in.
Avi: Let's try it. We'll start next Wednesday.`,
  },
};

const MIN_TRANSCRIPT_CHARS = 30;
const POPUP_STAGGER_MS = 80;
const DEFAULT_DUE_OFFSET_DAYS = 7;
const MAX_FILE_BYTES = 200 * 1024;
const STORAGE_KEY = 'postmeet:lastData:v1';
const STORAGE_TTL_DAYS = 7;

const STATUS_COLORS = {
  info: 'text-stone-600',
  success: 'text-ink',
  error: 'text-red-700',
};

const OWNER_PALETTES = [
  { stripe: 'border-l-[3px] border-l-[#5C7A6E]', avatarBg: '#5C7A6E' },
  { stripe: 'border-l-[3px] border-l-[#3D5A6C]', avatarBg: '#3D5A6C' },
  { stripe: 'border-l-[3px] border-l-[#8B6F47]', avatarBg: '#8B6F47' },
  { stripe: 'border-l-[3px] border-l-[#6B7A5A]', avatarBg: '#6B7A5A' },
  { stripe: 'border-l-[3px] border-l-[#9B7B6E]', avatarBg: '#9B7B6E' },
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

const COL_BASE_CLASSES = 'flex-shrink-0 w-72 bg-white border border-line p-4';

// ---------- App state ----------

let lastData = null;
// Auto-detected from input content. 'text' (raw transcript) | 'doc' (URL pasted) |
// 'file' (uploaded file content already in textarea).
let detectedMode = 'text';
let uploadedFileName = '';

const DOC_URL_RE = /https?:\/\/docs\.google\.com\/document\/d\/[\w-]+/;

// ---------- Persistence (localStorage) ----------

function persist() {
  if (!lastData) return;
  try {
    const blob = JSON.stringify({ data: lastData, savedAt: Date.now() });
    localStorage.setItem(STORAGE_KEY, blob);
  } catch (_) {
    /* quota or disabled — fail silently */
  }
}

function loadPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const blob = JSON.parse(raw);
    const ageMs = Date.now() - (blob.savedAt || 0);
    if (ageMs > STORAGE_TTL_DAYS * 24 * 60 * 60 * 1000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return blob;
  } catch (_) {
    return null;
  }
}

function clearPersisted() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (_) {}
}

function maybeRestoreSession() {
  const blob = loadPersisted();
  if (!blob || !blob.data) return;
  const ageMin = Math.round((Date.now() - blob.savedAt) / 60000);
  const ago = ageMin < 60 ? `${ageMin}m ago` : ageMin < 1440 ? `${Math.round(ageMin / 60)}h ago` : `${Math.round(ageMin / 1440)}d ago`;
  showToast({
    message: `Restore last session? (saved ${ago})`,
    actions: [
      {
        label: 'Restore',
        onClick: () => {
          lastData = blob.data;
          renderBoard(lastData);
          setStatus('Session restored.', 'success');
        },
      },
      {
        label: 'Discard',
        onClick: () => clearPersisted(),
      },
    ],
    sticky: true,
  });
}

// ---------- Mode detection (auto from textarea content) ----------

function detectMode() {
  const text = $('transcript').value.trim();
  // If a file has been loaded, the textarea is filled with its contents and
  // detectedMode is set to 'file' explicitly. Once the user edits it, fall
  // through to text/doc detection.
  if (detectedMode === 'file' && text === $('transcript').dataset.fileContent) {
    return 'file';
  }
  // Detect Google Doc URL only if the entire input is essentially a URL
  // (a couple of words around it is fine, but mostly URL-shaped).
  if (DOC_URL_RE.test(text) && text.length < 250 && !text.includes('\n\n')) {
    return 'doc';
  }
  return 'text';
}

function updateInputModeHint() {
  const mode = detectMode();
  const hint = $('inputModeHint');
  if (mode === 'doc') {
    hint.textContent = 'Detected: Google Doc URL';
    hint.classList.remove('hidden');
  } else if (mode === 'file' && uploadedFileName) {
    hint.textContent = `Detected: ${uploadedFileName}`;
    hint.classList.remove('hidden');
  } else {
    hint.classList.add('hidden');
  }
}

function attachShortcut(el) {
  el.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      $('extractBtn').click();
    }
  });
}

// ---------- File upload + drag-and-drop ----------

function handleFileSelected(file) {
  if (!file) return;
  if (file.size > MAX_FILE_BYTES) {
    setStatus(`File too large (${Math.round(file.size / 1024)} KB > 200 KB cap).`, 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    const content = String(reader.result || '');
    const ta = $('transcript');
    ta.value = content;
    ta.dataset.fileContent = content; // marker so detectMode() can identify file mode
    uploadedFileName = file.name;
    detectedMode = 'file';
    setStatus(`Loaded ${file.name} (${Math.round(file.size / 1024)} KB).`, 'success');
    updateInputModeHint();
  };
  reader.onerror = () => {
    setStatus("Couldn't read that file. Make sure it's plain text.", 'error');
  };
  reader.readAsText(file);
}

function setupDragAndDrop() {
  let depth = 0;
  const overlay = $('dropOverlay');
  const allowed = /\.(txt|md)$/i;

  document.addEventListener('dragenter', (e) => {
    if (!Array.from(e.dataTransfer?.types || []).includes('Files')) return;
    depth++;
    overlay.classList.remove('hidden');
  });
  document.addEventListener('dragleave', () => {
    depth = Math.max(0, depth - 1);
    if (depth === 0) overlay.classList.add('hidden');
  });
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    depth = 0;
    overlay.classList.add('hidden');
    const file = e.dataTransfer?.files?.[0];
    if (!file) return;
    if (!allowed.test(file.name)) {
      setStatus(`Only .txt and .md files are supported (got ${file.name}).`, 'error');
      return;
    }
    handleFileSelected(file);
  });
}

// ---------- Extract flow ----------

async function handleExtract() {
  const text = $('transcript').value.trim();
  if (text.length < MIN_TRANSCRIPT_CHARS) {
    setStatus(`Need at least ${MIN_TRANSCRIPT_CHARS} characters.`, 'error');
    return;
  }
  const mode = detectMode();
  let body;
  if (mode === 'doc') {
    // Extract just the Doc URL from the textarea (in case there's surrounding whitespace).
    const match = text.match(DOC_URL_RE);
    body = { doc_url: match ? match[0] : text };
  } else {
    body = { transcript: text };
  }

  $('extractBtn').disabled = true;
  $('extractBtn').textContent = 'Extracting…';
  setStatus(mode === 'doc' ? 'Fetching Google Doc…' : 'Calling Gemini…', 'info');
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
      `Extracted in ${dt}s · ${aiCount} action item${aiCount === 1 ? '' : 's'} · ${decCount} decision${decCount === 1 ? '' : 's'} · click any field to edit`,
      'success'
    );
    lastData = data;
    persist();
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

  // Calendar = one event per task (each task is a separate calendar slot).
  // Email = one consolidated email per owner (all of their tasks in one message).
  let urls = [];
  let label = '';
  if (kind === 'calendar') {
    urls = items.map(calendarUrl);
    label = `${urls.length} Calendar tab${urls.length === 1 ? '' : 's'}`;
  } else {
    const byOwner = {};
    items.forEach((it) => {
      const k = it.owner || 'Unassigned';
      (byOwner[k] = byOwner[k] || []).push(it);
    });
    urls = Object.entries(byOwner).map(([owner, list]) => ownerMailUrl(owner, list));
    const owners = Object.keys(byOwner);
    label = `${owners.length} Email tab${owners.length === 1 ? '' : 's'} (one per person${owners.length === items.length ? '' : `, covers ${items.length} task${items.length === 1 ? '' : 's'}`})`;
  }

  showToast({
    message: `Open ${label}? Browser may block popups.`,
    actions: [
      {
        label: 'Open all',
        primary: true,
        onClick: () => {
          urls.forEach((url, i) => {
            setTimeout(() => window.open(url, '_blank', 'noopener'), i * POPUP_STAGGER_MS);
          });
          setStatus(`Opened ${label}.`, 'success');
        },
      },
      { label: 'Cancel' },
    ],
  });
}

// ---------- Rendering ----------

function renderSkeleton() {
  const board = $('board');
  board.innerHTML = '';
  // Show one column with 3 card skeletons (vs 4 columns) — communicates the
  // shape of incoming data more honestly.
  const col = document.createElement('div');
  col.className = `${COL_BASE_CLASSES} animate-pulse`;
  col.innerHTML = `
    <div class="flex items-baseline justify-between mb-4 pb-3 border-b border-line">
      <div class="h-3 w-24 bg-line"></div>
      <div class="h-3 w-6 bg-line"></div>
    </div>
    <div class="space-y-3">
      ${Array.from({ length: 3 }, () => `
        <div class="bg-cream border border-line p-3 space-y-2">
          <div class="h-3 bg-line w-full"></div>
          <div class="h-3 bg-line w-2/3"></div>
          <div class="h-2 bg-line w-1/2 mt-3"></div>
        </div>
      `).join('')}
    </div>
  `;
  board.appendChild(col);
}

function renderError(msg) {
  $('summarySection').classList.add('hidden');
  const board = $('board');
  board.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'w-full text-center py-16 border border-line bg-white';
  wrap.innerHTML = `
    <p class="text-red-700 text-sm mb-4">Something went wrong: ${escapeHtml(msg)}</p>
    <button id="retryBtn" type="button" class="text-sm px-4 py-2 border border-ink text-ink hover:bg-ink hover:text-cream transition-colors focus:outline-none focus:ring-2 focus:ring-ink">Try again</button>
  `;
  board.appendChild(wrap);
  document.getElementById('retryBtn').onclick = () => $('extractBtn').click();
  setStatus('Extraction failed.', 'error');
}

function renderBoard(data) {
  $('summarySection').classList.remove('hidden');
  $('summaryText').textContent = data.summary || '(no summary)';

  const byOwner = {};
  (data.action_items || []).forEach((a, idx) => {
    const key = a.owner || 'Unassigned';
    (byOwner[key] = byOwner[key] || []).push({ item: a, idx });
  });

  const board = $('board');
  board.innerHTML = '';

  board.appendChild(
    makeColumn(
      'Decisions',
      'border-l-[3px] border-l-ember-500',
      null, // no avatar for decisions
      (data.decisions || []).map((d, i) => makeDecisionCard(d, i)),
      (data.decisions || []).length
    )
  );

  const owners = Object.keys(byOwner).sort((a, b) => {
    if (a === 'Unassigned') return 1;
    if (b === 'Unassigned') return -1;
    return a.localeCompare(b);
  });

  owners.forEach((owner, i) => {
    const entries = byOwner[owner];
    const palette =
      owner === 'Unassigned'
        ? { stripe: 'border-l-[3px] border-l-stone-400', avatarBg: '#A8A095' }
        : OWNER_PALETTES[hashIndex(owner, OWNER_PALETTES.length)];
    board.appendChild(
      makeColumn(owner, palette.stripe, palette.avatarBg, entries.map(({ item, idx }) => makeActionCard(item, idx)), entries.length)
    );
  });

  if (!owners.length && !(data.decisions || []).length) {
    board.innerHTML =
      '<div class="w-full text-center text-stone-500 text-sm py-16 border border-line bg-white">No decisions or action items detected.</div>';
  }
}

function hashIndex(str, mod) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h % mod;
}

function initials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function makeColumn(title, stripeClass, avatarBg, cardEls, count) {
  const col = document.createElement('section');
  col.setAttribute('role', 'group');
  col.setAttribute('aria-label', `${title}, ${count} item${count === 1 ? '' : 's'}`);
  col.className = `${COL_BASE_CLASSES} ${stripeClass}`;
  const avatarHtml = avatarBg
    ? `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full text-[11px] font-semibold text-white flex-shrink-0" style="background:${avatarBg}" aria-hidden="true">${escapeHtml(initials(title))}</span>`
    : '';
  col.innerHTML = `
    <div class="flex items-center justify-between mb-4 pb-3 border-b border-line">
      <div class="flex items-center gap-2 min-w-0">
        ${avatarHtml}
        <h3 class="text-base font-semibold text-ink truncate">${escapeHtml(title)}</h3>
      </div>
      <span class="text-sm text-stone-700 font-mono flex-shrink-0" aria-hidden="true">${String(count).padStart(2, '0')}</span>
    </div>
    <div class="space-y-3"></div>
  `;
  const stack = col.querySelector('div.space-y-3');
  cardEls.forEach((el) => stack.appendChild(el));
  return col;
}

function makeDecisionCard(text, idx) {
  const card = document.createElement('article');
  card.className = 'card-hover bg-cream border border-line p-3 text-sm text-ink leading-snug';
  card.innerHTML = `<span class="editable" data-decision="${idx}" tabindex="0" role="button" aria-label="Click to edit decision">${escapeHtml(text)}</span>`;
  return card;
}

function makeActionCard(item, idx) {
  const card = document.createElement('article');
  card.setAttribute('aria-label', `Action: ${item.task}, owner ${item.owner || 'unassigned'}`);
  card.className = 'card-hover bg-paper border border-line p-3 space-y-2';
  const due = item.due_date
    ? `<span class="editable text-xs text-ember-600 font-medium" data-idx="${idx}" data-field="due_date" tabindex="0" role="button" aria-label="Edit due date">${escapeHtml(formatDate(item.due_date))}</span>`
    : `<span class="editable text-xs text-stone-600 italic" data-idx="${idx}" data-field="due_date" tabindex="0" role="button" aria-label="Add due date">+ add date</span>`;
  const email = item.owner_email
    ? `<span class="editable text-xs text-stone-700 font-mono truncate" data-idx="${idx}" data-field="owner_email" tabindex="0" role="button" aria-label="Edit email">${escapeHtml(item.owner_email)}</span>`
    : `<span class="editable text-xs text-stone-600 italic" data-idx="${idx}" data-field="owner_email" tabindex="0" role="button" aria-label="Add email">+ add email</span>`;
  const context = item.context
    ? `<p><span class="editable text-xs text-stone-600 italic leading-snug" data-idx="${idx}" data-field="context" tabindex="0" role="button" aria-label="Edit context">${escapeHtml(item.context)}</span></p>`
    : `<p><span class="editable text-xs text-stone-600 italic" data-idx="${idx}" data-field="context" tabindex="0" role="button" aria-label="Add context">+ add context</span></p>`;
  card.innerHTML = `
    <p>
      <span class="editable text-sm text-ink leading-snug" data-idx="${idx}" data-field="task" tabindex="0" role="button" aria-label="Edit task">${escapeHtml(item.task)}</span>
    </p>
    ${context}
    <div class="flex items-center gap-3 flex-wrap pt-1 border-t border-line/60">${due}${email}</div>
    <div class="flex gap-2 pt-1">
      <a target="_blank" rel="noopener" href="${calendarUrl(item)}"
         aria-label="Open Calendar prefill for: ${escapeHtml(item.task)}"
         class="flex-1 text-center text-xs px-2 py-1.5 border border-line text-stone-600 hover:border-ink hover:text-ink transition-colors focus:outline-none focus:ring-2 focus:ring-ink">Calendar →</a>
      <a target="_blank" rel="noopener" href="${mailUrl(item)}"
         aria-label="Open Gmail compose for: ${escapeHtml(item.task)}"
         class="flex-1 text-center text-xs px-2 py-1.5 border border-line text-stone-600 hover:border-ink hover:text-ink transition-colors focus:outline-none focus:ring-2 focus:ring-ink">Email →</a>
    </div>
  `;
  return card;
}

// ---------- Inline editing (event delegation on the board) ----------

function setupInlineEditing() {
  const board = $('board');
  board.addEventListener('click', onEditableActivate);
  board.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      const t = e.target;
      if (t.classList && t.classList.contains('editable')) {
        e.preventDefault();
        onEditableActivate(e);
      }
    }
  });
}

function onEditableActivate(e) {
  const target = e.target;
  if (!target.classList || !target.classList.contains('editable')) return;
  if (target.dataset.editing === '1') return; // already in edit mode
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;
  startEdit(target);
}

function startEdit(span) {
  const idx = span.dataset.idx !== undefined ? Number(span.dataset.idx) : null;
  const field = span.dataset.field || null;
  const decisionIdx = span.dataset.decision !== undefined ? Number(span.dataset.decision) : null;

  let currentValue;
  if (decisionIdx !== null) {
    currentValue = (lastData?.decisions || [])[decisionIdx] || '';
  } else if (idx !== null && field) {
    const item = (lastData?.action_items || [])[idx] || {};
    currentValue = field === 'due_date' ? (item.due_date || '') : (item[field] || '');
  } else {
    return;
  }

  const useTextarea = field === 'task' || field === 'context' || decisionIdx !== null;
  const input = document.createElement(useTextarea ? 'textarea' : 'input');
  input.value = currentValue;
  if (!useTextarea) {
    input.type = field === 'due_date' ? 'date' : field === 'owner_email' ? 'email' : 'text';
  }
  input.className = 'w-full bg-white border border-ink p-2 text-xs text-ink focus:outline-none';
  if (useTextarea) input.rows = 2;
  span.dataset.editing = '1';
  span.replaceWith(input);
  input.focus();
  if (input.select) input.select();

  const finish = (commit) => {
    const newValue = commit ? input.value.trim() : currentValue;
    if (decisionIdx !== null) {
      lastData.decisions[decisionIdx] = newValue;
    } else if (idx !== null && field) {
      lastData.action_items[idx][field] = newValue;
      // If owner changed, the board grouping changes — full rerender.
    }
    persist();
    renderBoard(lastData);
  };

  input.addEventListener('blur', () => finish(true));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      finish(false);
    } else if (e.key === 'Enter' && !e.shiftKey && !useTextarea) {
      e.preventDefault();
      finish(true);
    } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && useTextarea) {
      e.preventDefault();
      finish(true);
    }
  });
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
    details: `Action item assigned to ${item.owner || 'Unassigned'} via Postmeet.${item.context ? `\n\nContext: ${item.context}` : ''}`,
  });
  if (item.owner_email) params.append('add', item.owner_email);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

/**
 * Build a single Gmail compose URL addressed to one owner, containing ALL
 * of their action items from the current meeting. One email per person,
 * not one per task.
 */
function ownerMailUrl(owner, items) {
  if (!items || !items.length) return '';
  const to = items.find((i) => i.owner_email)?.owner_email || '';
  const greeting = owner && owner !== 'Unassigned' ? owner : 'there';
  const subject =
    items.length === 1
      ? `Action item from our meeting — ${items[0].task}`
      : `${items.length} action items from our meeting`;
  const lines = [
    `Hi ${greeting},`,
    '',
    items.length === 1
      ? `Quick follow-up from our meeting. You agreed to take on the following:`
      : `Quick follow-up from our meeting. You agreed to take on the following ${items.length} items:`,
    '',
  ];
  items.forEach((item, i) => {
    if (items.length > 1) lines.push(`${i + 1}. ${item.task}`);
    else lines.push(`  • Task: ${item.task}`);
    if (item.due_date) {
      lines.push(items.length > 1 ? `   Due: ${formatDate(item.due_date)}` : `  • Due: ${formatDate(item.due_date)}`);
    }
    if (item.context) {
      lines.push(items.length > 1 ? `   Context: ${item.context}` : '');
      if (items.length === 1) lines.push(`Context: ${item.context}`);
    }
    if (items.length > 1) lines.push('');
  });
  lines.push(
    `If anything's unclear or needs to be re-scoped, reply here before the due date${items.length > 1 ? 's' : ''} and we'll sort it out.`
  );
  lines.push('', `Thanks,`, `(Sent via Postmeet)`);
  const body = lines.join('\n');
  const params = new URLSearchParams({ view: 'cm', fs: '1', tf: '1', to, su: subject, body });
  return `https://mail.google.com/mail/?${params.toString()}`;
}

/**
 * Per-card email button: open the consolidated email for THIS card's owner
 * (which includes all their other tasks too). Same URL whether you click
 * any of Bob's 4 cards.
 */
function mailUrl(item) {
  if (!lastData) return ownerMailUrl(item.owner, [item]);
  const owner = item.owner || 'Unassigned';
  const allOwnerItems = (lastData.action_items || []).filter(
    (i) => (i.owner || 'Unassigned') === owner
  );
  return ownerMailUrl(owner, allOwnerItems.length ? allOwnerItems : [item]);
}

// ---------- MOM (Minutes of Meeting) ----------

function buildMomBody(data) {
  const items = data.action_items || [];
  const decisions = data.decisions || [];
  const summary = data.summary || '';
  const lines = [
    `Hi team,`,
    '',
    `Sharing the MOM from today's meeting for everyone's reference.`,
    '',
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    `📝 SUMMARY`,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    summary || '(no summary)',
  ];
  if (decisions.length) {
    lines.push('', `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, `📋 DECISIONS (${decisions.length})`, `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    decisions.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (items.length) {
    lines.push('', `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, `✅ ACTION ITEMS (${items.length})`, `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    const byOwner = {};
    items.forEach((it) => {
      const k = it.owner || 'Unassigned';
      (byOwner[k] = byOwner[k] || []).push(it);
    });
    Object.keys(byOwner)
      .sort((a, b) => (a === 'Unassigned' ? 1 : b === 'Unassigned' ? -1 : a.localeCompare(b)))
      .forEach((owner) => {
        lines.push('', `▸ ${owner}${byOwner[owner][0].owner_email ? ` (${byOwner[owner][0].owner_email})` : ''}`);
        byOwner[owner].forEach((it) => {
          const due = it.due_date ? `  [due ${formatDate(it.due_date)}]` : '';
          lines.push(`   • ${it.task}${due}`);
          if (it.context) lines.push(`     ↳ ${it.context}`);
        });
      });
  }
  lines.push('', `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  lines.push(`If your name appears under Action Items, you'll also get an individual email with the calendar invite. Reply-all if anything below is wrong.`);
  lines.push('', `(Sent via Postmeet)`);
  return lines.join('\n');
}

function momEmailUrl(data) {
  const items = data.action_items || [];
  const recipients = Array.from(
    new Set(items.map((i) => (i.owner_email || '').trim()).filter(Boolean))
  );
  const today = formatDate(new Date().toISOString().slice(0, 10));
  const subject = `Minutes of Meeting — ${today}`;
  const body = buildMomBody(data);
  const params = new URLSearchParams({ view: 'cm', fs: '1', tf: '1', to: recipients.join(','), su: subject, body });
  return `https://mail.google.com/mail/?${params.toString()}`;
}

function sendMOM() {
  if (!lastData) return;
  const items = lastData.action_items || [];
  const recipients = Array.from(
    new Set(items.map((i) => (i.owner_email || '').trim()).filter(Boolean))
  );
  const open = () => {
    window.open(momEmailUrl(lastData), '_blank', 'noopener');
    setStatus(`Opened MOM draft for ${recipients.length} recipient${recipients.length === 1 ? '' : 's'}.`, 'success');
  };
  if (!recipients.length) {
    showToast({
      message: 'No emails extracted, MOM will open with empty To field. Continue?',
      actions: [
        { label: 'Open anyway', primary: true, onClick: open },
        { label: 'Cancel' },
      ],
    });
  } else {
    open();
  }
}

async function copyMOM() {
  if (!lastData) return;
  const text = buildMomBody(lastData);
  try {
    await navigator.clipboard.writeText(text);
    setStatus('MOM copied to clipboard.', 'success');
  } catch (_) {
    setStatus("Couldn't access clipboard — try the Email button.", 'error');
  }
}

// ---------- Date formatting ----------

function formatDate(isoDate) {
  if (!isoDate) return '';
  const d = new Date(isoDate + 'T00:00:00');
  if (isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

function defaultDate() {
  const d = new Date();
  d.setDate(d.getDate() + DEFAULT_DUE_OFFSET_DAYS);
  return d.toISOString().slice(0, 10);
}

// ---------- Toasts (replace native confirm) ----------

function showToast({ message, actions = [], sticky = false, durationMs = 6000 }) {
  const container = $('toastContainer');
  const toast = document.createElement('div');
  toast.className =
    'pointer-events-auto bg-ink text-cream px-4 py-3 shadow-lg max-w-sm flex items-start gap-3 animate-fade-in';
  toast.setAttribute('role', 'status');
  const text = document.createElement('p');
  text.className = 'text-sm flex-1 leading-snug';
  text.textContent = message;
  toast.appendChild(text);

  const dismiss = () => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  };

  if (actions.length) {
    const btnRow = document.createElement('div');
    btnRow.className = 'flex flex-col gap-1 flex-shrink-0';
    actions.forEach((a) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = a.label;
      btn.className = a.primary
        ? 'text-xs px-3 py-1 bg-ember-500 hover:bg-ember-600 text-white font-medium focus:outline-none focus:ring-2 focus:ring-ember-400'
        : 'text-xs px-3 py-1 border border-cream/30 text-cream hover:bg-cream/10 focus:outline-none focus:ring-2 focus:ring-cream/40';
      btn.onclick = () => {
        try {
          a.onClick?.();
        } finally {
          dismiss();
        }
      };
      btnRow.appendChild(btn);
    });
    toast.appendChild(btnRow);
  } else {
    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = '×';
    close.className = 'text-cream/60 hover:text-cream text-lg leading-none';
    close.setAttribute('aria-label', 'Dismiss');
    close.onclick = dismiss;
    toast.appendChild(close);
  }

  container.appendChild(toast);
  if (!sticky) setTimeout(dismiss, durationMs);
}

// ---------- Keyboard shortcuts modal ----------

function setupGlobalShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      $('shortcutsModal').classList.add('hidden');
      return;
    }
    // Don't trigger ? when user is typing in an input/textarea
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea') return;
    if (e.key === '?' || (e.shiftKey && e.key === '/')) {
      e.preventDefault();
      $('shortcutsModal').classList.toggle('hidden');
    }
  });
}

// ---------- Sample dropdown ----------

function setupSampleMenu() {
  const btn = $('loadSample');
  const menu = $('sampleMenu');
  btn.onclick = (e) => {
    e.stopPropagation();
    menu.classList.toggle('hidden');
  };
  menu.querySelectorAll('[data-sample]').forEach((el) => {
    el.onclick = () => {
      const key = el.dataset.sample;
      $('transcript').value = SAMPLE_TRANSCRIPTS[key].text;
      $('transcript').focus();
      menu.classList.add('hidden');
      setStatus(`Loaded sample: ${SAMPLE_TRANSCRIPTS[key].label}.`, 'info');
    };
  });
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && e.target !== btn) menu.classList.add('hidden');
  });
}

// ---------- Bootstrap ----------

document.addEventListener('DOMContentLoaded', () => {
  setupSampleMenu();
  $('fileInput').addEventListener('change', (e) => handleFileSelected(e.target.files[0]));
  attachShortcut($('transcript'));
  $('transcript').addEventListener('input', updateInputModeHint);
  $('extractBtn').onclick = handleExtract;
  $('momBtn').onclick = sendMOM;
  $('copyMomBtn').onclick = copyMOM;
  $('distributeCalBtn').onclick = () => openAll('calendar');
  $('distributeMailBtn').onclick = () => openAll('mail');
  $('shortcutsClose').onclick = () => $('shortcutsModal').classList.add('hidden');
  setupDragAndDrop();
  setupInlineEditing();
  setupGlobalShortcuts();
  maybeRestoreSession();
});
