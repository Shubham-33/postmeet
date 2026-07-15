# Launch Plan — Postmeet

**Owner:** Shubham Mittal · **Status:** v1 launched (public demo) · **Phase:** Development & Execution
**Related:** [7P Analysis](07-7p-analysis.md) · [Post-Launch](10-post-launch.md) · [Research Plan](05-research-plan.md) · [Case study home](./)

---

## 1. Launch philosophy

**This is not a "big bang" launch, and it shouldn't be.** Postmeet v1 is an experiment with a kill criterion ([MRD §10](02-mrd.md#10-recommendation)). Driving traffic to an unvalidated product wastes the scarcest resource a new product has: **the first impression of people who would have been your best users.**

So the launch is staged, and **each stage has an entry gate, a learning goal, and an exit criterion.** A stage that fails its gate does not proceed — it loops back.

> **Governing rule:** don't scale distribution until the loop is proven. Amplifying a broken funnel just burns the audience faster.

---

## 2. Launch stages

```
  ALPHA          PRIVATE BETA        PUBLIC LAUNCH        SCALE
  n≈5            n≈30–50             open                 marketplaces
  ─────────      ────────────        ─────────────        ─────────────
  Does it        Does the loop       Can it survive       Can it grow
  work at all?   close? (RQ2)        strangers?           without us?
       │              │                    │                   │
       ▼              ▼                    ▼                   ▼
  gate: P0s     gate: Activation     gate: reliability    gate: retention
  pass          ≥25% + precision     + no trust incident  + conversion
                ≥0.95
```

### Stage 0 — Alpha *(complete)*

| | |
|---|---|
| **Audience** | Me + ~5 friendly testers |
| **Goal** | Does the core loop function on real transcripts? |
| **Exit criteria** | ✅ All P0 stories pass · ✅ p95 <5s · ✅ zero stack traces on failure paths · ✅ publicly reachable with no login |
| **Learned** | Reliability, not quality, was the binding constraint ([ADR-2](08-development-execution.md#adr-2-fast-primary-model-with-automatic-fallback)). Hosting must be verified from an *unauthenticated* client ([the Streamlit detour](08-development-execution.md#the-deployment-detour--a-real-execution-lesson)). |
| **Status** | ✅ Done — [live](https://postmeet.onrender.com/) |

### Stage 1 — Private beta *(next — currently blocked)*

| | |
|---|---|
| **Audience** | 30–50 meeting-heavy leads: JTBD interviewees, PM/EM communities, personal network |
| **Entry gate** | 🔴 **BLOCKED on analytics instrumentation.** Running a beta whose primary metric is unmeasurable is theatre. |
| **Goal** | **RQ2** — does the loop actually close? Plus RQ4, RQ6. |
| **Duration** | 4 weeks |
| **Instrumentation required** | Activation · time-to-value · edit rate by field · failure rate ([Research §4.1](05-research-plan.md#41-product-analytics--the-cheapest-and-most-important)) |
| **Qual alongside** | 5–8 think-aloud sessions; exit survey; **churn interviews with people who tried once and never returned** — the most informative cohort and the one everyone forgets to talk to |
| **Exit criteria** | **Activation ≥25%** · precision ≥0.95 on the golden eval set · zero fabricated items reaching a recipient · qualitative signal that the pain is real |
| **If it fails** | **Do not launch publicly.** Return to discovery. Activation <25% means the last-mile thesis is wrong, and no amount of polish or model upgrading fixes a wrong thesis. |

### Stage 2 — Public launch

| | |
|---|---|
| **Entry gate** | Stage 1 exit criteria met |
| **Goal** | Reach beyond the network; test whether the value is self-evident to strangers |
| **Channels** | Show HN · r/productivity, r/ExperiencedDevs · PM/EM communities · LinkedIn (founder narrative) · SEO content live |
| **Angle** | Lead with the **engineering story**, not the product pitch: *"I shipped the smaller model on purpose"* and *"integration-grade distribution with zero OAuth."* Both are genuinely interesting and earn attention on merit — a launch post that just says "AI meeting tool" dies on arrival in this category. |
| **Prep** | Cold start eliminated (paid host — a 40s first load on launch day is unrecoverable) · rate limiting · model spend cap + alert · error monitoring · [User Guide](04-user-guide.md) live · fake-doors instrumented to capture H2 demand |
| **Success** | 1,000 sessions in week 1 · Activation holds ≥25% **with strangers** (the real test — friendly testers are biased) · no trust incident · fake-door signal ranks H2 |

### Stage 3 — Scale *(H2)*

| | |
|---|---|
| **Entry gate** | Public Activation holds; week-4 retention >20%; H2 demand evidenced by fake doors |
| **Channels** | Chrome Web Store · Zoom/Teams marketplaces · the **recipient loop** ([7P §3](07-7p-analysis.md#3-place-distribution)) |
| **Motion** | Turn the product's own output into the acquisition channel — every invite reaches a non-user at ~zero CAC |
| **Monetisation** | Pro tier live; gate on auto-capture, never on extraction |

---

## 3. Go-to-market

**Motion: PLG, bottom-up.** ([7P §4](07-7p-analysis.md#4-promotion))

| | |
|---|---|
| **Positioning** | *"Meeting tools capture what was said. Postmeet makes sure it gets done."* |
| **Target** | Meeting-heavy leads in tech-forward SMBs/scale-ups ("Priya") |
| **Wedge** | Zero setup — value in ~10s, no account, no permission, no admin gate |
| **Funnel** | Click link → sample → extract → **distribute** (the aha) → return next meeting → hit paste friction → convert to auto-capture |
| **Anti-strategy** | ❌ Don't compete on "best AI notetaker" (crowded, we lose) · ❌ no sales team pre-PMF · ❌ no enterprise motion until Dana's requirements exist |

**The aha moment is precisely defined:** *seeing a real Google Calendar invite open, fully prefilled, from a transcript pasted 10 seconds ago.* Every GTM decision optimises for reaching that moment faster. It's also why `distribute_click` is the Activation event — it's not a proxy for the aha, **it is the aha.**

---

## 4. Launch checklist

### Product
- [x] All P0 stories pass acceptance
- [x] Graceful, human-readable errors on every failure path
- [x] Accessibility: keyboard-complete, AA contrast, `aria-live` status
- [x] Samples load in one click (no transcript needed to evaluate)
- [x] Mobile-responsive
- [ ] **Analytics instrumented** 🔴 *blocking Stage 1*
- [ ] Fake doors live (Zoom / Outlook / auto-join) to rank H2

### Reliability
- [x] Model fallback chain verified
- [x] Upstream timeout bounded (30s)
- [x] CI green; 100% coverage gate enforced
- [x] Keep-warm ping (free-tier cold start)
- [ ] Paid host — **required before Stage 2** (40s first load is fatal on launch day)
- [ ] Rate limiting
- [ ] Model spend cap + alert
- [ ] Error monitoring / alerting

### Trust & compliance
- [x] Zero OAuth scopes
- [x] No server-side retention; local-only, 7-day TTL
- [x] Secrets in a secret store; none in repo
- [x] Privacy answers documented in the [User Guide](04-user-guide.md)
- [ ] **Golden eval set: precision ≥0.95** 🔴 *blocking Stage 1*
- [ ] Public privacy policy + ToS (before Stage 2)

### Content & comms
- [x] Public demo URL
- [x] User Guide + FAQ + troubleshooting
- [x] Open-source repo, README with live links
- [x] Case study / pitch deck
- [ ] Launch post (engineering-story angle)
- [ ] SEO content for the long tail
- [ ] Demo GIF/video

### Honest status
**Two hard blockers before a real Stage 1: analytics and the eval set.** Both are named in [PRD §4.2](03-prd.md#42-targets--instrumentation) and [§7.4](03-prd.md#74-evaluation). Everything shipped is necessary and not sufficient — v1 is a *working product* but not yet a *readable experiment*.

---

## 5. Rollout & safety

| Control | Approach |
|---|---|
| **Staged exposure** | Alpha → beta (invite) → public. No stage skips its gate. |
| **Kill switch** | `NIM_MODEL` env pins a model instantly; Render env change + redeploy in ~90s. A bad model swap is reversible in under two minutes without a code change. |
| **Rollback** | `main` is always deployable; revert + push = ~90s to previous state. |
| **Spend guard** | Cap + alert on model spend before public traffic (free credits are a real exhaustion risk — [E1](08-development-execution.md#6-risk-register-execution)). |
| **Trust incident plan** | If a fabricated commitment reaches a recipient: pause bulk distribute → reproduce → add to eval set → fix prompt → re-run eval → restore. **Precision regressions are treated as P0 incidents, not bugs.** |

---

## 6. What could go wrong at launch

| Scenario | Response |
|---|---|
| **Activation is 8%, not 25%** | The thesis is wrong. **Do not tune the model.** Return to discovery: is the pain real (RQ1)? Is friction the blocker (RQ3)? This is the outcome the whole staging exists to catch cheaply. |
| Everyone extracts, nobody distributes | Investigate the checkpoint: is distribution undiscoverable, or is trust too low to send? Distinguish via usability + edit rate. Two very different fixes. |
| A hallucinated item is emailed to a real person | Trust incident protocol (§5). This is the failure mode that ends products, not the one that annoys users. |
| Model credits exhaust mid-launch | Graceful error (already built) + spend alert. Degrades, doesn't crash. |
| Traffic spikes on Show HN and the free host melts | Paid host before Stage 2; rate limit. |
| A competitor ships the same wedge that week | Expected — it's copyable ([MRD R3](02-mrd.md#9-risks--assumptions)). The response is speed to H2/H3, never a feature war on the wedge. |

---

## 7. Definition of a successful launch

Not signups. Not traffic. Not upvotes.

> **A successful launch is one where we learn — with confidence — whether the last-mile thesis is true.**

| Outcome | Verdict |
|---|---|
| Activation ≥25% with strangers, precision ≥0.95, retention signal | ✅ **Thesis validated** → fund H2 |
| Activation <25%, cleanly measured | ✅ **A successful launch.** We learned the thesis is wrong for ~$0 instead of finding out after building the extension. |
| High traffic, no instrumentation, "felt good" | ❌ **A failed launch**, regardless of the numbers on the vanity dashboard. |

That third row is the one worth internalising: **an unmeasured launch that looks successful is worse than a measured one that fails**, because it licenses the next, far more expensive, wrong decision.

---

*Next: [Post-Launch →](10-post-launch.md)*
