# Methodology — How This Product Gets Built

**Owner:** Shubham Mittal · **Status:** v1.0 · **Phase:** Planning & Strategy
**Related:** [Research Plan](05-research-plan.md) · [PRD](03-prd.md) · [Development & Execution](08-development-execution.md) · [Case study home](./)

---

## 1. Principle: methodology serves the risk, not the ritual

Every framework below is chosen because it de-risks something specific. A team of three pre-PMF does not need SAFe; a product whose core is a probabilistic model **does** need something most Agile playbooks lack entirely — an evaluation track.

**The dominant risk changes by stage, so the method changes with it:**

| Stage | Dominant risk | Method that fits |
|---|---|---|
| Pre-PMF (now) | **Building the wrong thing** | Dual-track Agile, Lean loops, fake doors |
| Post-PMF | Building it too slowly | Scrum/Kanban delivery, DORA |
| Scale | Breaking it | SLOs, incident process, staged rollout |

Postmeet is squarely in row 1. **Everything below optimises for learning speed, not throughput.**

---

## 2. Dual-track Agile — the core operating model

The trap for an AI product is running a delivery sprint on an unvalidated assumption. Dual-track separates *learning* from *building*, running both continuously.

```
DISCOVERY TRACK  ──►  interviews · fake doors · evals · prototypes
   (validate)             │
                          │  only validated, de-risked items pass ▼
                          ▼
DELIVERY TRACK   ──►  ─────────── build · test · ship ───────────►
   (execute)
```

**Rules that make it real:**
1. **Nothing enters delivery without a validated assumption.** The backlog gate is evidence, not enthusiasm.
2. **Discovery runs a sprint ahead** — always feeding the next delivery cycle.
3. **Same team, both tracks.** Handing discovery to a separate research team is how insight dies in a slide.
4. **Discovery has its own output**: validated/invalidated assumptions, not features.

**Applied to Postmeet:** v1 shipped as a *delivery* artifact against an *unvalidated* discovery assumption (the ~70% stat). That's an acceptable hackathon trade and an unacceptable ongoing one. The corrective is [RQ1–RQ4](05-research-plan.md#2-research-questions) running in the discovery track **before** H2 delivery starts.

---

## 3. Lean: build → measure → learn

Each horizon is an experiment with a stated hypothesis and a kill criterion.

| | v1 (H1) |
|---|---|
| **Hypothesis** | If we remove setup friction entirely, users who extract commitments will distribute them. |
| **Build** | Smallest thing that tests it — no auth, no DB, no integrations. |
| **Measure** | **Activation** = distribute ÷ extract. |
| **Learn** | ≥25% → the last mile is the wedge, fund H2. <25% → thesis wrong, **don't tune the model**, re-frame. |

**MVP discipline: an MVP is the cheapest *test*, not the smallest *product*.** That's the reasoning behind every v1 cut ([PRD §3.2](03-prd.md#32-non-goals-v1)) — persistence, accounts and native integrations were removed **because they don't move the hypothesis**, not because they were hard.

> **Honest self-critique:** we built the "build" and skipped the "measure." A Lean loop with no measurement is just building. Fixing that is [PRD Q2](03-prd.md#13-open-questions) / v1.1 P0.

---

## 4. Design Thinking — where it applies

Used for the *interface*, where the problem is human, not technical:

| Stage | Applied to Postmeet |
|---|---|
| **Empathise** | JTBD interviews; the artifact tour ("show me where those action items live") |
| **Define** | "Priya can't get commitments out of her notes and into her team's world without 15 min of retyping" |
| **Ideate** | How might we distribute without integration? → **the URL-prefill insight** |
| **Prototype** | Clickable board; sample transcripts so evaluation needs no setup |
| **Test** | Think-aloud usability (n=5–8): *can they find distribute unaided?* |

The whole no-OAuth wedge came from an **Ideate** constraint — *"assume you can never have an OAuth token; now solve distribution."* Constraint-driven ideation produced the product's only real insight.

---

## 5. Delivery: Kanban over Scrum (for now)

| | Scrum | Kanban | **Choice** |
|---|---|---|---|
| Fixed-length sprints | ✅ | ❌ | |
| Good when scope is stable | ✅ | | |
| Good when priorities shift on new evidence | | ✅ | **← us** |
| Ceremony overhead | Higher | Lower | |

**Choice: Kanban with a WIP limit, plus a fortnightly review.**

**Why:** at this stage, priorities *should* change the moment discovery returns a result. Sprint commitments create pressure to finish work that new evidence has already invalidated — the opposite of what a pre-PMF team needs. Kanban lets us stop work mid-flight when we learn it's pointless.

**When we'd switch to Scrum:** post-PMF, once the roadmap is stable enough that a 2-week commitment isn't a liability, and the team is large enough that cadence beats flexibility.

**Definition of Done (enforced in CI, not by hope):**
- [ ] Acceptance criteria in the PRD story pass
- [ ] Unit tests for new logic; **100% line+branch coverage maintained**
- [ ] Linter clean
- [ ] For prompt/model changes: **eval suite run, no regression**
- [ ] Errors are human-readable — no stack traces reach a user
- [ ] Accessibility: keyboard-complete, AA contrast
- [ ] Docs/README updated if behaviour changed

---

## 6. Prioritisation

### 6.1 RICE — worked example

`RICE = (Reach × Impact × Confidence) ÷ Effort`
*Reach* = users/quarter · *Impact* 0.25–3 · *Confidence* 0–100% · *Effort* = person-weeks.

| Item | R | I | C | E | **RICE** | Call |
|---|---|---|---|---|---|---|
| **Instrument Activation analytics** | 5,000 | 3.0 | 100% | 0.5 | **30,000** | 🥇 Do first |
| Golden eval set + harness | 5,000 | 2.0 | 90% | 2 | **4,500** | 🥈 |
| Browser extension (auto-capture, H2) | 3,000 | 3.0 | 50% | 8 | **563** | 🥉 |
| AI notetaker (auto-join) | 3,000 | 3.0 | 40% | 16 | 225 | Later |
| Outlook / Microsoft support | 1,500 | 2.0 | 60% | 5 | 360 | Later |
| Persistence + accounts | 2,000 | 1.5 | 70% | 4 | 525 | Later |
| Slack/Notion/Jira targets | 1,000 | 1.0 | 60% | 3 | 200 | No |
| Native Calendar/Gmail API (OAuth) | 800 | 1.0 | 70% | 6 | 93 | ❌ Rejected |

**What the numbers expose:** analytics scores **50× the extension** — not because it's exciting, but because it's nearly free, certain, and *unblocks the decision about everything below it*. RICE's real value here is that it makes "the boring instrumentation task beats the exciting AI feature" an argument you can win with a number instead of a preference.

Note also that **native OAuth integration scores lowest** — it's expensive, and it destroys the zero-setup wedge that is the entire strategy. RICE agrees with the strategy; that's a good sign the inputs aren't fudged.

**RICE's limits (stated, because using a framework uncritically is the failure mode):** Confidence is where bias hides — I set the extension to 50% precisely because [fake-door data](05-research-plan.md#43-fake-door-tests) doesn't exist yet. RICE can't score strategic necessity, so it never overrides an explicit strategy call; it informs one.

### 6.2 MoSCoW for release scope

| | v1 |
|---|---|
| **Must** | Extract w/ owner+date · zero setup · one-click Calendar+Gmail · inline edit · no fabrication |
| **Should** | Doc URL · file upload · MoM · samples |
| **Could** | Local persistence · keyboard shortcuts · bulk distribute |
| **Won't (this release)** | Accounts · DB · native APIs · Slack/Notion · mobile apps · auto-capture |

**"Won't" is the load-bearing column.** Writing it down is what stops scope creep from being relitigated weekly.

---

## 7. Goal-setting: OKRs

**Objective — *Prove the last mile is the wedge.*** *(one quarter)*

| KR | Target | Status |
|---|---|---|
| KR1 | Activation (extract → distribute) **≥ 25%** | ⚠️ **Unmeasured** — blocked on instrumentation |
| KR2 | Extraction p95 **< 5s** | ✅ ~2.5s |
| KR3 | Hallucination rate **= 0** across the golden eval set | ⚠️ Eval set not yet built |
| KR4 | ≥15 JTBD interviews; first-party completion rate replaces the borrowed stat | ⬜ Not started |

**Deliberate properties:** KRs are **outcomes, not shipped features** ("Activation ≥25%", never "ship the extension"). KR1 is allowed to fail — an OKR you're certain to hit was a task list. And the ⚠️/⬜ marks stay visible: **an OKR board that's all green is a lying OKR board.**

---

## 8. Eval-driven development — the AI-specific addition

Standard Agile has no answer for "the code is correct but the *output* is wrong." Deterministic tests can't catch a model that starts inventing action items — the function returns valid JSON, and the JSON is a lie.

**So the pipeline has a second gate:**

```
Code change ──► unit tests (deterministic)   ──► ✅/❌
Prompt or model change ──► unit tests
                       └─► EVAL SUITE (probabilistic) ──► precision/recall deltas ──► ✅/❌
```

**Rules:**
1. **The system prompt is production code.** It is versioned, reviewed, and cannot change without an eval run.
2. **No model swap without an eval delta.** ([ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback) predates this rule — which is exactly why it's flagged as a gap in [PRD §7.4](03-prd.md#74-evaluation).)
3. **Precision is weighted over recall** — asymmetric costs (MR-3).
4. **Production edit-rate is a live eval** — free, continuous quality signal with no labelling ([Research §4.1](05-research-plan.md#41-product-analytics--the-cheapest-and-most-important)).

This is the single biggest methodological difference between shipping an AI product and shipping software, and it's the part most teams discover only after a trust incident.

---

## 9. What I'd change next time

An honest retro on the method itself:

| What happened | The lesson |
|---|---|
| Shipped v1 with **no analytics** | The Lean loop lost its "measure." Instrumentation isn't a feature — it's the experiment's read-out. It should have been in the Definition of Done. |
| Model chosen on **latency + spot-check**, not an eval set | Right call, insufficient evidence. Under a hackathon clock it's defensible; as a habit it's how trust incidents happen. |
| Built before validating the **~70% stat** | Acceptable for a time-boxed prototype. Unacceptable as a basis for H2 spend — hence RQ1 gating H2. |
| Cut scope aggressively and stated the cuts | Worked. The "Won't" column is why v1 shipped and stayed testable. |

---

*Next: [7P Analysis →](07-7p-analysis.md)*
