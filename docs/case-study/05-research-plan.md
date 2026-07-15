# Research Plan — Postmeet

**Owner:** Shubham Mittal · **Status:** v1.0 · **Phase:** Planning & Strategy
**Related:** [MRD](02-mrd.md) · [PRD](03-prd.md) · [Methodology](06-methodology.md) · [Case study home](./)

---

## 1. Why this document exists

v1 was built on a **hypothesis**, not on evidence: that meeting commitments are frequently dropped, and that the blocker on fixing it is *setup friction* rather than *model quality*. That hypothesis is plausible and it is **unvalidated**.

This plan states what we don't know, in priority order, and the cheapest honest way to find out. **The governing principle: match research spend to decision risk.** We do not run a study to learn something an instrumented button click would tell us for free.

---

## 2. Research questions

Ordered by *how much damage being wrong causes*.

| # | Question | If we're wrong… | Method | Priority |
|---|---|---|---|---|
| **RQ1** | Is the pain real and *severe* for our segment — or is it real but tolerable? | The premise collapses. Everything downstream is wasted. | JTBD interviews + survey | **P0** |
| **RQ2** | Will people who extract actually **distribute**? | The last-mile thesis is wrong; we built the wrong wedge. | **Product analytics** (Activation) | **P0** |
| **RQ3** | Is setup friction genuinely the blocker, or do people not adopt for other reasons (trust, habit, "my notes are fine")? | The zero-OAuth wedge solves a non-problem. | JTBD interviews + fake-door | **P0** |
| **RQ4** | Is extraction good enough on **real, messy** transcripts (not our clean samples)? | Trust breaks on first real use; churn at the moment of truth. | Golden eval set | **P0** |
| **RQ5** | What triggers willingness to pay — auto-capture, persistence, or teams? | We gate the wrong thing and conversion stalls. | Pricing survey + fake-door | P1 |
| **RQ6** | Do users trust bulk-send, or do they send item-by-item? | Mis-scoped H2 UX. | Analytics + usability | P1 |
| **RQ7** | Does the correction flywheel produce usable training signal at real volume? | The moat thesis fails; we're a feature. | Data analysis (H2+) | P1 |
| **RQ8** | Who actually decides/pays — the lead, or IT? | Wrong GTM motion. | Interviews | P2 |

> **RQ1–RQ3 are the ones that could kill the product.** They come first, and no H2 investment is justified until they're answered.

---

## 3. Discovery research *(is the problem real?)*

### 3.1 JTBD interviews — **the highest-value study**

| | |
|---|---|
| **Goal** | RQ1, RQ3, RQ8 |
| **Who** | n = 15–20. Meeting-heavy leads (EM / PM / chief-of-staff / team lead), 8+ meetings/week, tech-forward SMB or scale-up. **Two contrast groups:** 12–15 who feel the pain, **plus 5 who say follow-through is fine** — disconfirming cases are where you learn you're wrong. |
| **Screener** | "How many meetings did you attend last week?" (≥8) · "Who's accountable when a meeting action item doesn't get done?" (them) · **Exclude** anyone who works on meeting-AI tools. |
| **Format** | 45 min, remote, semi-structured, recorded with consent. |
| **Sample size logic** | Thematic saturation for a narrow, homogeneous segment typically lands at 12–15; 20 buys headroom for the contrast group. |

**Interview guide — retrospective, not hypothetical:**
1. *"Walk me through your last meeting that produced commitments. What happened after it ended?"* (behaviour, not opinion)
2. *"Show me where those action items live right now."* (artifact tour — reveals the real workaround)
3. *"Tell me about the last time something agreed in a meeting got dropped. What happened?"* (severity, consequence)
4. *"What did you do about it?"* (is there a workaround they're happy with?)
5. *"What have you tried?"* (Otter/Fireflies? Why did it stick or not?) → **RQ3**
6. *"If it were solved tomorrow, what changes for you?"* (value)

**Anti-bias rules — non-negotiable:**
- ❌ Never describe Postmeet before the problem section. Never ask *"would you use a tool that…"* — that measures politeness, not demand.
- ✅ Ask about the **last time**, not the general case. Memory of specifics beats self-theorising.
- ✅ **Chase the disconfirming answer.** If someone says follow-through isn't a problem, dig hard — that's the most valuable interview in the set.
- ✅ Separate the moderator from the builder where possible; I am the most biased person in the room about this product.

**Analysis:** thematic coding → JTBD statements → severity × frequency map.
**Decision rule:** if **fewer than ~60%** describe a *specific, recent, consequential* drop unprompted, the pain is **tolerable**, not burning → **pivot or stop**, do not proceed to H2.

### 3.2 Artifact / diary study

| | |
|---|---|
| **Goal** | RQ1 severity, quantified without self-report bias |
| **Method** | n = 5–8, two weeks. Participants forward their meeting notes and log each commitment + whether it was done by the due date. |
| **Output** | A **first-party** completion rate — the number that replaces the borrowed "~70%." |
| **Why it matters** | This is the single study that converts our headline stat from vendor-sourced to evidence ([MRD §2.2](02-mrd.md#22-evidence)). |

### 3.3 Competitive teardown

| | |
|---|---|
| **Goal** | RQ3, positioning |
| **Method** | Hands-on: sign up for Otter, Fireflies, Fathom, Granola, Zoom AI Companion, Copilot. **Time-to-first-value stopwatch** on each. Log every permission requested and every admin gate hit. |
| **Output** | A friction ledger proving (or disproving) the setup-tax claim, and a defensible positioning map ([MRD §5.2](02-mrd.md#52-the-strategic-map)). |
| **Note** | If a competitor's TTFV is already <60s with no admin gate, **our core insight is wrong** and we should know that in a day, for free. |

---

## 4. Validation research *(are we building the right thing?)*

### 4.1 Product analytics — **the cheapest and most important**

RQ2 is answerable by instrumentation, not interviews. **This is v1's biggest gap** ([PRD §4.2](03-prd.md#42-targets--instrumentation)): the primary hypothesis currently has no measurement.

**Minimal, privacy-preserving event taxonomy** (aggregate counts only, **no meeting content**, cookieless — compatible with the stateless privacy promise in [PRD NFR-5](03-prd.md#8-non-functional-requirements)):

| Event | Properties | Answers |
|---|---|---|
| `session_start` | — | Denominator |
| `input_mode_selected` | paste \| doc \| upload \| sample | Which input matters (FR priority) |
| `extract_attempt` | char_count_bucket | Funnel top |
| `extract_success` | latency_ms, item_count, decision_count | NFR-1, quality proxy |
| `extract_error` | error_type | Failure rate |
| `field_edited` | field_name | **Edit rate → extraction quality proxy** |
| `distribute_click` | kind (calendar\|email\|mom\|bulk) | **RQ2 — Activation** |
| `session_end` | duration | Time-to-value |

**The one number that matters:** `distribute_click` ÷ `extract_success` = **Activation**. Target ≥25%. Below that, the thesis is dead.

**Secondary insight:** `field_edited` by field name is a *free, continuous* proxy for model quality in production — if `owner_email` is edited 60% of the time, FR-10 (email matching) is broken, and no eval set was needed to learn it.

### 4.2 Prototype usability testing

| | |
|---|---|
| **Goal** | RQ6; friction inside the flow |
| **Method** | n = 5–8 moderated, think-aloud. Task: *"You just ran this meeting. Get everyone their action items."* Then say nothing. |
| **Watch for** | Do they find distribute unaided? Do they trust output enough to send? Do they edit first? Do they understand nothing is auto-sent? |
| **Rationale** | 5 users surface ~80% of severe usability issues; this is a cheap, high-yield study. |

### 4.3 Fake-door tests

| | |
|---|---|
| **Goal** | RQ3, RQ5 — demand for unbuilt things, before building them |
| **Method** | Add non-functional entry points: **"Connect Zoom"**, **"Connect Outlook"**, **"Auto-join my meetings"**. Clicking → *"Coming soon — want early access?"* + email capture. |
| **Reads** | Click rate = demand signal for H2. Email-leave rate = intensity. **Ranks H2 scope with real behaviour instead of opinion.** |
| **Ethics** | Honest "coming soon," genuine waitlist, no dark patterns, no fake charges. |

### 4.4 Pricing research

| | |
|---|---|
| **Goal** | RQ5 |
| **Method** | **Van Westendorp** (4 price-sensitivity questions) on the beta list + fake-door on tier gates. |
| **Caveat** | Stated pricing is weak evidence. Treat it as a **range-finder** to design the real test (a live paywall), not as an answer. |

---

## 5. AI-specific research: evaluation

> **"Vibes don't scale."** v1's model decision was made on measured latency plus spot-checked quality — defensible under a hackathon clock, **not** defensible going forward ([PRD §7.4](03-prd.md#74-evaluation)).

### 5.1 Golden eval set

| | |
|---|---|
| **Goal** | RQ4 — the model-quality question |
| **Build** | 50–100 transcripts, **two human labellers**, adjudicated disagreements. Each labelled with ground-truth decisions + action items (task, owner, email, date). |
| **Composition — this is the whole point** | Deliberately **not** clean samples: multi-speaker crosstalk · unattributed pronouns ("I'll take that") · vague non-commitments (the **precision** traps) · no-deadline items · non-English names · very long meetings · meetings with **zero** action items (must return empty, not invent) |
| **Why** | Our samples are curated and flatter the model. Real transcripts are messy. [MRD R7](02-mrd.md#9-risks--assumptions) is a Medium-High risk precisely here. |

### 5.2 Metrics

| Metric | Definition | Target | Why |
|---|---|---|---|
| **Precision** | correct items ÷ items returned | **≥ 0.95** | Fabrication destroys trust asymmetrically (MR-3) |
| **Recall** | correct items ÷ true items | ≥ 0.80 | A miss costs one edit — recoverable |
| **Owner accuracy** | correct owner ÷ items | ≥ 0.90 | Wrong owner = wrong person emailed = embarrassing |
| **Date accuracy** | correct date ÷ dated items | ≥ 0.85 | Known weak spot; mitigated by editability |
| **Email accuracy** | correct email ÷ emailed items | ≥ 0.95 | Wrong address = a real leak |
| **Hallucination rate** | fabricated ÷ 100 items | **0** | Non-negotiable |
| **Empty-case correctness** | returns empty on no-commitment transcripts | 100% | The classic over-eager-model failure |

**Precision is weighted above recall by design.** These are asymmetric errors: a missed item costs one edit; a fabricated item ("Marcus said he'd do X" — he didn't) costs trust permanently and can't be undone once emailed.

### 5.3 How the eval is used

1. **Gate model changes.** No swap (8B ↔ 70B ↔ anything) without an eval delta. This retroactively upgrades [ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback) from "measured latency + spot check" to a defensible decision.
2. **Regression-guard prompts.** The system prompt is production logic; changing it must run the eval, in CI.
3. **Set the launch bar.** Precision <0.95 → don't ship.
4. **Seed the flywheel.** The labelling rubric here is the same schema production corrections produce → the eval set and the training corpus are the same asset ([Vision §9](01-product-vision.md#9-the-moat)).

### 5.4 Ongoing / production evaluation

- **Edit rate by field** as a live quality signal (§4.1) — free, continuous, no labelling.
- **Shadow evaluation:** run a candidate model on real traffic, compare outputs offline, ship only on a win.
- **Regression cadence:** full eval on every prompt/model change; automated in CI.

---

## 6. Sequencing & cost

| Phase | Studies | Duration | Cost | Gate |
|---|---|---|---|---|
| **0 — Free wins** | Competitive teardown · **instrument analytics** | 1 week | ~$0 | Do this first. RQ2 becomes answerable, RQ3 partly answered, for nothing. |
| **1 — Problem validation** | JTBD interviews (n=15–20) · diary study (n=5–8) | 3–4 weeks | Incentives (~$50–75/participant) | **RQ1 gate: ≥60% report a specific, consequential drop → proceed. Else pivot.** |
| **2 — Quality validation** | Golden eval set + harness | 2 weeks | Labelling time | **RQ4 gate: precision ≥0.95 → proceed** |
| **3 — Solution validation** | Usability (n=5–8) · fake-doors live | 2 weeks | ~$0 | **RQ2 gate: Activation ≥25% → fund H2** |
| **4 — Monetisation** | Van Westendorp · tier fake-doors | 2 weeks | Low | RQ5 → pricing design |

**Total to a defensible go/no-go on H2: ~8–10 weeks.**

> **Note the ordering.** The free/cheap studies (teardown, analytics) run *first* — they can invalidate the premise before a single participant is recruited. Expensive research is a last resort, not an opening move.

---

## 7. How findings change decisions

Research that can't change a decision shouldn't be run. Every study above is bound to one:

| Finding | Decision |
|---|---|
| RQ1 fails (<60% report severe, specific drops) | **Stop / pivot.** Do not build H2. The problem is tolerable. |
| RQ2 fails (Activation <25%) | **The last-mile thesis is wrong.** Don't tune the model — re-examine the hypothesis. |
| RQ3 fails (friction isn't the blocker) | Wedge is wrong → re-position; the zero-OAuth advantage is worthless. |
| RQ4 fails (precision <0.95 on messy input) | **Quality is the gate, not distribution.** Escalate to 70B or fine-tune; delay H2. |
| RQ4 passes *and* 8B ≈ 70B on messy input | Keep the fast primary — [ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback) confirmed with evidence. |
| Fake-door: Zoom ≫ Outlook | Sequence H2 auto-capture by that ranking, not by intuition. |
| RQ5: auto-capture is the willingness-to-pay trigger | Gate paid on H2 features; keep extraction free forever. |

---

## 8. What I'd do first with a real budget

If I owned this on day one with a team, in order:

1. **Instrument Activation** (1 week, ~$0). The primary hypothesis is currently unmeasured. Everything else is guessing until this exists.
2. **Competitive teardown** (2 days, ~$0). Could invalidate the core insight immediately.
3. **JTBD interviews** (3 weeks). The only way to know if the pain is severe or merely real.
4. **Golden eval set** (2 weeks). Converts the model decision from an anecdote into evidence.

Notice that **the two highest-value actions are nearly free** — and that the most expensive one (interviews) is third. That ordering *is* the research strategy.

---

*Next: [Methodology →](06-methodology.md)*
