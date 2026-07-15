# Post-Launch — Operating, Measuring & Iterating

**Owner:** Shubham Mittal · **Status:** v1.0 · **Phase:** Development & Execution
**Related:** [Launch Plan](09-launch-plan.md) · [PRD](03-prd.md) · [Research Plan](05-research-plan.md) · [Case study home](./)

---

## 1. The post-launch job

Launch is the *start* of the experiment, not the end of the project. The post-launch job is three things, in order:

1. **Read the result** — did the loop close?
2. **Close the loop between evidence and roadmap** — make the next decision on data, not momentum.
3. **Protect trust** — one fabricated commitment costs more than a quarter of features gains.

**The trap this document exists to avoid:** shipping, watching traffic go up, and calling it validation. Traffic is not the hypothesis.

---

## 2. The measurement dashboard

### 2.1 What we watch

| Tier | Metric | Target | Cadence | Why |
|---|---|---|---|---|
| **North star** | Commitment Completion Rate | — | H3 | Not observable until we own completion state. Steer on inputs until then. |
| **Primary** | **Activation** (extract → distribute ≥1) | **≥25%** | Daily | *The* hypothesis. Everything else is secondary. |
| Input | Time-to-value (p50) | <30s | Weekly | The wedge is speed-to-aha |
| Input | Extraction p95 latency | <5s | Daily | NFR-1; degradation is silent |
| Input | Retention (W1/W4) | W4 >20% | Weekly | One-time novelty vs. habit |
| Input | Extraction precision / recall | ≥0.95 / ≥0.80 | Per model/prompt change | Trust |
| **Guardrail** | Hallucination rate | **0** | Per eval run | Non-negotiable |
| **Guardrail** | Edit rate by field | <40% | Weekly | Free live quality signal |
| **Guardrail** | Failure rate | <2% | Daily | Reliability |
| Business | Free→Pro conversion | TBD | Monthly | H2 |

### 2.2 The two numbers that decide everything

**Activation** answers *"is the thesis right?"* — and **edit rate by field** answers *"where is the model actually weak?"* for free, continuously, with no labelling.

Edit-rate-by-field is the most underrated instrument here. If `owner_email` is corrected 60% of the time, FR-10 (email matching) is broken — and we learn that from production behaviour without commissioning a study. It's a golden eval set that users build for us, for nothing, forever.

### 2.3 What we deliberately don't optimise

| Vanity metric | Why it's excluded |
|---|---|
| Page views / signups | No signup exists. Traffic ≠ value. |
| Extractions per day | Rises even if **nobody distributes** — i.e. it goes up while the product fails. Actively misleading. |
| "Meetings processed" counters | We literally have no database. **Fabricating this number was a real mistake in v1**, since corrected ([Dev §7](08-development-execution.md#7-what-id-do-differently)). |
| Time-in-app | Perverse: less time is better. The goal is to leave fast. |

**A metric that can go up while the product fails is worse than no metric.** That's the filter.

---

## 3. Feedback loops

Four loops, running at different speeds:

| Loop | Speed | Source | Feeds |
|---|---|---|---|
| **Behavioural** | Continuous | Analytics: Activation, edit rate, drop-off | Prioritisation |
| **Corrective** | Continuous | Every user edit = a labelled correction | **The flywheel** + eval set |
| **Qualitative** | Weekly | Usability sessions, churn interviews, support | The *why* behind the numbers |
| **Evaluative** | Per change | Golden eval set in CI | Model/prompt gate |

### 3.1 The corrective loop is the strategy

```
extract → user edits before sending → correction captured (schema-identical to eval labels)
   → eval set grows · fine-tune / few-shot on accepted output → accuracy ↑
   → trust ↑ → more extractions → more corrections ──┐
   └──────────────────────────────────────────────────┘
```

The design decision that makes this possible was made for a different reason: **the human checkpoint** ([7P §6](07-7p-analysis.md#6-process)) exists for *trust*, and it turns out to also be the data-collection mechanism and the moat ([Vision §9](01-product-vision.md#9-the-moat)). One decision, three jobs.

**Requirement:** corrections must be captured as **aggregate, content-free signal** (which field, was it changed, edit distance bucket) — not raw meeting text. This preserves [ADR-3](08-development-execution.md#adr-3-stateless--no-database)'s privacy promise. Storing raw transcripts to train would trade the adoption wedge for the moat — and at H1 the wedge is worth more. Any move to content-level training requires **explicit, informed opt-in.** Non-negotiable.

### 3.2 Churn interviews — the cohort everyone skips

The most valuable users to talk to are the ones who **tried it once and never came back.** They are unmotivated to be polite and they know exactly what was wrong. Cadence: 3–5 per month, recruited from the beta list, asked one question — *"Walk me through the last time you thought about using it and didn't."*

---

## 4. Operating cadence

| Ritual | Frequency | Output |
|---|---|---|
| Metric review | Weekly, 30 min | Activation trend; anything red |
| Discovery sync | Weekly | What did we learn? What changes? |
| Backlog re-rank | Fortnightly | RICE re-scored **with new Confidence values** — that's what the evidence actually buys |
| Eval run | Every prompt/model change (CI) | Precision/recall delta |
| OKR check-in | Monthly | Honest status, incl. ⚠️ and ⬜ |
| Retro | Monthly | Process changes |

**Kanban, not Scrum, deliberately** ([Methodology §5](06-methodology.md#5-delivery-kanban-over-scrum-for-now)): post-launch, priorities *should* move the week evidence lands. Sprint commitments would create pressure to finish work the data has already invalidated.

---

## 5. Incident response: trust

Standard sev levels don't capture the failure that matters here. **A fabricated commitment emailed to a real person is a P0 — even though nothing crashed and every test passes.**

| Step | Action |
|---|---|
| 1. Contain | Pause bulk distribute (highest blast radius) |
| 2. Reproduce | Recover the transcript from the reporter (with consent) |
| 3. **Add to eval set** | Every incident becomes a permanent regression test |
| 4. Fix | Prompt/model change |
| 5. Verify | Full eval — precision must not regress elsewhere |
| 6. Restore & communicate | Say what happened, plainly |

**Why P0:** the error lands on the *user's* credibility with their own team, not on ours. Marcus receives an invite for something he never agreed to, and Priya looks careless. **We damage a relationship we're not party to** — which is unrecoverable in a way an outage isn't.

---

## 6. The iteration plan

### 6.1 v1.1 — Make the experiment readable *(immediate)*

| Priority | Item | Why |
|---|---|---|
| **P0** | Privacy-preserving analytics (aggregate, cookieless, content-free) | Activation is currently **unmeasured**. Everything below is guessing until this lands. RICE: **30,000** — highest by 50× |
| **P0** | Golden eval set + CI harness | Converts [ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback) from anecdote to evidence; gates trust |
| P1 | Fake doors (Zoom / Outlook / auto-join) | Ranks H2 with behaviour instead of opinion |
| P1 | Paid host (kill the 40s cold start) | Required before public launch |
| P2 | Recipient attribution loop | Cheapest growth lever we own ([7P §3](07-7p-analysis.md#3-place-distribution)) |

### 6.2 Then — gated on evidence

```
                  Activation ≥25%?
                   ┌─────┴─────┐
                 YES           NO
                  │             │
             Fund H2       Back to discovery
        (auto-capture)     RQ1: is pain real?
                  │        RQ3: is friction the blocker?
                  ▼        → pivot the hypothesis,
        H3: completion       DON'T tune the model
        tracking → CCR
```

**H2 — Kill the paste step:** browser extension + AI notetaker (Zoom/Teams/Meet), native Gmail/Outlook/Calendar, persistence + team workspaces. *Sequenced by fake-door demand, not intuition.*

**H3 — Own the outcome:** completion tracking, proactive nudges, follow-through analytics. **This is where the north star becomes measurable** — and where Postmeet stops being a utility and becomes a system of record.

---

## 7. Long-term risks

| Risk | Watch | Response |
|---|---|---|
| **Platform-native ships the last mile** (Copilot/Zoom) | Their release notes | Cross-platform + flywheel; accelerate H2/H3. **The existential one** ([MRD §5.3](02-mrd.md#53-the-honest-competitive-risk)) |
| Flywheel doesn't produce usable signal | Correction volume/quality | If it fails, **this is a feature, not a company** — say so honestly and act |
| Free tier cannibalises conversion | Free→Pro rate | Gate on friction removal, never on extraction |
| Google changes the URL specs | Distribution failure rate | H2 native APIs are the structural hedge |
| Model costs scale badly | $/extraction | 8B is already ~free; fine-tuned small models get cheaper |

---

## 8. Honest scorecard

| Dimension | Status |
|---|---|
| Core loop works, live, publicly | ✅ |
| Fast, reliable, graceful (~2.5s, fallback) | ✅ |
| Engineering quality (69 tests, 100%, green CI) | ✅ |
| Trust guardrails designed in | ✅ |
| Privacy stance genuinely honest | ✅ |
| Honest, verifiable stats (fabricated ones removed) | ✅ |
| **Primary hypothesis measured** | 🔴 **No — the biggest gap** |
| **Model quality formally evaluated** | 🔴 **No — spot-checked only** |
| Problem validated with first-party research | 🔴 No — borrowed vendor stat |
| Monetisation tested | ⬜ Not started |

**The candid read:** v1 is a **well-built product and an incomplete experiment.** It proves I can ship something reliable, tasteful and honest — and the three red rows prove exactly where I'd start on Monday. A case study that showed all green would be less credible, not more.

---

## 9. What I learned

1. **Reliability beats intelligence at the point of use.** The 46s→2.5s decision did more for the product than any model upgrade could. Users experience *latency*; they only infer *quality*.
2. **Ship the read-out with the experiment.** A Lean loop without instrumentation is just building. This was v1's real mistake — not a technical one, a methodological one.
3. **Deterministic tests can't see a lying model.** 100% coverage and a fabricated action item coexist happily. AI products need a second, probabilistic gate.
4. **Honest numbers beat impressive ones.** Replacing "12,847 meetings processed" with "~2.5s · 0 OAuth scopes" made the product *more* persuasive and removed a question I couldn't have answered.
5. **Verify the artifact from a stranger's client.** A login wall made a "shipped" demo unreachable — and Streamlit's own apps proved it wasn't my config.
6. **The best decisions serve several goals at once.** The human checkpoint = trust + data + the moat. When one choice does three jobs, the strategy is probably coherent.

---

*Back to: [Case study home](./) · [Vision](01-product-vision.md) · [MRD](02-mrd.md) · [PRD](03-prd.md)*
