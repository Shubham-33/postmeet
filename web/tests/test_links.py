"""Regression suite for links.py — the Calendar / Gmail / MOM URL builders.

Pure functions, no network. Targets 100% line + branch coverage of links.py and
locks the exact prefill-URL behavior so a refactor can't silently change the
links a reviewer clicks.
"""
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

import links

# ---------- default_date ----------

def test_default_date_is_today_plus_offset():
    expected = (date.today() + timedelta(days=links.DEFAULT_DUE_OFFSET_DAYS)).isoformat()
    assert links.default_date() == expected


# ---------- format_date ----------

def test_format_date_valid():
    assert links.format_date("2026-07-05") == "Sun, Jul 5, 2026"


def test_format_date_empty_returns_empty():
    assert links.format_date("") == ""


def test_format_date_unparseable_returns_input():
    assert links.format_date("next Tuesday") == "next Tuesday"


# ---------- calendar_url ----------

def test_calendar_url_full_item():
    item = {
        "task": "Ship billing fix",
        "owner": "Sarah",
        "owner_email": "sarah@acme.com",
        "due_date": "2026-07-05",
        "context": "Unblocks the July release.",
    }
    url = links.calendar_url(item)
    q = parse_qs(urlparse(url).query)
    assert url.startswith(links.CAL_BASE)
    assert q["action"] == ["TEMPLATE"]
    assert q["text"] == ["[Postmeet] Ship billing fix"]
    assert q["dates"] == ["20260705T090000Z/20260705T100000Z"]
    assert q["add"] == ["sarah@acme.com"]
    assert "Context: Unblocks the July release." in q["details"][0]


def test_calendar_url_no_due_falls_back_to_default_and_no_email_no_context():
    item = {"task": "Do thing", "owner": "", "owner_email": "", "due_date": "", "context": ""}
    url = links.calendar_url(item)
    q = parse_qs(urlparse(url).query)
    stamp = links.default_date().replace("-", "")
    assert q["dates"] == [f"{stamp}T090000Z/{stamp}T100000Z"]
    assert "add" not in q                      # no attendee when no email
    assert q["details"] == ["Action item assigned to Unassigned via Postmeet."]  # no context appended


# ---------- owner_mail_url ----------

def test_owner_mail_url_empty_items_returns_empty():
    assert links.owner_mail_url("Sarah", []) == ""


def test_owner_mail_url_single_item_with_due_and_context():
    items = [{"task": "Ship fix", "owner_email": "sarah@acme.com",
              "due_date": "2026-07-05", "context": "release blocker"}]
    url = links.owner_mail_url("Sarah", items)
    q = parse_qs(urlparse(url).query)
    assert url.startswith(links.GMAIL_BASE)
    assert q["to"] == ["sarah@acme.com"]
    assert q["su"] == ["Action item from our meeting — Ship fix"]
    body = q["body"][0]
    assert "Hi Sarah," in body
    assert "• Task: Ship fix" in body
    assert "• Due: Sun, Jul 5, 2026" in body
    assert "Context: release blocker" in body
    assert "due date " in body and "due dates" not in body   # singular


def test_owner_mail_url_single_item_no_due_no_context_unknown_owner():
    """Owner 'Unassigned' → greeting 'there'; no email → empty To; no due/context branches."""
    items = [{"task": "Follow up", "owner_email": "", "due_date": "", "context": ""}]
    url = links.owner_mail_url("Unassigned", items)
    q = parse_qs(urlparse(url).query)
    assert q.get("to", [""]) == [""] or "to" not in q
    body = q["body"][0]
    assert "Hi there," in body
    assert "Due:" not in body
    assert "Context:" not in body


def test_owner_mail_url_multiple_items():
    items = [
        {"task": "Task A", "owner_email": "bob@acme.com", "due_date": "2026-07-05", "context": "why A"},
        {"task": "Task B", "owner_email": "", "due_date": "", "context": ""},
    ]
    url = links.owner_mail_url("Bob", items)
    q = parse_qs(urlparse(url).query)
    assert q["su"] == ["2 action items from our meeting"]
    body = q["body"][0]
    assert "the following 2 items:" in body
    assert "1. Task A" in body
    assert "2. Task B" in body
    assert "   Due: Sun, Jul 5, 2026" in body
    assert "   Context: why A" in body
    assert "due dates" in body                # plural for multiple items
    assert q["to"] == ["bob@acme.com"]        # first email found is used


def test_owner_mail_url_empty_owner_name_greets_there():
    items = [{"task": "X", "owner_email": "", "due_date": "", "context": ""}]
    body = parse_qs(urlparse(links.owner_mail_url("", items)).query)["body"][0]
    assert "Hi there," in body


# ---------- build_mom_body ----------

def test_build_mom_body_full():
    data = {
        "summary": "We synced on billing.",
        "decisions": ["Postpone redesign to Q4."],
        "action_items": [
            {"task": "Ship fix", "owner": "Sarah", "owner_email": "sarah@acme.com",
             "due_date": "2026-07-05", "context": "release blocker"},
            {"task": "Triage bugs", "owner": "Unassigned", "owner_email": "", "due_date": "", "context": ""},
        ],
    }
    body = links.build_mom_body(data)
    assert "We synced on billing." in body
    assert "📋 DECISIONS (1)" in body
    assert "1. Postpone redesign to Q4." in body
    assert "✅ ACTION ITEMS (2)" in body
    assert "▸ Sarah (sarah@acme.com)" in body
    assert "▸ Unassigned" in body
    assert "   • Ship fix  [due Sun, Jul 5, 2026]" in body
    assert "     ↳ release blocker" in body
    # Unassigned must sort AFTER named owners
    assert body.index("▸ Sarah") < body.index("▸ Unassigned")


def test_build_mom_body_empty_uses_placeholders():
    body = links.build_mom_body({})
    assert "(no summary)" in body
    assert "DECISIONS" not in body        # no decisions section when none
    assert "ACTION ITEMS" not in body     # no action-items section when none


# ---------- mom_email_url ----------

def test_mom_email_url_dedupes_and_sorts_recipients():
    data = {
        "summary": "s", "decisions": [],
        "action_items": [
            {"task": "a", "owner": "B", "owner_email": "b@x.com", "due_date": "", "context": ""},
            {"task": "b", "owner": "A", "owner_email": "a@x.com", "due_date": "", "context": ""},
            {"task": "c", "owner": "B", "owner_email": "b@x.com", "due_date": "", "context": ""},
        ],
    }
    q = parse_qs(urlparse(links.mom_email_url(data)).query)
    assert q["to"] == ["a@x.com,b@x.com"]                 # deduped + sorted
    assert q["su"][0].startswith("Minutes of Meeting — ")


def test_mom_email_url_no_emails_empty_to():
    data = {"summary": "s", "decisions": [], "action_items": []}
    q = parse_qs(urlparse(links.mom_email_url(data)).query, keep_blank_values=True)
    assert q["to"] == [""]


# ---------- group_by_owner / owner_email ----------

def test_group_by_owner_unassigned_last():
    items = [
        {"task": "1", "owner": "Zoe"},
        {"task": "2", "owner": ""},          # → Unassigned
        {"task": "3", "owner": "Amy"},
        {"task": "4", "owner": "Amy"},
    ]
    grouped = links.group_by_owner(items)
    assert list(grouped.keys()) == ["Amy", "Zoe", "Unassigned"]
    assert len(grouped["Amy"]) == 2


def test_owner_email_finds_first_non_empty():
    items = [{"owner_email": ""}, {"owner_email": "found@x.com"}, {"owner_email": "second@x.com"}]
    assert links.owner_email(items) == "found@x.com"


def test_owner_email_none_returns_empty():
    assert links.owner_email([{"owner_email": ""}, {}]) == ""
