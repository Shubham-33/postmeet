"""Postmeet — client-side distribution link builders.

Pure functions that turn extracted action items into prefilled Google Calendar /
Gmail / Minutes-of-Meeting URLs (the "no-OAuth trick"). No network, no framework
imports — so they're trivially unit-testable and reused by the Streamlit UI.

Ported from ``static/postmeet.js`` so the links are byte-for-byte identical to
the Flask front end's behavior.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlencode

DEFAULT_DUE_OFFSET_DAYS = 7
CAL_BASE = "https://calendar.google.com/calendar/render"
GMAIL_BASE = "https://mail.google.com/mail/"


def default_date() -> str:
    """Fallback due date (today + :data:`DEFAULT_DUE_OFFSET_DAYS`) as ISO ``YYYY-MM-DD``."""
    return (date.today() + timedelta(days=DEFAULT_DUE_OFFSET_DAYS)).isoformat()


def format_date(iso: str) -> str:
    """``"2026-07-05"`` → ``"Sun, Jul 5, 2026"``. Returns the input unchanged if unparseable."""
    if not iso:
        return ""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
    except ValueError:
        return iso
    return f"{d:%a}, {d:%b} {d.day}, {d.year}"


def calendar_url(item: dict) -> str:
    """Build a Google Calendar ``render?action=TEMPLATE`` URL prefilled for one action item."""
    d = (item.get("due_date") or "").strip() or default_date()
    stamp = d.replace("-", "")
    context = (item.get("context") or "").strip()
    details = f"Action item assigned to {item.get('owner') or 'Unassigned'} via Postmeet."
    if context:
        details += f"\n\nContext: {context}"
    params = {
        "action": "TEMPLATE",
        "text": f"[Postmeet] {item.get('task', '')}",
        "dates": f"{stamp}T090000Z/{stamp}T100000Z",
        "details": details,
    }
    if item.get("owner_email"):
        params["add"] = item["owner_email"]
    return f"{CAL_BASE}?{urlencode(params)}"


def owner_mail_url(owner: str, items: list[dict]) -> str:
    """One consolidated Gmail compose URL per owner, containing ALL their tasks.

    Returns ``""`` when ``items`` is empty. Recipient is the first owner_email found.
    """
    if not items:
        return ""
    to = next((i["owner_email"] for i in items if i.get("owner_email")), "")
    greeting = owner if owner and owner != "Unassigned" else "there"
    n = len(items)
    subject = (
        f"Action item from our meeting — {items[0].get('task', '')}"
        if n == 1
        else f"{n} action items from our meeting"
    )
    lines = [
        f"Hi {greeting},",
        "",
        "Quick follow-up from our meeting. You agreed to take on the following:"
        if n == 1
        else f"Quick follow-up from our meeting. You agreed to take on the following {n} items:",
        "",
    ]
    for i, item in enumerate(items):
        task = item.get("task", "")
        if n > 1:
            lines.append(f"{i + 1}. {task}")
        else:
            lines.append(f"  • Task: {task}")
        if item.get("due_date"):
            due = format_date(item["due_date"])
            lines.append(f"   Due: {due}" if n > 1 else f"  • Due: {due}")
        if item.get("context"):
            if n > 1:
                lines.append(f"   Context: {item['context']}")
            else:
                lines.append(f"Context: {item['context']}")
        if n > 1:
            lines.append("")
    plural = "s" if n > 1 else ""
    lines.append(
        f"If anything's unclear or needs to be re-scoped, reply here before the due date{plural} "
        "and we'll sort it out."
    )
    lines += ["", "Thanks,", "(Sent via Postmeet)"]
    params = {"view": "cm", "fs": "1", "tf": "1", "to": to, "su": subject, "body": "\n".join(lines)}
    return f"{GMAIL_BASE}?{urlencode(params)}"


def build_mom_body(data: dict) -> str:
    """Render the plain-text Minutes-of-Meeting body from an extraction result."""
    items = data.get("action_items", []) or []
    decisions = data.get("decisions", []) or []
    summary = data.get("summary", "") or ""
    rule = "━" * 28
    lines = [
        "Hi team,",
        "",
        "Sharing the MOM from today's meeting for everyone's reference.",
        "",
        rule,
        "📝 SUMMARY",
        rule,
        summary or "(no summary)",
    ]
    if decisions:
        lines += ["", rule, f"📋 DECISIONS ({len(decisions)})", rule]
        lines += [f"{i + 1}. {d}" for i, d in enumerate(decisions)]
    if items:
        lines += ["", rule, f"✅ ACTION ITEMS ({len(items)})", rule]
        by_owner: dict[str, list[dict]] = {}
        for it in items:
            by_owner.setdefault(it.get("owner") or "Unassigned", []).append(it)
        for owner in sorted(by_owner, key=lambda o: (o == "Unassigned", o.lower())):
            email = by_owner[owner][0].get("owner_email")
            lines += ["", f"▸ {owner}" + (f" ({email})" if email else "")]
            for it in by_owner[owner]:
                due = f"  [due {format_date(it['due_date'])}]" if it.get("due_date") else ""
                lines.append(f"   • {it.get('task', '')}{due}")
                if it.get("context"):
                    lines.append(f"     ↳ {it['context']}")
    lines += ["", rule]
    lines.append(
        "If your name appears under Action Items, you'll also get an individual email "
        "with the calendar invite. Reply-all if anything below is wrong."
    )
    lines += ["", "(Sent via Postmeet)"]
    return "\n".join(lines)


def mom_email_url(data: dict) -> str:
    """Build a Gmail compose URL for the full MOM, addressed to every extracted email."""
    items = data.get("action_items", []) or []
    recipients = sorted({(i.get("owner_email") or "").strip() for i in items if i.get("owner_email")})
    subject = f"Minutes of Meeting — {format_date(date.today().isoformat())}"
    params = {
        "view": "cm",
        "fs": "1",
        "tf": "1",
        "to": ",".join(recipients),
        "su": subject,
        "body": build_mom_body(data),
    }
    return f"{GMAIL_BASE}?{urlencode(params)}"


def group_by_owner(items: list[dict]) -> dict[str, list[dict]]:
    """Group action items by owner (defaulting to ``"Unassigned"``), Unassigned last."""
    by_owner: dict[str, list[dict]] = {}
    for it in items:
        by_owner.setdefault(it.get("owner") or "Unassigned", []).append(it)
    return {k: by_owner[k] for k in sorted(by_owner, key=lambda o: (o == "Unassigned", o.lower()))}


def owner_email(items: list[dict]) -> str:
    """First non-empty ``owner_email`` among ``items``, else ``""``."""
    return next((i.get("owner_email") for i in items if i.get("owner_email")), "")
