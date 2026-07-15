# 7P Marketing Mix Analysis — Postmeet

**Owner:** Shubham Mittal · **Status:** v1.0 · **Phase:** Planning & Strategy
**Related:** [MRD](02-mrd.md) · [Vision](01-product-vision.md) · [Launch Plan](09-launch-plan.md) · [Case study home](./)

---

## How to read this

The 7Ps (Booms & Bitner's extension of the 4Ps for **services**) are a completeness check: they force you to notice that a product is not just the software — it's the price, the channel, the people and the process around it.

**The extended three (People, Process, Physical Evidence) matter most here**, because Postmeet is a service delivered through an interface, and its output is *artifacts other people receive*.

> **Position first, then the mix.** Everything below descends from one strategic choice:
> **Postmeet competes on the last mile (distribution), not on capture — and wins entry through zero setup.**
> Any P that contradicts that is wrong, no matter how attractive it looks in isolation.

---

## 1. Product

**What is actually being sold:** not "AI meeting notes" — **follow-through**. The unit of value is *a commitment that landed in the right person's world*.

| Layer | Content |
|---|---|
| **Core benefit** | Commitments made in meetings actually get done |
| **Actual product** | Transcript → summary, decisions, and owned/dated action items → one-click Calendar invite or Gmail draft per person |
| **Augmented product** | Inline editing (human checkpoint) · MoM email + clipboard copy · three input modes · samples · keyboard-complete a11y · zero data retention |

**Differentiators, in order of strategic weight:**
1. **Distribution, not summarisation** — the open quadrant ([MRD §5.2](02-mrd.md#52-the-strategic-map)).
2. **Zero setup / zero OAuth** — value in ~10s with no account, no permission, no admin gate.
3. **Precision-biased AI** — never invents a commitment (MR-3); the human always sends.
4. **Speed** — ~2.5s, deliberately chosen over a smarter-but-slower model.

**Product-level risks:** the wedge is copyable in a week ([MRD R3](02-mrd.md#9-risks--assumptions)); the product is a *feature* unless the H2/H3 flywheel starts.

---

## 2. Price

**Model:** freemium, product-led, bottom-up. **Not** priced per meeting — usage-metering a core loop punishes the exact behaviour we're trying to prove.

| Tier | Price | Includes | Purpose |
|---|---|---|---|
| **Free** | $0 | Unlimited paste/Doc/file extraction · full distribution · no account | Own the top of the funnel; harvest correction data; make the wedge frictionless |
| **Pro** | ~$12 /user/mo | Auto-capture (extension) · persistence & history · Outlook + Google · priority latency | The friction-removal upgrade |
| **Team** | ~$20 /user/mo | Shared workspaces · AI notetaker auto-join · completion tracking + nudges · analytics | H3 value: own the outcome |
| **Enterprise** | Custom | SSO/SAML · DPA · data residency · admin controls | Unlocks "Dana" ([MRD §4.3](02-mrd.md#43-anti-persona--dana-the-enterprise-it-admin)) at H2/H3 |

### Pricing rationale

- **Charge to remove friction, not to unlock core value.** Extraction stays free forever. We monetise *not having to paste* — the thing heavy users want most and light users don't care about. This aligns willingness-to-pay with intensity of use.
- **Anchoring:** Otter/Fireflies sit roughly $10–20/user/mo. Pro at ~$12 is deliberately *inside* the category's expected band — pricing is not our differentiator, and being cheap would signal "feature," not "product."
- **Marginal cost ≈ 0.** An 8B extraction is fractions of a cent, so a generous free tier is economically trivial and strategically decisive.
- **Why not per-meeting?** It taxes the core loop and makes users ration the behaviour we most need. Per-seat is predictable and matches how the buyer already budgets.

**Key risk ([MRD R5](02-mrd.md#9-risks--assumptions)):** the free tier is *so* complete that conversion stalls.
**Mitigation:** gate on auto-capture and persistence — real, felt friction — not on artificial extraction limits.
**Evidence needed:** all numbers above are hypotheses. [RQ5](05-research-plan.md#2-research-questions) (Van Westendorp + tier fake-doors) exists to replace them with data. *Stating a price without research is a hypothesis; pretending it's a plan is the mistake.*

---

## 3. Place (distribution)

| Channel | Role | Status |
|---|---|---|
| **Web app** (direct URL) | Primary. Zero-install is the whole point — the channel *is* the wedge. | ✅ Live |
| **Chrome Web Store** | H2 extension. High-intent discovery; category-native. | Planned |
| **Zoom / Teams marketplaces** | H2. Meet the meeting where it happens; strong distribution surface. | Planned |
| **Microsoft/Google Workspace marketplaces** | H2/H3. Required for the enterprise motion. | Planned |
| **The recipients themselves** | **Underrated.** Every invite/email lands with a non-user (Marcus). | ✅ Live, unexploited |

**Strategic note — the free channel we're not using yet:** because assignees receive real Calendar invites and Gmail drafts, **Postmeet already reaches people who have never visited the site.** Today those artifacts carry only a subtle "(Sent via Postmeet)" line. That's a viral loop sitting idle. A tasteful attribution + one-click "extract your own meeting" path turns the *product's output* into the acquisition channel — near-zero CAC, and it compounds with usage. This is the highest-leverage Place decision available and it costs almost nothing.

**Anti-channel:** enterprise field sales. Contradicts the bottom-up motion, and the product isn't ready for Dana.

---

## 4. Promotion

**Motion: PLG.** The demo *is* the pitch — no signup means the funnel is "click link → feel value," which almost no competitor can match.

| Lever | Play | Why it fits |
|---|---|---|
| **Product-led** | Public URL, samples preloaded, value in 10s | Removes every step between curiosity and the aha |
| **Content/SEO** | *"Zoom transcript to action items"*, *"meeting follow-through"*, *"minutes of meeting template"* | High-intent, low-competition long tail; the category's head terms are owned by incumbents |
| **Marketplaces** | Chrome/Zoom/Teams listings (H2) | Intent-rich, category-native discovery |
| **Community** | Show HN, r/productivity, PM/EM communities | The no-OAuth trick is a genuinely interesting story — it earns attention on merit |
| **Founder narrative** | The 8B-over-70B tradeoff, the URL wedge | Technical credibility; attracts practitioners, not just users |
| **Viral loop** | Attribution on generated artifacts (see §3) | Compounds; near-zero CAC |

**Positioning line:** *"Meeting tools capture what was said. Postmeet makes sure it gets done."*

**Anti-promotion:** don't compete on "best AI notetaker." That's the crowded lane, it invites a comparison we lose (Otter has years of ASR investment), and it re-frames us as capture — contradicting the strategy.

---

## 5. People

### 5.1 The people who deliver it

| Role | Why needed | When |
|---|---|---|
| **PM** (me) | Discovery, prioritisation, evals, the H2/H3 call | Now |
| **Full-stack eng** ×2 | Extension + notetaker are real engineering | H2 |
| **Product designer** | Board UX is the trust surface; distribution must be unmissable | H2 |
| **ML/AI eng** | Eval harness, fine-tuning on the correction corpus | H2/H3 |
| **DevRel / content** | PLG demands content, not sales headcount | H2 |
| **Support** | In-app + docs; the [User Guide](04-user-guide.md) is tier-0 deflection | H2 |

Deliberately **no sales team** pre-H3. Hiring sellers into a PLG motion before PMF is how bottom-up products die.

### 5.2 The people who receive it

**Marcus (the assignee) is a service touchpoint, not a bystander.** He experiences Postmeet purely through an artifact he didn't ask for. If that invite is wrong — wrong date, wrong owner, a task he never agreed to — the damage lands on *Priya's* credibility, not ours, and she stops using it.

**That is precisely why precision is weighted over recall** ([Research §5.2](05-research-plan.md#52-metrics)): the person most exposed to an AI error is the one with the least context to catch it.

---

## 6. Process

**Delivery process (how value reaches the user):**

```
Land (no signup) → Sample or paste → Extract (~2.5s) → Review & edit ← human checkpoint
                                                            ↓
                                              One-click distribute → user clicks Save/Send
```
Exactly **one required decision** (what to paste) before value. Everything else is optional.

| Process | Design choice | Rationale |
|---|---|---|
| **Onboarding** | None. Samples replace a tutorial. | A tutorial is an admission the product isn't obvious |
| **Failure** | Human-readable errors, never a stack trace; auto-fallback on model failure | Errors are a service moment; a crash is a churn event |
| **Human checkpoint** | Everything editable; **nothing auto-sends** | Trust + the source of flywheel data |
| **Support** | Self-serve docs → in-app → email | Matches a $0–12/mo price point |
| **Feedback → product** | Corrections are logged as signal, not just UI state | The process *is* the flywheel |
| **Privacy** | Stateless by default | Removes the objection instead of answering it |

**The process insight:** the human checkpoint looks like a *limitation* ("why doesn't it just send?") but is simultaneously the trust mechanism **and** the data-collection mechanism. One design decision serving three purposes is a sign the strategy is coherent.

---

## 7. Physical Evidence

For a service, "physical evidence" = the tangible proof the value is real. Postmeet's evidence is unusually strong because **its output lives in other people's tools.**

| Evidence | Signal |
|---|---|
| **The board** | Structured, owned, dated — visibly not just a summary |
| **"Extracted in 2.8s · 5 action items · 1 decision"** | Speed and value, stated as fact |
| **The Google Calendar invite** | *The* proof point — a real invite in a real calendar. Indistinguishable from a native integration. |
| **The Gmail draft** | Formatted, per-person, human-readable |
| **The MoM** | A shareable artifact with a life beyond the app |
| **Honest stats** (~2.5s · 0 OAuth scopes · 100% coverage) | Credibility through verifiable facts — *replaced fabricated usage counts, deliberately* |
| **Open-source repo, green CI** | Engineering rigor is public and checkable |
| **The 40s cold start** | ⚠️ **Negative evidence** — the free tier's first impression. Mitigated by a keep-warm ping; a paid host is the real fix. |

**The strategic point:** the calendar invite is the strongest evidence we have *and* our distribution channel *and* our viral loop. Same artifact, three jobs. That's what a coherent mix looks like — and it's why "Physical Evidence" isn't a box-ticking exercise here.

---

## 8. Coherence check

The mix is only as good as its consistency with the strategy. Auditing:

| P | Serves "last mile + zero setup"? |
|---|---|
| Product | ✅ Distribution is the core; setup removed by construction |
| Price | ✅ Free extraction; charge to remove *remaining* friction |
| Place | ✅ Zero-install web; recipients as a latent channel |
| Promotion | ✅ PLG — the demo is the pitch; explicitly refuses the capture fight |
| People | ✅ No sales pre-PMF; assignee treated as a touchpoint |
| Process | ✅ One decision to value; human checkpoint = trust + data |
| Physical Evidence | ✅ A real calendar invite proves it better than any landing page |

**No P contradicts the strategy** — and where one nearly did (per-meeting pricing would tax the core loop; native OAuth integration would delete the wedge), it was rejected on those grounds. Consistency across all seven is the actual output of this analysis; the individual boxes are just how you get there.

**Weakest link:** Place. We're not yet using the recipient loop — the cheapest growth lever we own.

---

*Next: [Development & Execution →](08-development-execution.md)*
