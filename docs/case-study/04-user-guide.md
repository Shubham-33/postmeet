# User Guide & Instruction Manual — Postmeet

**Audience:** end users · **Version:** v1 · **Phase:** Ideation (deliverable)
**Live app:** [postmeet.onrender.com](https://postmeet.onrender.com/) · [Case study home](./)

---

## 1. What Postmeet does

Postmeet reads a meeting transcript and gives you back:

- a **summary** of the meeting,
- the **decisions** that were made, and
- the **action items** — each with an owner, an email, a due date, and why it matters.

Then it lets you send each action item to the person who owns it — as a **prefilled Google Calendar invite** or a **prefilled Gmail draft** — in one click.

**You do not need an account. You do not grant any permissions. Nothing you paste is stored.**

---

## 2. Quick start (30 seconds)

1. Open **[postmeet.onrender.com](https://postmeet.onrender.com/)**.
   *(First load after a quiet period can take ~40 seconds — the free host is waking up. After that it's instant.)*
2. Click **Load sample ▾** and pick **Standup**, **Planning**, or **Retro**.
3. Click **Extract** (or press **⌘/Ctrl + Enter**).
4. In ~3 seconds you'll see the board: a **Decisions** column and one column per person.
5. On any card, click **📅 Calendar** — Google Calendar opens in a new tab, fully prefilled. Click **Save**.

That's the whole product.

---

## 3. Getting your meeting in

There are three ways. Postmeet auto-detects which you're using.

### 3.1 Paste a transcript
Paste the text straight into the box. Anything works — Zoom/Teams/Meet transcript exports, your own notes, a Slack recap. Minimum 30 characters.

**Tip:** speaker labels help a lot. `Priya: I'll ship the fix by Friday` extracts far better than an unattributed wall of text.

### 3.2 Use a Google Doc
Paste the Doc's URL instead of text. Postmeet fetches the text automatically.

> ⚠️ **The Doc must be shared as "Anyone with the link can view."** Postmeet uses Google's public export endpoint and never asks for access to your Drive. A private Doc will return a clear error telling you to change sharing.

### 3.3 Upload a file
Click **Attach file**, or drag a file onto the page. Accepts `.txt` and `.md`, up to 200 KB (longer files are truncated with a warning).

---

## 4. Reading the board

| Element | Meaning |
|---|---|
| **Decisions column** | Explicit decisions ("we decided X"). Not tasks — no owner, no date. |
| **One column per person** | Every action item that person committed to. |
| **Card title** | The task itself. |
| **Date (orange)** | The due date. Relative dates like "Friday" are resolved to a real date. |
| **Email** | An address found in the transcript and matched to that person. |
| **Context (italic)** | One line on *why* the task matters or what it unblocks. |
| **Unassigned column** | Commitments with no clear owner — always sorted last. |

Postmeet only extracts **explicit commitments**. If someone muses "maybe we should look at that," it will not become a task. This is deliberate — a made-up action item is worse than a missing one.

---

## 5. Fixing things before you send

**Click any field to edit it.** Task, owner, email, date, context — all editable inline.

Fields showing **+ add email** or **+ add date** are where Postmeet found nothing. Click to fill them in.

**Edits flow straight into the links.** If you fix Marcus's email and then click Email, the corrected address is used. Nothing is sent until you click a distribute button — you are always the last checkpoint.

---

## 6. Distributing

### 6.1 One item → a calendar invite
Click **📅 Calendar** on any card. Google Calendar opens with the title, date, attendee and context prefilled. Review, click **Save**.

### 6.2 One person → one email with all their items
Click **✉️ Email** on a card, or **✉️ Email {name}**. A Gmail draft opens addressed to that person, containing **every** item they own — one email per person, not one per task. Review, click **Send**.

### 6.3 Everyone at once
From the summary panel:

| Button | What it does |
|---|---|
| **Email MOM to team** | One Gmail draft with the full formatted minutes, addressed to everyone whose email was found. |
| **Copy MOM as text** | The same minutes on your clipboard — paste into Slack, Notion, anywhere. |
| **All Calendars** | Opens a prefilled Calendar tab for every action item. |
| **All Emails** | Opens a prefilled Gmail draft for every person. |

> **Heads-up:** bulk actions open several tabs. Your browser may ask you to allow pop-ups for this site the first time.

---

## 7. How it works without any login ("the no-OAuth trick")

Google Calendar and Gmail both accept **prefilled actions via a URL**:

```
https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...&add=...
https://mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...
```

Postmeet builds those URLs and opens them in a new tab. The tab uses **your own, already-signed-in Google session** — so it looks and behaves exactly like a real integration, while Postmeet itself never sees your Google account, never asks for a permission, and holds **zero** OAuth scopes.

**What this means for you:**
- ✅ Nothing to install, approve, or get IT to sign off on.
- ✅ Postmeet has no access to your calendar or mail — it just opens a prefilled window.
- ⚠️ The invite/email is sent **from your account**, so bulk-sending means you click Save/Send once per item.

---

## 8. Your data & privacy

| Question | Answer |
|---|---|
| Is my transcript stored on a server? | **No.** Extraction is stateless. Nothing is written to a database — there isn't one. |
| Is anything saved at all? | Only in **your own browser** (local storage), so a refresh doesn't lose your board. It expires after 7 days and never leaves your device. |
| Does Postmeet read my email or calendar? | **No.** It holds no permissions on your Google account. |
| Where does the text go? | To the model provider (NVIDIA NIM) for the single extraction call, and back. That's it. |
| Do you need my Google account? | Never asked for. |
| How do I delete everything? | Refresh, or clear site data. There's nothing on our side to delete. |

Don't paste content you're not comfortable sending to a third-party model API — the same caution you'd apply to any AI tool.

---

## 9. Keyboard shortcuts

Press **?** anywhere to see them.

| Shortcut | Action |
|---|---|
| **⌘/Ctrl + Enter** | Extract |
| **?** | Show shortcuts |
| **Esc** | Close dialog |
| **Tab / Shift+Tab** | Move between controls (everything is keyboard-reachable) |

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| First load takes ~40s | Free host was asleep | Wait — it only happens after idle. Then it's fast. |
| *"Transcript is too short"* | Under 30 characters | Paste more text. |
| *"This Google Doc isn't public"* | Doc isn't link-shared | Share → **Anyone with the link can view**. |
| *"Could not find a Doc ID in that URL"* | Not a Docs URL (e.g. a Sheet) | Use a `docs.google.com/document/d/...` URL. |
| *"The model took too long"* | Model cold-starting | Press **Extract** again. |
| Only one tab opened on bulk send | Pop-up blocker | Allow pop-ups for this site, or use per-card buttons. |
| Wrong day for "Friday" | Relative-date edge case | Click the date and fix it — that's why it's editable. |
| No email on a card | No matching address in the transcript | Click **+ add email**. |
| Board vanished | Local storage cleared / >7 days | Re-extract. Nothing is stored server-side by design. |

---

## 11. Known limitations (deliberate, v1)

1. **No server-side persistence** — a refresh keeps your board only via local storage. Intentional: no database means no privacy question.
2. **You click Save/Send yourself** — Postmeet drafts, it never sends. True auto-send needs OAuth, which is exactly the friction we removed. This is an honest trade.
3. **Public Docs only** — private Docs need a real OAuth flow (out of scope for v1).
4. **Relative dates can slip** — the model occasionally misjudges the weekday. Always editable.
5. **Quality tracks transcript quality** — speaker labels and explicit commitments extract well; rambling, unattributed text less so.
6. **Google-first** — Calendar/Gmail today. Outlook is on the roadmap ([Vision H2](01-product-vision.md#8-three-horizon-vision)).

---

## 12. FAQ

**Do I need to install anything?** No. It's a web page.

**Does it join my meetings?** Not in v1 — you bring the transcript. An auto-joining notetaker is the H2 plan.

**Does it work with Zoom / Teams / Meet?** Any transcript those tools export works. Automatic capture is H2.

**Is it free?** Yes, the demo is free to use.

**Can my teammates see the board?** No — it's local to your browser. What they receive is a normal calendar invite or email.

**What model is it?** NVIDIA NIM running Llama 3.1 (8B primary, 70B fallback). Chosen for consistent ~2.5s responses over a marginally smarter but much slower option — see [the reasoning](03-prd.md#71-model--inference).

**Can I use it for something other than meetings?** Any text containing commitments works — a project thread, an email chain. Meetings are just the sharpest case.

---

*Next: [Research Plan →](05-research-plan.md)*
