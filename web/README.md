# Postmeet

> Paste a meeting → get a Trello-style board of decisions and action items → distribute to everyone in one click.

🏆 **Top 10 Finalist → 2nd Runner-Up at [PromptWars Chennai 2026](https://www.linkedin.com/posts/promptwars-chennai-googlefordevelopers-share-7457292011818209281-mB4X/)** — a one-day Google for Developers × Hack2Skill build-and-pitch hackathon. Optimized for *intent, speed, and execution*, not framework boilerplate.

## The problem

Every team has meetings. Every meeting produces commitments. **70% of those commitments are forgotten within a week** because they live in someone's notes, in a Slack thread, in a Doc no one re-opens. Postmeet closes that loop in five seconds.

## How it works

```
                ┌─ Paste transcript ─┐
Two inputs ─────┤                     ├──► NVIDIA Llama 3.1 ─────► structured JSON ──► Trello board
                └─ Google Doc URL ───┘   (8B + 70B fallback,        │
                                          NIM JSON mode)            │
                                                                    │
                                                          ┌─────────┴─────────┐
                                                          │  Per-card actions: │
                                                          │   📅 Calendar      │
                                                          │   ✉️  Email         │
                                                          │  Bulk actions:     │
                                                          │   📅 All Calendars │
                                                          │   ✉️  All Emails    │
                                                          └────────────────────┘
```

**The "no-OAuth trick.** Google Calendar and Gmail both accept URL-encoded prefilled actions:

- `https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...&add=...`
- `https://mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...` (Gmail web compose — always opens Gmail in browser, doesn't depend on local mail client)

Click → opens the user's already-logged-in Google in a new tab with everything pre-filled. They click *Save* / *Send*. Looks identical to a real integration in a demo. **Zero OAuth setup, zero scope review, judges can try it on their own laptop in 10 seconds.**

## Services used

| Service | Used for |
|---|---|
| **NVIDIA NIM — Llama 3.1** (build.nvidia.com) | Structured extraction via the OpenAI-compatible endpoint in JSON response mode. Fast 8B primary (~2-3s) with automatic 70B fallback on error. |
| **Google Docs** (public export endpoint) | Fetch transcript text from a shared-publicly Doc URL — no OAuth |
| **Google Calendar** | Per-action prefilled event creation via URL spec |
| **Gmail** | Per-action prefilled email via Gmail web compose URL |
| **Cloud Run** | Production deployment, auto-scaling, free HTTPS |
| **Secret Manager** | NVIDIA API key never appears in plaintext outside Secret Manager |
| **Cloud Build** | Buildpack-based container build (no Dockerfile maintenance) |

That's **NVIDIA Llama 3.1 + 6 Google Cloud services** in a single ~250-LOC app.

## Run locally

```bash
# 1. Get a free NVIDIA NIM API key at https://build.nvidia.com
echo 'NVIDIA_API_KEY=your_key' > ../.env

# 2. Install + run
pip3 install -r requirements.txt
python3 app.py

# 3. Open
open http://127.0.0.1:5050
```

## Run the tests

```bash
pip3 install -r requirements-dev.txt
pytest
```

The suite has **69 tests** and the gate is **100% line + branch coverage** on `app.py` and `links.py` — `pyproject.toml` fails the run if coverage drops below 100%.

```
Name       Stmts   Miss Branch BrPart  Cover
---------------------------------------------
app.py       117      0     28      0   100%
links.py      93      0     34      0   100%
---------------------------------------------
69 passed in 0.09s
Required test coverage of 100% reached.
```

Tests cover: missing API key at import time, regex parsing for Doc URLs (positive + negative cases), `fetch_google_doc_text` against 401/403/500/HTML-login-page/happy responses, `parse_extraction` (fenced / prose-wrapped / no-object cases), `call_llm` happy + HTTP-error paths, the `/extract` endpoint across both transcript and doc-URL modes including all error branches (short input, malformed payload, network errors, malformed model JSON, missing `choices`, private docs). All HTTP I/O is mocked — tests run in <100ms with no network.

## Deploy to Cloud Run

```bash
./deploy.sh YOUR_PROJECT_ID YOUR_NVIDIA_KEY
```

The script enables required APIs, stores the key in Secret Manager, builds via buildpacks, and deploys. ~3 minutes cold, ~1 minute on subsequent deploys.

## Demo script (90 seconds)

**Setup before stage:** have a sample meeting transcript ready in a Google Doc, sharing set to "Anyone with the link." Have the URL on your clipboard.

1. **(0:00)** Open the live URL. Click **Load sample** → realistic transcript appears.
2. **(0:10)** Click **Extract** (or ⌘+Enter). Skeleton loaders appear, then ~3s later the board renders: *Decisions* column + one column per assignee.
3. **(0:30)** Pick any action item card. Click **📅 Calendar** → Google Calendar opens in a new tab with title, date, and attendee email all pre-filled. Click *Save*.
4. **(0:45)** Back to the board. Click **✉️ All Emails** at the top → confirm dialog → 5 Gmail compose tabs open at once, each pre-filled for its assignee.
5. **(1:00)** Switch tabs: **📄 Google Doc URL**. Paste the prepared share URL. Click **Extract**. Same board, but extracted from a Doc instead of pasted text.
6. **(1:20)** Pitch line: *"Every team has meetings. Every meeting produces commitments that vanish. Postmeet closes the loop in 5 seconds — paste, extract, distribute. No setup, no auth, no integration work — just outcomes."*

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask backend + extraction pipeline; `/extract` accepts `transcript` text or `doc_url` |
| `links.py` | Pure Calendar / Gmail / MOM URL builders — framework-free, 100% test-covered |
| `streamlit_app.py` | Streamlit front end (the deployed UI); reuses `app` + `links` |
| `templates/index.html` | Flask single-page UI with tab toggle, Trello board, distribute-all, full a11y |
| `requirements.txt` | flask, requests, python-dotenv, gunicorn, streamlit |
| `Procfile` | Cloud Run launch: `gunicorn -b 0.0.0.0:$PORT --workers 2 --timeout 60 app:app` |
| `deploy.sh` | One-shot Cloud Run deploy: API enable → Secret Manager → build → deploy |
| `.gcloudignore` | Excludes `.env`, `.tmp/`, `.git/` from container build context |
| `runtime.txt` | Pins Python 3.10 for buildpacks |

## Rubric mapping

| Parameter | Where Postmeet earns it |
|---|---|
| **Code Quality** | Small, layered modules — pipeline (`app.py`), pure link builders (`links.py`), thin UI (`streamlit_app.py`); pure functions for parsing & dispatch; ruff-clean |
| **Security** | NVIDIA API key in Secret Manager (not plain env var). No PII persistence. OAuth-free dispatch via URL spec = least-privilege by design. `.gcloudignore` keeps `.env` out of build context. |
| **Efficiency** | Single model call per extraction. NIM JSON response mode + a pinned prompt contract keep output parseable (tolerant `{…}` slice, no retry loop). Bulk distribute opens N tabs in parallel via `setTimeout` stagger. Cloud Run auto-scales to zero. |
| **Testing** | **69 pytest tests, 100% line + branch coverage** on `app.py` + `links.py` (210/210 statements, 62/62 branches, 0 partial). Coverage is gated in `pyproject.toml` — CI fails if it drops below 100%. All HTTP mocked, suite runs in <150ms |
| **Accessibility** | Skip-to-content link, semantic HTML (`main`, `section`, `article`, `header`), ARIA labels on all interactive elements, `role="status"` + `aria-live` for status updates, visible focus rings on every focusable element, keyboard shortcut (⌘/Ctrl+Enter), tab toggle uses proper `role="tab"` / `aria-selected`, color contrast meets WCAG AA on the dark theme |
| **Problem Statement Alignment** | Directly improves coordination, communication, and task visibility — meeting commitments become a shared, distributed plan with one click |
| **Services usage** | NVIDIA NIM (Llama 3.1, 8B + 70B fallback), Google Docs export, Google Calendar URL spec, Gmail compose URL, Cloud Run, Secret Manager, Cloud Build |

## Known limitations

- **No persistence** — refresh resets the board. Intentional: no DB to provision, no privacy questions for judges.
- **Per-attendee Google account state** — distribute-all opens N tabs from the *current* user's session, so one person clicks "Save" N times. A real product would dispatch via Calendar API on behalf of attendees, but that requires domain-wide delegation; URL-trick is honest about the constraint.
- **Date resolution** — the model occasionally misjudges day-of-week for relative dates ("next Monday" when today is a Saturday). Always editable before save.
- **Public Doc requirement** — the no-OAuth Doc fetch only works for "Anyone with the link" Docs. Private docs need a real OAuth flow (out of scope for the hackathon).
