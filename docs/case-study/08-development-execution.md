# Development & Execution — Postmeet v1

**Owner:** Shubham Mittal · **Status:** v1 shipped · **Phase:** Development & Execution
**Related:** [PRD](03-prd.md) · [Methodology](06-methodology.md) · [Launch Plan](09-launch-plan.md) · [Case study home](./)

---

## 1. What shipped

| | |
|---|---|
| **Live** | [postmeet.onrender.com](https://postmeet.onrender.com/) — public, no login |
| **Code** | [github.com/Shubham-33/postmeet](https://github.com/Shubham-33/postmeet) — open, CI green |
| **Stack** | Python · Flask · NVIDIA NIM (Llama 3.1) · Render · GitHub Actions |
| **Quality** | **69 tests · 100% line + branch coverage** on business logic, gated in CI · ruff clean |
| **Performance** | Extraction ~2.5s typical (p95 target <5s) |
| **Origin** | Built for **PromptWars 2026** (vibe-coding hackathon) — **3rd prize** — then hardened for portfolio/production use |

---

## 2. Architecture

```
                       ┌─────────────────────────────────────┐
  Browser              │  Flask (app.py)                     │
  ├─ paste ───────────►│                                     │
  ├─ Doc URL ─────────►│  GET  /         → single-page UI    │
  ├─ file upload ─────►│  POST /extract  → extraction        │
  │                    │        │                            │
  │                    │        ├─ fetch_google_doc_text()   │──► Google Docs
  │                    │        │   (public export, no OAuth)│    public export
  │                    │        │                            │
  │                    │        └─ call_llm()                │──► NVIDIA NIM
  │                    │            ├─ 8B primary  (~2.5s)   │    OpenAI-compatible
  │                    │            └─ 70B fallback           │    /chat/completions
  │                    │            └─ parse_extraction()     │
  │                    └─────────────────────────────────────┘
  │                                     │ JSON
  ▼                                     ▼
  Board renders ──► inline edit ──► links.py builds prefilled URLs
                                          │
                                          ├──► calendar.google.com/render?...
                                          └──► mail.google.com/?view=cm&...
                                                    (opens in user's own session)
```

**Module boundaries — chosen for testability:**

| Module | Responsibility | Why separate |
|---|---|---|
| `app.py` | HTTP surface + extraction pipeline | Pure functions (`call_llm`, `parse_extraction`, `fetch_google_doc_text`) — testable without a server |
| `links.py` | Calendar/Gmail/MoM URL builders | **Zero framework imports.** Pure in → pure out, so the highest-risk logic (what a recipient actually receives) is trivially unit-testable |
| `templates/` + `static/` | Flask single-page UI | Presentation only |
| `streamlit_app.py` | Alternate UI | Imports `app` + `links` — proves the core is genuinely decoupled |

**The design principle:** the two things most likely to be wrong — *what the model returns* and *what the recipient receives* — are both pure functions behind hard boundaries. Everything else is I/O.

---

## 3. Architecture Decision Records

### ADR-1: Prefilled URLs instead of OAuth integration

| | |
|---|---|
| **Status** | ✅ Accepted — this is the product |
| **Context** | Distribution needs to reach a user's calendar/inbox. Conventional answer: OAuth + Calendar/Gmail APIs. |
| **Decision** | Use Google's public **URL specs** (`calendar/render?action=TEMPLATE...`, `mail/?view=cm...`) to open prefilled actions in the user's own signed-in session. |
| **Consequences** | ✅ Zero setup, zero scopes, works on first visit, no security review, no token storage, no admin gate. ✅ Recipients need nothing. ❌ User clicks Save/Send themselves — no true automation. ❌ Depends on a spec Google could change ([MRD R6](02-mrd.md#9-risks--assumptions)). |
| **Rejected alternative** | Native API + OAuth — "correct," and it deletes the entire wedge. Scored **lowest** on RICE ([Methodology §6.1](06-methodology.md#61-rice--worked-example)). |
| **Reversibility** | High. `links.py` is isolated; H2 can add native APIs behind the same interface without touching the pipeline. |

### ADR-2: Fast primary model with automatic fallback

| | |
|---|---|
| **Status** | ✅ Accepted |
| **Context** | Extraction needs to feel synchronous ([PRD G4](03-prd.md#31-goals): p95 <5s). Instinct says use the biggest model for quality. |
| **Measurements** | `llama-3.3-70b`: **did not respond at all** — consistent timeouts on the hosted tier. `llama-3.1-70b`: **9s–46s, inconsistent**, incl. a 45s timeout→fallback. `llama-3.1-8b`: **~2.5s, consistent across runs**, comparable extraction quality on this task (owners, emails, dates, decisions all correct). |
| **Decision** | **8B as primary; 70B as automatic fallback** on transient errors. `NIM_MODEL` env pins a single model. |
| **Rationale** | Model quality is an **input** to product value, not the goal. A 46s hang reads as *broken*; 2.5s reads as *magic*. On a well-bounded extraction task, 8B's quality was indistinguishable in spot checks — so the 70B "upgrade" bought nothing users could perceive and cost the thing they'd notice most. |
| **Consequences** | ✅ p95 target met with headroom. ✅ Survives a cold/failed primary. ❌ Possible quality gap on messy transcripts — **unmeasured**. |
| **Honest weakness** | Decided on **measured latency + spot-checked quality**, not a golden eval set. Defensible under a hackathon clock; **not** a defensible habit. [Research §5](05-research-plan.md#5-ai-specific-research-evaluation) exists to retire this debt; [RQ4](05-research-plan.md#2-research-questions) could overturn this ADR — and should be allowed to. |

### ADR-3: Stateless — no database

| | |
|---|---|
| **Status** | ✅ Accepted for v1 |
| **Decision** | No server-side persistence. Client-side local storage only (7-day TTL). |
| **Rationale** | Three wins from one cut: (1) removes the privacy objection at adoption — *"we don't store your meetings"* is stronger than any policy page; (2) nothing to test at v1 — persistence doesn't move the Activation hypothesis; (3) zero infra/ops/compliance surface. |
| **Consequences** | ✅ Fast to ship, no GDPR surface, honest privacy claim. ❌ No history, no cross-device, **no server-side analytics** — which is exactly why Activation went unmeasured. |
| **Note** | The privacy stance and the measurement gap came from the *same* decision. The v1.1 fix (aggregate, cookieless, content-free counts) keeps the promise while restoring the read-out. |

### ADR-4: Structured output via JSON mode + tolerant parsing

| | |
|---|---|
| **Status** | ✅ Accepted |
| **Context** | Migrated from Gemini (`responseSchema` → hard schema guarantee) to NVIDIA NIM, which offers JSON mode but not an equally strict schema guarantee. |
| **Decision** | JSON response mode + the exact contract pinned in the system prompt + a tolerant parser slicing first `{` → last `}`. One call, no retry loop. Parse failures do **not** trigger the model fallback (a different model won't fix a contract violation — only transient errors are retried). |
| **Consequences** | ✅ Single call preserves the latency budget. ✅ Survives fenced/prose-wrapped output. ❌ Weaker guarantee than a native schema — mitigated by the parser + a clear 502. |

---

## 4. Execution timeline

| Phase | Work | Outcome |
|---|---|---|
| **Hackathon (PromptWars 2026)** | Core loop: extract → board → distribute. Flask + Gemini. | Working prototype · **3rd prize** |
| **Hardening** | Test suite → 100% coverage, gzip, caching, a11y pass, CI | Production-grade backend |
| **UX revamp** | File upload + drag-drop, inline editing, MoM, editorial UI, local persistence | The product as it is today |
| **Model migration** | Gemini → NVIDIA NIM. Discovered 3.3-70B dead → 3.1-70B slow → **8B + fallback** (ADR-2) | 46s → **2.5s** |
| **Portability & reliability** | `links.py` extracted + 100%-covered · fallback chain · graceful errors · env model override | 47 → **69 tests** |
| **Deployment** | Streamlit Cloud attempted → **rejected** (see below) → Render + keep-warm cron | Public, no-login URL |
| **Consistency pass** | Frontend copy corrected to NVIDIA; **fabricated usage stats replaced with true facts** | Coherent across app/repo/docs |

### The deployment detour — a real execution lesson

Streamlit Community Cloud was the obvious free host, and a Streamlit UI was built for it. It failed for a non-obvious reason: **the platform forces a mandatory viewer sign-in on every app.**

Diagnosis took a discriminating test rather than guesswork: repo visibility was confirmed public via API; a fresh redeploy still gated; then — the decisive step — **Streamlit's own showcase apps** (`roadmap`, `30days`, `cheat-sheet`.streamlit.app) were checked and **all returned the identical `/-/auth/app` redirect.** That ruled out our configuration entirely and proved it was platform-wide.

Migrated to **Render** (`render.yaml`, gunicorn) → genuinely public URL.

**The lessons:**
1. **A login wall silently kills a portfolio/demo link** — the artifact looks "shipped" while being unreachable. Verify from an *unauthenticated* client, always.
2. **Test the hypothesis that discriminates.** Checking a known-good third-party app answered in seconds what settings-fiddling couldn't answer in an hour.
3. The Streamlit UI wasn't wasted — it forced `links.py` out of the frontend, which is why that logic is now pure and 100% covered.

---

## 5. Quality strategy

### 5.1 Deterministic testing

| | |
|---|---|
| **Suite** | 69 tests · **100% line + branch** on `app.py` + `links.py` · <150ms · all HTTP mocked |
| **Gate** | `--cov-fail-under=100` in `pyproject.toml` — **CI fails if coverage drops** |
| **Covered** | Missing API key at import · Doc-URL regex (+/− cases) · Doc fetch: 401/403/500/HTML-login/happy · `parse_extraction`: fenced, prose-wrapped, no-object, malformed · `call_llm`: happy, HTTP error, **fallback-on-timeout**, **all-models-fail**, **parse-error-not-retried** · `/extract` across both input modes and every error branch · gzip middleware edge cases · every `links.py` builder |
| **Why 100%** | Not vanity. This is a **pipeline**: an unhandled branch surfaces as a stack trace to a user, or worse, a silently wrong calendar invite. The 100% bar is cheap on ~200 statements and it forces every error path to be *designed*, not discovered. |

**What the tests genuinely protect:** `links.py` coverage locks the exact prefill-URL output. A refactor that silently changed a recipient's date, address, or email body would be caught — that's the failure mode with real-world consequences (an assignee gets a wrong invite; Priya's credibility, not ours, takes the hit).

### 5.2 The gap: probabilistic testing

100% coverage proves **the code is correct**. It cannot prove **the output is right** — the function can return perfectly valid JSON containing a fabricated commitment, and every test passes.

That's the eval harness's job, and **it doesn't exist yet** ([Research §5](05-research-plan.md#5-ai-specific-research-evaluation)). Stating this plainly matters more than the coverage badge: *for an AI product, deterministic tests are necessary and structurally insufficient.*

### 5.3 CI/CD

| | |
|---|---|
| **CI** | GitHub Actions on push/PR to `main`: install → pytest with the 100% gate. Mocked HTTP → no network, no key, no flake. |
| **CD** | Render auto-deploys `main`. Verified: push → live in ~90s. |
| **Ops** | Scheduled Actions cron pings the app every 10 min (free tier sleeps at 15 min idle → ~40s cold start). |
| **Secrets** | `NVIDIA_API_KEY` in Render's secret store only. `.gitignore`/`.gcloudignore` exclude `.env`. Zero secrets in the repo. |

---

## 6. Risk register (execution)

| # | Risk | Sev | Status | Mitigation |
|---|---|---|---|---|
| E1 | Model provider outage / credit exhaustion | High | 🟡 Live | Fallback chain; graceful user-facing error; **free-tier credits are a real portfolio risk** |
| E2 | Cold start = 40s first impression | Med | 🟢 Mitigated | Keep-warm cron; paid tier is the real fix |
| E3 | Google changes the URL specs | High | 🟡 Accepted | Long-stable public specs; H2 native APIs are the structural hedge |
| E4 | Hallucinated commitment reaches a recipient | **High** | 🟡 Partial | Precision-biased prompt + human checkpoint. **No eval measurement yet** — the top open risk |
| E5 | Activation unmeasured | High | 🔴 **Open** | v1.1 P0: privacy-preserving analytics |
| E6 | Secret leakage | High | 🟢 Closed | Secret store; repo scanned; ignore rules |
| E7 | Popup blockers break bulk distribute | Low | 🟢 Mitigated | Staggered opens + per-item fallback |
| E8 | 8B underperforms on messy real transcripts | Med | 🔴 **Open** | Golden eval set ([RQ4](05-research-plan.md#2-research-questions)) |

---

## 7. What I'd do differently

| Decision | Verdict | Reasoning |
|---|---|---|
| Cut persistence/accounts/integrations | ✅ Right | Kept v1 a *test*, not a product. The "Won't" column is why it shipped. |
| URL-prefill wedge | ✅ Right | The only genuine insight; still the whole differentiator. |
| 8B over 70B | ✅ Right call, **weak evidence** | Correct instinct (reliability > marginal quality); should have been eval-backed, not spot-checked. |
| Ship without analytics | ❌ **Wrong** | Ran a Lean experiment with no read-out. Instrumentation belonged in the Definition of Done. **Biggest mistake of v1.** |
| Fabricated usage stats in the UI | ❌ **Wrong, since fixed** | "12,847 meetings processed" on a product with **no database** is indefensible — and the exact thing a sharp reviewer probes. Replaced with true facts (~2.5s · 0 OAuth scopes · 100% coverage). Honest numbers were also *more* impressive. |
| Streamlit-first hosting | ➖ Neutral | Cost time; produced the `links.py` refactor. Verify public reachability *before* investing in a host. |
| 100% coverage gate | ✅ Right | Cheap at this size; forced error paths to be designed. |

---

*Next: [Launch Plan →](09-launch-plan.md)*
