# Product Vision — Postmeet

**Owner:** Shubham Mittal · **Status:** Living document · **Phase:** Ideation
**Related:** [MRD](02-mrd.md) · [PRD](03-prd.md) · [Case study home](./)

---

## 1. Vision statement

> **Every commitment made in a meeting lands in the owner's world before the meeting ends — and gets done.**

Meetings are where organisations make decisions and assign ownership. They are also where that ownership quietly dies. Postmeet's vision is to close the gap between *"we agreed"* and *"it happened"* — not by recording meetings better, but by making the resulting commitments impossible to lose.

## 2. Positioning statement

Using Geoffrey Moore's format:

> **For** teams who run recurring, decision-heavy meetings
> **who** lose track of the commitments made in them,
> **Postmeet** is a meeting-to-action tool
> **that** turns any transcript into owned, dated action items and pushes each one into the owner's calendar and inbox in a single click.
> **Unlike** Otter, Fireflies, Fathom and Granola — which compete on capturing and summarising meetings —
> **Postmeet** starts where they stop: the last mile of distribution, with **zero setup and no OAuth**.

## 3. Mission

Make follow-through the default outcome of a meeting, not an act of individual discipline.

## 4. The problem we're solving

| | |
|---|---|
| **Observed pain** | Commitments made verbally in meetings are captured in notes, then never actioned. Industry estimates put the share of meeting action items never completed at **~44–73%** (see [MRD §2](02-mrd.md#2-market-problem)). |
| **Why it persists** | Capture ≠ action. Notes live in a doc; work lives in a calendar and an inbox. Nothing carries a commitment across that boundary. |
| **Why now** | LLMs made reliable extraction of structured commitments from unstructured speech cheap and fast (~2.5s, fractions of a cent). The bottleneck moved from *understanding* the meeting to *acting* on it. |
| **Why it stays unsolved** | Incumbents optimise the part that demos well (transcript quality). The last mile requires integrations, which require OAuth, admin approval and security review — a setup tax that kills adoption before value is ever felt. |

## 5. The core insight

**The blocker on the last mile isn't model intelligence — it's setup friction.**

This drives the wedge: Google Calendar and Gmail both accept fully **prefilled actions via URL**. Postmeet exploits this to deliver integration-grade value with **zero authentication**. A user goes from a raw transcript to a saved calendar invite in ~10 seconds, on their first visit, without creating an account.

That is the strategic bet: **time-to-value is the moat at the wedge stage**, and everything else (accounts, integrations, persistence) is deferred until the loop is proven.

## 6. Target user

**Primary:** the *meeting owner* — an EM, PM, chief-of-staff, or team lead who runs 8–20 meetings a week and is accountable for the outcomes.
**Secondary:** the *assignee* — the person who receives a prefilled invite/email and does the work.

Full personas in [MRD §4](02-mrd.md#4-personas).

## 7. North-star metric

> **Commitment Completion Rate (CCR)** — of the action items Postmeet surfaces, the share that are actually completed by their due date.

**Why this one:** it is the only metric that goes up *only if the product delivers the promise*. Extractions, sends and MAU can all rise while follow-through stays broken. CCR cannot.

**Honest caveat:** CCR is not directly observable at v1 (we don't yet own completion state). Until Horizon 3 (completion tracking) closes the loop, we steer on the input funnel — **Activation (extract → distribute)**, **time-to-value**, and **extraction precision/recall** — which are leading indicators of CCR. Full metric tree in [PRD §4](03-prd.md#4-success-metrics).

## 8. Three-horizon vision

| Horizon | Timeframe | Product | Strategic purpose |
|---|---|---|---|
| **H1 — Validate the loop** *(shipped)* | Now | Paste / Doc / file → extract → one-click distribute. No setup, no OAuth, no storage. | Prove people will extract **and then distribute**. Cheapest possible test of the core hypothesis. |
| **H2 — Kill the paste step** | 6–12 mo | Browser extension + AI notetaker that auto-joins Zoom / Teams / Meet and pulls the transcript itself. Native send via Gmail, Outlook, Calendar. Persistence + team workspaces. | Remove the last manual step. Move from "a tool I remember to use" to "a thing that just happens." |
| **H3 — Own the outcome** | 12–24 mo | Completion tracking, proactive nudges ("did you ship X?"), commitment history per person/team, follow-through analytics. | Close the north-star loop. Become the **system of record for follow-through**, not a utility. |

## 9. The moat

At H1 there is no moat — the URL trick is copyable in a week. The defensibility thesis is a **data flywheel**:

```
extract → user edits before sending → edits are labelled corrections
   → fine-tune / few-shot on accepted output → accuracy rises
   → more trust → more extractions → more labels ──┐
   └──────────────────────────────────────────────┘
```

Every correction a user makes is free, in-domain, human-labelled training data on *exactly* the task. An incumbent can copy the feature; they cannot copy the corpus of "what this org's commitments actually look like." Compounding accuracy on org-specific language (project names, people, cadences) is what makes H3 defensible.

## 10. Product principles

1. **Time-to-value beats feature depth.** Anything that delays the first "wow" past ~30 seconds is suspect.
2. **Never invent a commitment.** A hallucinated action item destroys trust permanently; a missed one costs one edit. Bias to precision.
3. **The user is the last checkpoint.** Everything is editable before it is sent. We draft; humans send.
4. **Reliability > model size.** A fast, consistent answer beats a marginally better one that sometimes hangs. (See [the model decision](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback).)
5. **Earn the right to store data.** Statelessness is a feature at H1 — no data, no privacy objection, no adoption blocker.

## 11. Non-goals (explicitly not building)

| Non-goal | Rationale |
|---|---|
| Best-in-class transcription | Commodity, capital-intensive, and not where the pain is. We consume transcripts; we don't produce them (until H2's notetaker, and even then via existing ASR). |
| A general project-management tool | Jira/Asana/Linear own this. Postmeet feeds them; it does not replace them. |
| A meeting *recorder* brand | Recording is the crowded lane. We're the action layer. |
| Enterprise admin/SSO at H1 | Real requirement — deferred until segments demand it. Building it early is the classic pre-PMF trap. |

## 12. What success looks like

**In 12 months:** teams stop copying action items out of meeting notes by hand, because the invite is already in their calendar before they've left the call.
**In 3 years:** "Did we ever close that out?" is answerable from data, and CCR is a metric teams track like they track velocity.

---

*Next: [MRD — the market case →](02-mrd.md)*
