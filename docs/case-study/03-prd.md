# Product Requirements Document (PRD) — Postmeet v1

**Owner:** Shubham Mittal · **Status:** v1.0 — Shipped · **Phase:** Ideation → Execution
**Related:** [Vision](01-product-vision.md) · [MRD](02-mrd.md) · [Development & Execution](08-development-execution.md) · [Case study home](./)

---

## 1. TL;DR

Postmeet v1 turns a meeting transcript into a board of owned, dated action items and lets the user push each one into Google Calendar or Gmail in a single click — **with no account, no OAuth, and no stored data.** v1 exists to test one hypothesis: *people who extract commitments will actually distribute them.*

**Shipped:** [postmeet.onrender.com](https://postmeet.onrender.com/) · **Code:** [github.com/Shubham-33/postmeet](https://github.com/Shubham-33/postmeet)

---

## 2. Problem statement

Meeting owners manually retype action items out of notes into calendars, inboxes and trackers — or skip it, and the commitments drop. Existing tools capture meetings well but stop at a summary; closing the last mile conventionally requires OAuth-gated integrations that most users never get approved. (Full market case: [MRD](02-mrd.md).)

## 3. Goals & non-goals

### 3.1 Goals

| # | Goal | Measured by |
|---|---|---|
| G1 | Prove users will extract **and then distribute** | Activation ≥ 25% (extract → ≥1 item distributed) |
| G2 | Deliver first value in under 30 seconds, with zero setup | Time-to-value p50 < 30s from landing → first distribute |
| G3 | Extraction users trust enough to send without heavy rework | Edit rate < 40% of fields; **zero** fabricated items in eval |
| G4 | Feel synchronous | Extraction p95 < 5s |
| G5 | Remove privacy as an adoption objection | No server-side retention of meeting content |

### 3.2 Non-goals (v1)

| Non-goal | Why |
|---|---|
| Accounts, auth, teams | Not needed to test G1; adds friction that would confound the result |
| Server-side persistence / a database | Statelessness *is* the privacy answer at v1; also nothing to test yet |
| Native Calendar/Gmail **API** integration | The URL trick delivers the same user value at 0 setup cost. Native APIs are an H2 investment |
| Transcription / recording | Commodity + capital-intensive; out of the wedge ([Vision §11](01-product-vision.md#11-non-goals-explicitly-not-building)) |
| Slack / Notion / Jira targets | Calendar + email are where the owner actually lives; more targets = more surface, no more learning |
| Mobile-native apps | Responsive web is sufficient for the test |

---

## 4. Success metrics

### 4.1 Metric tree

```
NORTH STAR
└── Commitment Completion Rate (CCR)          ← not observable until H3; steer on inputs
    │
    ├── INPUT METRICS (the funnel)
    │   ├── Activation:     % sessions extract → distribute ≥1 item      [PRIMARY for v1]
    │   ├── Time-to-value:  seconds, landing → first distribute
    │   ├── Extraction quality: precision / recall vs. golden eval set
    │   └── Retention:      repeat sessions / user / week
    │
    └── GUARDRAIL METRICS (must not degrade)
        ├── Hallucination rate: fabricated items per 100 extracted   [target: 0]
        ├── Edit rate:          % of fields corrected before send
        └── Failure rate:       % extractions returning an error
```

### 4.2 Targets & instrumentation

| Metric | Target (v1) | How measured |
|---|---|---|
| **Activation** | ≥ 25% | Event: `extract_success` → `distribute_click` in same session |
| **Time-to-value** | p50 < 30s | `page_load` → first `distribute_click` |
| **Extraction p95 latency** | < 5s | Server-side timer on `/extract` |
| **Hallucination rate** | 0 per 100 | Manual scoring against golden eval set ([Research §5](05-research-plan.md#5-ai-specific-research-evaluation)) |
| **Edit rate** | < 40% of fields | Event: `field_edited` / fields rendered |
| **Failure rate** | < 2% | Non-2xx from `/extract` ÷ total |

> **Status — honest gap.** v1 shipped **without analytics instrumentation** (no event pipeline, deliberately, to keep the stateless privacy promise and ship fast). Activation is therefore currently **unmeasured** — the primary metric for the primary goal. This is the single biggest weakness of v1 and is **Priority 1 for v1.1**: add privacy-preserving, aggregate-only, cookieless event counts (no meeting content), which is compatible with G5. *Shipping a hypothesis test you can't read the result of is a mistake — naming it is more useful than hiding it.*

### 4.3 Kill criterion

If Activation < 25% once instrumented, the last-mile thesis is **wrong** and the response is to pivot the hypothesis — not to improve the model.

---

## 5. Personas & user stories

Personas: [MRD §4](02-mrd.md#4-personas). Stories are written from the meeting owner ("Priya") unless noted.

| ID | Story | Acceptance criteria | Priority |
|---|---|---|---|
| US-1 | As a meeting owner, I want to paste a transcript and get structured action items, so I stop retyping them | Given a ≥30-char transcript, when I press Extract, then I see a summary, decisions, and action items each with owner/date within 5s | **P0** |
| US-2 | As a meeting owner, I want to try it instantly without signing up, so I can judge it in a minute | No account/permission prompt exists anywhere in the flow | **P0** |
| US-3 | As a meeting owner, I want to send a commitment to its owner's calendar in one click | Clicking Calendar opens a Google Calendar event prefilled with title, date, attendee, context | **P0** |
| US-4 | As a meeting owner, I want to email each person their own items | Clicking Email opens a Gmail draft addressed to that owner containing **all** of their items | **P0** |
| US-5 | As a meeting owner, I want to fix a wrong name/date before sending | Any field is editable inline; edits flow into the generated links | **P0** |
| US-6 | As a meeting owner, I want to send everyone the minutes | One action opens a Gmail draft with formatted MoM addressed to all extracted emails | **P1** |
| US-7 | As a meeting owner, I want to use a Google Doc I already keep notes in | Pasting a public Doc URL fetches its text and extracts from it | **P1** |
| US-8 | As a meeting owner, I want to try it with no transcript handy | Sample transcripts load in one click | **P1** |
| US-9 | As a meeting owner, I want to upload a transcript file | `.txt`/`.md` upload and drag-drop are accepted (≤200 KB) | **P1** |
| US-10 | As an **assignee** (Marcus), I want commitments to arrive without installing anything | Received artifacts are a normal Google Calendar invite / Gmail message | **P0** |
| US-11 | As a keyboard user, I want to operate the app without a mouse | All actions reachable via keyboard; ⌘/Ctrl+Enter extracts; visible focus rings | **P1** |
| US-12 | As a returning user, I don't want to lose my board on refresh | Last result restored from local storage (client-side only, TTL 7d) | **P2** |

---

## 6. Functional requirements

> Each maps to a market requirement from [MRD §8](02-mrd.md#8-market-requirements).

### 6.1 Input

| ID | Requirement | Maps to |
|---|---|---|
| FR-1 | Accept a pasted transcript (min 30 chars, else reject with a clear message) | MR-8 |
| FR-2 | Accept a public Google Doc URL and fetch its plain text (no OAuth, via the public export endpoint) | MR-1, MR-8 |
| FR-3 | Accept `.txt`/`.md` upload + drag-drop, ≤200 KB, truncate with warning beyond | MR-8 |
| FR-4 | Auto-detect input mode from content (URL vs. prose) rather than forcing a mode toggle | MR-1 |
| FR-5 | Provide ≥3 one-click sample transcripts (standup / planning / retro) | MR-1 |
| FR-6 | Reject a non-public Doc with an actionable error ("set sharing to Anyone with the link") | MR-8 |

### 6.2 Extraction

| ID | Requirement | Maps to |
|---|---|---|
| FR-7 | Return `summary` (1–2 sentences), `decisions[]`, and `action_items[]` | MR-2 |
| FR-8 | Each action item carries: `task`, `owner`, `owner_email`, `due_date`, `context` | MR-2 |
| FR-9 | Resolve relative dates ("Friday", "next Monday") to absolute `YYYY-MM-DD` using today's date | MR-2 |
| FR-10 | Match an owner to an email found **anywhere** in the transcript by first-name match on the local-part | MR-2 |
| FR-11 | Extract **only explicit commitments**; never infer or invent a task | **MR-3** |
| FR-12 | Emit empty string/array rather than guessing when data is absent | MR-3 |
| FR-13 | One assignee per item; split shared ownership into separate items | MR-2 |

### 6.3 Review & edit

| ID | Requirement | Maps to |
|---|---|---|
| FR-14 | Render a board: a Decisions column + one column per owner | MR-2 |
| FR-15 | Every field (task, owner, email, date, context) editable inline | **MR-5** |
| FR-16 | Edits propagate to all generated links without re-extraction | MR-5 |
| FR-17 | Nothing is transmitted anywhere until the user explicitly clicks a distribute action | MR-5, MR-9 |

### 6.4 Distribute

| ID | Requirement | Maps to |
|---|---|---|
| FR-18 | Per item: open a prefilled Google Calendar event (title, date, attendee, context) | **MR-4** |
| FR-19 | Per owner: open a Gmail draft containing **all** of that owner's items (one email per person, not per task) | MR-4, MR-7 |
| FR-20 | Bulk: open all calendars / all emails, staggered to survive popup blockers | MR-4 |
| FR-21 | MoM: one Gmail draft, formatted minutes, addressed to all extracted emails (deduped, sorted) | MR-4 |
| FR-22 | MoM copyable as plain text to the clipboard | MR-4 |
| FR-23 | Items with no due date default to today + 7 days | MR-4 |
| FR-24 | All distribution must work for recipients with no Postmeet account | **MR-7** |

---

## 7. AI requirements

> The section most PRDs miss. An LLM feature without stated quality, failure and evaluation requirements is not specified — it's hoped for.

### 7.1 Model & inference

| ID | Requirement | Decision & rationale |
|---|---|---|
| AI-1 | Extraction must be a **single** model call — no agentic loops, no retries on success path | Latency budget (G4) and cost; the task is well-bounded |
| AI-2 | Primary model must meet p95 < 5s | **Llama 3.1 8B** via NVIDIA NIM: ~2.5s consistent |
| AI-3 | The system must degrade gracefully if the primary model fails | Automatic fallback chain → **Llama 3.1 70B**; transient errors only |
| AI-4 | Model choice must be config-swappable without a code change | `NIM_MODEL` env var pins a single model |
| AI-5 | Temperature 0 | Determinism; this is extraction, not generation |

> **Key tradeoff (documented, not hidden):** the 70B model was tested first and *rejected as primary* — measured latency was **9s–46s with timeouts**, vs. 8B's **~2.5s consistent**, at comparable extraction quality on this task. **Model quality is an input to product value, not the goal.** Full ADR: [Development §ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback).

### 7.2 Output contract

| ID | Requirement |
|---|---|
| AI-6 | Request JSON response mode; pin the exact JSON contract in the system prompt |
| AI-7 | Parse defensively — tolerate markdown fences/prose by slicing the first `{` to the last `}` |
| AI-8 | Malformed content must surface as a clear 502, never a crash or a partial board |
| AI-9 | A parse failure must **not** trigger the model fallback (a different model won't fix a contract violation — only transient errors are retried) |

### 7.3 Guardrails

| ID | Requirement | Enforcement |
|---|---|---|
| AI-10 | **Never fabricate a commitment** (MR-3) | Prompt constrains to explicit commitments; measured as hallucination rate = 0 in eval |
| AI-11 | Never invent context — empty string if none exists | Prompt rule + eval check |
| AI-12 | Never invent an email address | Only emails literally present in the transcript may be used |
| AI-13 | The human is the final checkpoint — the system drafts, it never sends | No auto-send exists in the product by design |

### 7.4 Evaluation

| ID | Requirement |
|---|---|
| AI-14 | A **golden eval set** of human-labelled transcripts must exist before any model change is accepted |
| AI-15 | Track **precision** (fabrications), **recall** (misses), and **field accuracy** (owner/date/email) |
| AI-16 | Model swaps must be decided on eval deltas, not vibes |
| AI-17 | Eval set must include **real, messy, multi-speaker** transcripts — not only curated samples ([MRD R7](02-mrd.md#9-risks--assumptions)) |

> **Status — honest gap.** v1's model decision was made on **measured latency + spot-checked quality**, not a formal eval set. That was defensible under a hackathon constraint and is **not** defensible for v1.1. Building the eval harness is the top AI-quality investment ([Research §5](05-research-plan.md#5-ai-specific-research-evaluation)).

---

## 8. Non-functional requirements

| ID | Category | Requirement | Status |
|---|---|---|---|
| NFR-1 | Performance | Extraction p95 < 5s | ✅ ~2.5s typical |
| NFR-2 | Performance | Page < 100 KB gzipped; index cached 5 min | ✅ gzip + Cache-Control |
| NFR-3 | Reliability | Single model failure must not fail the request | ✅ fallback chain |
| NFR-4 | Reliability | Upstream timeout bounded at 30s | ✅ |
| NFR-5 | Privacy | **No server-side persistence** of transcripts or extractions | ✅ stateless |
| NFR-6 | Privacy | Client-side restore only, local storage, 7-day TTL, user-clearable | ✅ |
| NFR-7 | Security | API key only via secret manager / env — never in the repo or client | ✅ Render secret; `.gcloudignore`/`.gitignore` exclude `.env` |
| NFR-8 | Security | **Zero OAuth scopes requested** — least privilege by construction | ✅ |
| NFR-9 | Accessibility | WCAG AA: semantic landmarks, ARIA labels, `aria-live` status, visible focus, keyboard-complete, AA contrast | ✅ |
| NFR-10 | Quality | 100% line+branch coverage on business logic, gated in CI | ✅ 69 tests |
| NFR-11 | Portability | No vendor lock-in on the model provider | ✅ OpenAI-compatible endpoint + env override |
| NFR-12 | Extensibility | Must not foreclose enterprise needs (SSO, residency) at H2/H3 | ⚠️ Deferred, not blocked |

---

## 9. Primary UX flow

```
Landing (no auth)
   │
   ├─ Paste transcript  ┐
   ├─ Public Doc URL    ├──► [Extract]  ──► single LLM call (~2.5s)
   ├─ Upload .txt/.md   ┘         │
   └─ Load sample ──────┘         ▼
                          Board renders
                          ├── Summary + decisions
                          └── One column per owner
                                 │
                          Inline edit any field  ◄── human checkpoint
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          📅 Calendar (per item)     ✉️ Email (per owner, all their items)
          ✉️ MoM to all             📋 Copy MoM
                    │
                    ▼
        Prefilled Google tab opens → user clicks Save / Send
```

**Design intent:** the flow has exactly one required decision (what to paste) before value appears. Everything else is optional refinement.

---

## 10. Dependencies

| Dependency | Purpose | Risk |
|---|---|---|
| NVIDIA NIM (Llama 3.1) | Extraction | Free-tier credits could exhaust → app degrades with a clear error, not a crash |
| Google Calendar URL spec | Per-item distribution | Long-stable public spec; change would break FR-18 ([MRD R6](02-mrd.md#9-risks--assumptions)) |
| Gmail compose URL spec | Email distribution | As above |
| Google Docs public export | FR-2 | Only works for link-shared docs — a stated limitation |
| Render (free tier) | Hosting | Sleeps after 15 min idle → ~40s cold start; mitigated by a scheduled keep-warm ping |

## 11. Risks & mitigations

| # | Risk | Mitigation |
|---|---|---|
| P1 | Users extract but never distribute (kills the thesis) | Make distribution the visually dominant action; instrument Activation (v1.1) |
| P2 | A hallucinated item destroys trust | AI-10..13 + human checkpoint + precision-biased prompt |
| P3 | Wrong date resolution on relative dates | Today's date injected into the prompt; **all dates editable**; known limitation documented |
| P4 | Popup blockers break bulk distribute | Staggered `window.open`; per-item fallback |
| P5 | Model provider outage | Fallback chain; clear user-facing error, never a stack trace |
| P6 | Cold start makes first impression ~40s | Scheduled keep-warm ping every 10 min |

## 12. Release criteria

v1 ships only when **all** are true:

- [x] All P0 stories pass acceptance
- [x] Extraction p95 < 5s measured live
- [x] 100% line+branch coverage on business logic; CI green
- [x] Zero secrets in the repo; key in a secret store
- [x] Zero fabricated items across the sample suite
- [x] Graceful, human-readable errors on every failure path (no stack traces)
- [x] Publicly reachable with no login
- [x] Accessibility pass (keyboard-complete, AA contrast)

## 13. Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| Q1 | Is the ~70% pain figure real for our segment? | Research | Before H2 |
| Q2 | What Activation rate do we actually see? | Analytics (v1.1) | Before H2 |
| Q3 | Do users trust extraction enough to bulk-send, or do they send one-by-one? | Research + analytics | H2 scoping |
| Q4 | Is 8B sufficient on messy real transcripts, or does quality force 70B? | Eval harness | v1.1 |
| Q5 | Does the correction flywheel produce usable training signal at realistic volume? | Data science | H3 |

---

## Appendix A — Extraction schema

```json
{
  "summary": "string",
  "decisions": ["string"],
  "action_items": [{
    "task":        "string",
    "owner":       "string  (first name, or 'Unassigned')",
    "owner_email": "string  (empty if not present in transcript)",
    "due_date":    "string  (YYYY-MM-DD, empty if none stated)",
    "context":     "string  (≤~25 words explaining why it matters; empty if absent)"
  }]
}
```

## Appendix B — API surface

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/` | GET | — | Single-page UI (gzipped, cached 5 min) |
| `/extract` | POST | `{"transcript": str}` or `{"doc_url": str}` | `200` → schema above · `400` too short/invalid · `403` private doc · `502` upstream/model failure |

---

*Next: [User Guide →](04-user-guide.md)*
