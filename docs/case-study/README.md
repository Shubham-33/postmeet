# Postmeet — Product Management Case Study

**Shubham Mittal** · AI Product Manager
🔗 [Live app](https://postmeet.onrender.com/) · [Pitch deck](https://shubham-33.github.io/postmeet/) · [Styled case-study hub](https://shubham-33.github.io/postmeet/case-study/) · [Source](https://github.com/Shubham-33/postmeet)

---

Postmeet turns any meeting transcript into owned, dated action items and pushes each one into the owner's calendar and inbox — **with zero setup and no OAuth**. These are the working product-management documents behind it.

> **How to read this.** These are real working documents, not a highlight reel. They include the decisions I got wrong, the metric I failed to instrument, and the assumptions still waiting on evidence. If you only read two: the **[PRD](03-prd.md)** (how I specify an AI feature) and **[Post-Launch](10-post-launch.md)** (how I judge my own work).

---

## Phase 01 — Ideation

| # | Document | What's in it |
|---|---|---|
| 01 | **[Product Vision](01-product-vision.md)** | Positioning statement, the core insight (friction beats intelligence), north-star metric, three-horizon vision, the data-flywheel moat, explicit non-goals |
| 02 | **[MRD — Market Requirements](02-mrd.md)** | Market problem & evidence, TAM/SAM/SOM with labelled assumptions, personas, competitive map, the honest platform-native risk, 11 numbered market requirements |
| 03 | **[PRD — Product Requirements](03-prd.md)** | Goals, metric tree, user stories, 24 functional requirements, and a full **AI requirements** section: model, output contract, guardrails, evaluation |
| 04 | **[User Guide & Manual](04-user-guide.md)** | Quick start, all input modes, distributing, how the no-OAuth trick works, privacy answers, troubleshooting, FAQ, known limitations |

## Phase 02 — Planning & Strategy

| # | Document | What's in it |
|---|---|---|
| 05 | **[Research Plan](05-research-plan.md)** | 8 research questions ranked by decision risk; JTBD guides with anti-bias rules, diary study, fake doors, analytics taxonomy, golden eval set — each bound to a decision |
| 06 | **[Methodology](06-methodology.md)** | Dual-track Agile, Lean loops, why Kanban over Scrum *here*, RICE (worked example), MoSCoW, OKRs, and **eval-driven development** |
| 07 | **[7P Analysis](07-7p-analysis.md)** | Product · Price · Place · Promotion · People · Process · Physical Evidence — each audited against one strategy |

## Phase 03 — Development & Execution

| # | Document | What's in it |
|---|---|---|
| 08 | **[Development & Execution](08-development-execution.md)** | Architecture, 4 ADRs (incl. shipping the *smaller* model on purpose), quality strategy, the deployment detour, "what I'd do differently" |
| 09 | **[Launch Plan](09-launch-plan.md)** | Staged alpha → beta → public → scale with entry gates and kill criteria, GTM, launch checklist, trust-incident protocol |
| 10 | **[Post-Launch](10-post-launch.md)** | Metric dashboard, vanity metrics deliberately excluded, the correction flywheel, iteration plan, honest scorecard |

---

## The through-line

| | |
|---|---|
| **Insight** | The last mile of meetings is blocked by **setup friction**, not model intelligence. Everyone else competes on capture. |
| **Wedge** | Prefilled Calendar/Gmail URLs → integration-grade value with **zero OAuth**, first visit, no account. |
| **Defining tradeoff** | Shipped **Llama 3.1 8B** (~2.5s consistent) over **70B** (9–46s, timeouts) at comparable quality. *Model quality is an input to product value, not the goal.* |
| **Moat thesis** | Every user correction is labelled, in-domain training data → accuracy compounds with usage. |
| **Honest gap** | The primary metric (Activation) **shipped unmeasured**, and model quality was spot-checked rather than formally evaluated. Both are named, prioritised, and first in the queue. |

---

*🏆 **2nd Runner-Up at PromptWars Chennai 2026** (Google for Developers × Hack2Skill) — [announcement](https://www.linkedin.com/posts/promptwars-chennai-googlefordevelopers-share-7457292011818209281-mB4X/) — then hardened into a portfolio product: 69 tests, 100% line + branch coverage, green CI, live on a public URL.*
