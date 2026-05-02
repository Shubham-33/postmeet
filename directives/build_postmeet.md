---
name: Build Postmeet
description: SOP for building Postmeet — a meeting → action items → distributed tasks tool for the PromptWars hackathon
status: in-progress
---

# Directive: Build Postmeet

## Goal

Ship a working demo of **Postmeet** for the PromptWars hackathon: a single-page web app where a user pastes a meeting transcript (or a Google Doc URL of meeting notes), and the system extracts decisions + action items, then auto-creates Google Calendar events and Gmail notifications for every assignee.

The MVP must be demoable end-to-end in under 90 seconds on stage.

## Success Criteria

- [ ] User pastes raw transcript → structured `{decisions[], action_items[{owner, task, due_date}], summary}` returned in <5s
- [ ] User can also paste a Google Doc URL → text is fetched server-side and processed identically
- [ ] "Distribute" button creates one Google Calendar event per action item on the assignee's calendar
- [ ] "Distribute" button sends one Gmail notification per assignee summarizing their assigned items
- [ ] A shareable read-only summary page renders the structured output
- [ ] All API calls are scoped read/write narrowly (least privilege)
- [ ] Three sample transcripts pass snapshot tests for the extraction step

## Non-Goals (do NOT build)

- Persistent database / accounts / billing
- Slack integration (stretch only)
- Speech-to-Text from raw audio (stretch only — paste transcript instead)
- Mobile-native app
- Editing extracted action items in-line (v2)

## Inputs

- **Transcript text** — raw paste, any format
- **Google Doc URL** — must be readable by the authenticated user
- **(Stretch) Google Meet recording link** — defer

## Tools / Scripts

All deterministic logic lives in `execution/`. Create these scripts as needed; check first whether one already exists before writing a new one.

| Script | Purpose | Status |
|---|---|---|
| `execution/extract_actions.py` | Single LLM call: transcript → `{decisions, action_items, summary}` JSON | TODO |
| `execution/fetch_google_doc.py` | Given a Doc URL, return plain text via Google Docs API | TODO |
| `execution/create_calendar_event.py` | Create one event on a user's calendar with title, description, attendee, due date | TODO |
| `execution/send_gmail.py` | Send a templated email summarizing an assignee's action items | TODO |
| `execution/distribute_actions.py` | Orchestrator: takes extracted output + auth, calls calendar + gmail in parallel | TODO |

The web app (Next.js) lives at the project root or `web/` — it calls these scripts via API routes, OR re-implements them in TypeScript. **Decision pending** (see Open Questions).

## Outputs

- **Live URL** (Vercel deploy) — the demo target
- **Shareable summary page** at `/m/[id]` — public read-only view of one extraction
- **Side effects per "Distribute":** N calendar events created + M emails sent (N = action items, M = unique assignees)

## Edge Cases

- **No assignee detected** → action item appears in output with `owner: "unassigned"`, no calendar/email dispatch for it; UI flags it visually
- **No due date detected** → default to 7 days from now, flag visually so user can confirm
- **Assignee name doesn't match a real email** → require user to map name → email in a small pre-distribute step
- **Google Doc fetch fails (403/404)** → fallback to "paste raw text" with a clear error
- **LLM returns malformed JSON** → retry once with stricter prompt; on second failure, show raw extraction with manual editing
- **Empty transcript / <50 words** → reject up front with friendly error
- **Same transcript distributed twice** → idempotency via session ID; show "already distributed" warning

## Judging Rubric Mapping

| Parameter | How Postmeet scores |
|---|---|
| **Code Quality** | Small surface (~5 scripts + 1 web app), pure functions for parsing/dispatch |
| **Security** | OAuth scoped to `calendar.events`, `gmail.send`, `documents.readonly` only. No PII persistence. Session-only state. |
| **Efficiency** | One LLM call per meeting. Calendar + Gmail dispatched in parallel via `Promise.all`. Doc fetches cached by URL hash. |
| **Testing** | Pure parsers unit-tested. Three sample transcripts as snapshot fixtures. Integration test for distribute pipeline against a test Google account. |
| **Accessibility** | Semantic HTML, keyboard nav, alt text, screen-reader-friendly action item list, WCAG AA contrast |
| **Problem Statement Alignment** | Directly improves coordination + task visibility — the original ask |
| **Google Services Usage** | Docs API (read), Calendar API (write), Gmail API (send), Tasks API (alt write target). 4 services minimum. |

## Open Questions (resolve before coding)

1. **Web stack:** Next.js (TypeScript everywhere) vs. Python FastAPI + plain HTML? Next.js is faster to deploy and matches "vibe-coding" aesthetic. Python matches the project's existing `execution/` convention.
2. **Auth model:** does the meeting *organizer* authenticate once and Postmeet writes to *attendees'* calendars (requires domain-wide delegation, complex), OR does each attendee authenticate themselves? MVP answer: organizer authenticates, action items dispatch as **calendar invites** (which puts events on attendees' calendars without needing their auth) + Gmail sends as the organizer.
3. **LLM choice:** Gemini 2.5 Flash — picked for the Google integration story (judges weight Google services) and for guaranteed JSON via `responseSchema`. Fast enough for live demos.
4. **Persistence for shareable links:** in-memory + ephemeral, or one Google Sheet per session as the "database"? Sheet-as-DB matches the project's pattern and adds another Google Service to the rubric.

## Self-Annealing Notes

_Update this section as we build. Record API quirks, rate limits, prompt tweaks that improved extraction quality, etc._

- (none yet)
