# Market Requirements Document (MRD) — Postmeet

**Owner:** Shubham Mittal · **Status:** v1.0 · **Phase:** Ideation
**Related:** [Vision](01-product-vision.md) · [PRD](03-prd.md) · [7P Analysis](07-7p-analysis.md) · [Case study home](./)

> **Scope note.** An MRD describes **what the market needs and why it's worth serving** — it deliberately does *not* specify implementation. The "how" lives in the [PRD](03-prd.md).

---

## 1. Executive summary

Knowledge workers run an enormous volume of meetings, and a large share of the commitments made in them are never completed. A crowded field of AI meeting tools has driven **capture** (transcription + summarisation) to commodity quality, but the **last mile** — moving a commitment into the owner's calendar and inbox — remains unsolved, because solving it conventionally requires integrations gated behind OAuth and IT approval.

Postmeet addresses the last mile with a **zero-setup distribution wedge**, delivering integration-grade value with no authentication. The recommendation is to enter via a **PLG, bottom-up motion** aimed at meeting-heavy team leads in tech-forward SMBs, and to earn defensibility through a correction-driven data flywheel rather than through the (copyable) wedge itself.

---

## 2. Market problem

### 2.1 The pain

Meetings manufacture commitments — "I'll have the PR ready by Friday," "I'll set up the QA channel." These are verbal, ephemeral, and captured (if at all) in prose notes. The work, however, lives somewhere else entirely: a calendar, an inbox, a tracker. **Nothing reliably carries the commitment across that boundary**, so follow-through depends on individual discipline.

### 2.2 Evidence

| Claim | Source / status |
|---|---|
| A large share of meeting action items are never completed — cited figures range **~44–73%** | Industry/vendor sources (Fellow, Streamli9). **Directional, not peer-reviewed.** |
| Meeting volume among knowledge workers is high and rose with remote/hybrid work | Widely reported; directionally uncontroversial |
| The AI meeting-assistant category is crowded and well-funded | Observable: Otter, Fireflies, Fathom, Granola, Read.ai, plus platform-native (Zoom AI Companion, Microsoft Copilot) |

> ⚠️ **Assumption risk — flagged deliberately.** The headline "~70%" is a *vendor-sourced* range, not rigorous research. It is strong enough to justify **investigating** the problem; it is **not** strong enough to justify a roadmap. The [Research Plan](05-research-plan.md) treats validating this — with first-party instrumentation and JTBD interviews — as **Research Question 1**. Building on an unvalidated headline stat is exactly the failure mode this document is meant to prevent.

### 2.3 Root cause

The problem is **not** an information problem (the notes exist). It is a **transfer** problem. And the conventional fix — integrate with the calendar/mail system — collides with an adoption tax:

```
Integration → OAuth consent → security review → admin approval → rollout
                                    ↑
                       most users never get past here
```

The insight driving Postmeet: **the last mile is blocked by setup friction, not by model capability.**

---

## 3. Market sizing

> **Methodology note.** These are **assumption-driven estimates built top-down, with every assumption labelled.** No first-party data exists at this stage. The purpose is to establish an order of magnitude ("is this a business?"), not false precision. A real sizing exercise would triangulate top-down with a bottom-up build from actual funnel data.

**Assumptions (all challengeable):**

| # | Assumption | Value | Confidence |
|---|---|---|---|
| A1 | Global knowledge workers | ~1.0B | Medium (widely cited range 0.8–1.25B) |
| A2 | Share in meeting-heavy, decision-making roles who'd plausibly pay | ~15% | **Low** — needs research |
| A3 | Reachable via English-language, self-serve, Google/Microsoft-centric tooling | ~35% of A2 | Low |
| A4 | Realistic 3-yr capture of the reachable segment for a new entrant | ~1% | Low |
| A5 | Blended ARPU (freemium mix, see [7P §2](07-7p-analysis.md#2-price)) | ~$60/user/yr | Medium |

**Resulting funnel:**

| Layer | Definition | Math | Estimate |
|---|---|---|---|
| **TAM** | All knowledge workers who attend commitment-generating meetings | 1.0B × 15% (A1×A2) | **~150M users** → ~$9.0B/yr @ $60 ARPU |
| **SAM** | Those reachable by our product/channel today (English, self-serve, Google/MS ecosystem) | 150M × 35% (A3) | **~52M users** → ~$3.1B/yr |
| **SOM** | Credible 3-year capture | 52M × 1% (A4) | **~525K users** → **~$31M ARR** |

**Interpretation:** even under conservative assumptions this clears the "is it a venture-scale market?" bar by an order of magnitude. **The binding constraint is not market size — it is differentiation in a crowded category.** That reframes the strategic question from *"is the market big enough?"* to *"can we own a defensible slice of it?"* — which §5 and §7 address.

---

## 4. Personas

### 4.1 Primary — "Priya," the Meeting Owner

| | |
|---|---|
| **Role** | Engineering Manager / Team Lead / Chief-of-staff, 25–45, tech-forward SMB or scale-up |
| **Context** | Runs 8–20 meetings/week: standups, planning, retros, 1:1s. Accountable for outcomes she doesn't personally execute. |
| **Job to be done** | *"When a meeting ends, help me make sure every commitment lands with its owner, so I don't have to chase people or re-litigate what we agreed."* |
| **Current workaround** | Takes notes → manually retypes action items into Slack/Jira/email → chases in the next standup. 10–20 min of post-meeting admin per meeting. |
| **Pain** | The admin tax is boring and skippable; when she skips it, things silently drop. Chasing costs her credibility and goodwill. |
| **Success** | Zero post-meeting retyping; commitments visible to owners without her nagging. |
| **Buying power** | Can adopt a free tool unilaterally; can expense a team plan (~$10–20/user/mo) without procurement. **This is why she's primary.** |

### 4.2 Secondary — "Marcus," the Assignee

| | |
|---|---|
| **Role** | IC engineer/designer/analyst |
| **JTBD** | *"When I agree to something in a meeting, put it where I'll actually see it, so I don't drop it."* |
| **Pain** | Agrees verbally, then it lives only in someone else's notes. Discovers it was due yesterday. |
| **Success** | The commitment appears in his calendar with a date and context, without him doing anything. |
| **Note** | Marcus never has to install Postmeet — he receives a normal Google Calendar invite / Gmail. **This is a distribution advantage: the product spreads to people who aren't users.** |

### 4.3 Anti-persona — "Dana," the Enterprise IT Admin

Not a target at H1. Dana requires SSO, DPAs, data residency, admin controls, and a security review. Serving Dana at H1 would mean building the entire compliance apparatus *before* proving the loop. **Deliberately deferred** — but she becomes the gatekeeper at H2/H3, so the architecture shouldn't foreclose her (see [PRD §8](03-prd.md#8-non-functional-requirements)).

---

## 5. Competitive landscape

### 5.1 The field

| Player | Core bet | Strength | Gap Postmeet exploits |
|---|---|---|---|
| **Otter.ai** | Transcription at scale | Brand, accuracy, mature | Output is a transcript/summary; action items are a list, not distributed work |
| **Fireflies.ai** | Notetaker + CRM/tool integrations | Broad integrations, search | Integrations require OAuth + admin approval → setup tax |
| **Fathom** | Free, fast meeting summaries | Excellent UX, generous free tier | Same last-mile gap; summary-centric |
| **Granola** | AI notepad that augments *your* notes | Beloved UX, low friction | Deliberately personal/notes-first; not a distribution layer |
| **Read.ai** | Meeting analytics + coaching | Unique angle (engagement metrics) | Analytics ≠ action |
| **Zoom AI Companion / MS Copilot** | Platform-native summaries | **Zero install; already in the meeting** | Locked to one platform; generic action lists; no cross-tool distribution |

### 5.2 The strategic map

The whole category clusters on one axis — **how well do you capture the meeting?** Almost no one competes on **how reliably does the commitment get done?**

```
                 HIGH follow-through
                          │
                          │        ◆ Postmeet
                          │          (the open quadrant)
                          │
  LOW capture ────────────┼──────────────── HIGH capture
                          │   ◆ Otter  ◆ Fireflies
                          │   ◆ Fathom ◆ Granola
                          │   ◆ Copilot / Zoom AI
                          │
                 LOW follow-through
```

### 5.3 The honest competitive risk

**Platform-native tools (Copilot, Zoom AI) are the existential threat, not Otter.** They are already inside the meeting, cost nothing extra, and require zero adoption decision. If Microsoft ships "turn these action items into Outlook tasks + calendar invites," the wedge evaporates.

**Why we can still win a slice:**
1. **Cross-platform.** Teams don't live on one meeting platform; Copilot won't serve a Zoom call well. Postmeet is platform-agnostic by construction.
2. **Distribution beats summarisation.** Platform tools optimise for the meeting; we optimise for the *commitment lifecycle* across tools.
3. **Speed of the wedge.** Zero-setup lets us reach users the platforms' admin-gated rollouts take quarters to reach.
4. **The flywheel.** Correction data on *follow-through specifically* compounds in a way a generic assistant's doesn't.

**Mitigation:** treat H2 (auto-capture) and H3 (completion tracking) as the real product; the H1 wedge exists to buy the data and the users to get there. **If the flywheel doesn't start, this is a feature, not a company** — that is the central strategic risk, and it's stated here rather than buried.

---

## 6. Market trends

| Trend | Implication for Postmeet |
|---|---|
| Extraction-grade LLMs are now cheap, fast, and small (8B-class does this task in ~2.5s) | Unit economics are trivial; model capability is **not** the differentiator. Reinforces "friction, not intelligence." |
| Capture is commoditising; every platform ships a free summariser | Do **not** compete on capture. Confirms the last-mile positioning. |
| Shift from "AI that tells you things" → "AI that does things" (agentic) | Postmeet is natively on the right side of this: it produces *actions*, not prose. |
| Buyers increasingly resist new OAuth scopes and vendor sprawl | The zero-OAuth wedge is a **security-posture advantage**, not just a UX one. |
| Hybrid work keeps meeting volume structurally high | Problem is durable, not a fad. |

---

## 7. Business case

**Model:** freemium, product-led, bottom-up. (Tiers and pricing rationale: [7P §2](07-7p-analysis.md#2-price).)

| Element | Position |
|---|---|
| **Free tier** | Unlimited paste-based extraction. Costs ~fractions of a cent per extraction; buys the top of the funnel and the correction data. |
| **Paid trigger** | Auto-capture (H2 extension/notetaker), persistence, team workspaces — i.e. we charge to *remove the remaining friction*, not to unlock the core value. |
| **Land** | Individual lead adopts free, unilaterally, in <1 min. |
| **Expand** | Assignees receive invites → become aware → team plan. Marcus is a growth channel. |
| **Gross margin** | Very high; inference is the only variable cost and it's ~$0.0001-class per extraction at 8B. |
| **Key risk** | Free tier is *so* useful that conversion stalls. Mitigation: gate on friction-removal (auto-capture), which is precisely what heavy users want most. |

---

## 8. Market requirements

> Numbered, testable, implementation-free. The [PRD](03-prd.md) maps each to a functional requirement.

| ID | Requirement | Rationale | Priority |
|---|---|---|---|
| **MR-1** | A user must reach first value without creating an account or granting any permission | Setup friction is the root cause (§2.3); time-to-value is the wedge | **Must** |
| **MR-2** | The system must extract commitments with an explicit owner and a due date, not just a prose summary | An action item without an owner/date is not actionable — it's a note | **Must** |
| **MR-3** | The system must never fabricate a commitment that wasn't made | Trust is asymmetric: one hallucination costs more than ten misses | **Must** |
| **MR-4** | Each commitment must be deliverable into the owner's calendar and inbox in one action | This *is* the last mile | **Must** |
| **MR-5** | The user must be able to correct any extracted field before anything is sent | Humans are the checkpoint; also the source of flywheel data | **Must** |
| **MR-6** | Results must return fast enough to feel synchronous (target < 5s) | Post-meeting attention is a closing window | **Must** |
| **MR-7** | Recipients must not need to install or sign up for anything | Assignees are a distribution channel, not a conversion cost | **Must** |
| **MR-8** | The system must accept meeting content from wherever it already lives | Transcripts arrive in many forms; forcing one is friction | **Should** |
| **MR-9** | No meeting content should be retained without explicit user intent | Removes the privacy objection at adoption | **Should** |
| **MR-10** | The system should capture transcripts without manual paste | The remaining friction after H1; the paid trigger | **Could** (H2) |
| **MR-11** | The system should know whether a commitment was completed | Required to measure/serve the north star | **Could** (H3) |

---

## 9. Risks & assumptions

| # | Risk / assumption | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | The ~70% stat doesn't survive first-party validation; the pain is real but tolerable | **High** — invalidates premise | Medium | RQ1 in [Research Plan](05-research-plan.md); validate before H2 investment |
| R2 | Platform-native (Copilot/Zoom) ships the last mile | **High** | Medium–High | Cross-platform + flywheel; move fast to H2/H3 |
| R3 | The URL-prefill wedge is trivially copyable | Medium | **High** | Accept it. The wedge is for entry, not defence; the moat is the correction corpus |
| R4 | Users extract but don't distribute (loop breaks at the last step) | **High** — kills the thesis | Medium | This is the #1 thing H1 instrumentation must measure (Activation) |
| R5 | Free tier cannibalises conversion | Medium | Medium | Gate on auto-capture/persistence, not core extraction |
| R6 | Google changes/deprecates the Calendar/Gmail URL specs | **High** — breaks distribution | Low | Long-stable public specs; H2 native APIs are the structural hedge |
| R7 | Extraction quality is unacceptable on real (messy, multi-speaker) transcripts vs clean samples | High | **Medium–High** | Golden eval set on *real* transcripts, not curated samples ([Research Plan §5](05-research-plan.md#5-ai-specific-research-evaluation)) |

---

## 10. Recommendation

**Proceed to H1 build** — but treat it as an **experiment with a kill criterion**, not a product launch.

- **Validate first:** RQ1 (is the pain real and severe?) and R4 (does the loop actually close?).
- **Kill/pivot criterion:** if **Activation (extract → distribute ≥1 item) < 25%** in the first cohort, the last-mile thesis is wrong and no amount of model quality fixes it.
- **Invest in H2 only** once the loop is proven, because auto-capture is where the cost — and the paid conversion — actually sits.

---

*Next: [PRD — what we're building →](03-prd.md)*
