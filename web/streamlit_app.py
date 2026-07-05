"""Postmeet — Streamlit front end.

A Python-only UI for the same pipeline that powers the Flask app: paste a
transcript / drop a public Google Doc URL / upload a file → NVIDIA Llama (with a
fast fallback) extracts a summary, decisions, and per-owner action items →
distribute via prefilled Google Calendar / Gmail / MOM links (no OAuth).

Extraction (:func:`app.call_llm`, :func:`app.fetch_google_doc_text`) and the link
builders (:mod:`links`) are imported, not reimplemented — this file is only the
presentation layer.

Deploy on Streamlit Community Cloud with main file path ``web/streamlit_app.py``
and a secret ``NVIDIA_API_KEY``.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Key bootstrap — app.py checks NVIDIA_API_KEY at import time. Locally it reads
# ../.env itself; on Streamlit Cloud there's no .env, so inject from st.secrets
# into the environment BEFORE importing app.
# ---------------------------------------------------------------------------


def _ensure_key() -> None:
    if os.environ.get("NVIDIA_API_KEY") or os.environ.get("NIM_API_KEY"):
        return
    try:
        key = st.secrets["NVIDIA_API_KEY"]
    except Exception:
        key = None
    if key:
        os.environ["NVIDIA_API_KEY"] = str(key)


_ensure_key()

try:
    from app import call_llm, fetch_google_doc_text  # noqa: E402
except RuntimeError:
    st.set_page_config(page_title="Postmeet", page_icon="📝")
    st.title("Postmeet")
    st.error(
        "**No NVIDIA API key configured.** Set `NVIDIA_API_KEY` in the app's "
        "Secrets (Streamlit Cloud → ⋮ → Settings → Secrets), or in a local `.env`. "
        "Get a free key at https://build.nvidia.com."
    )
    st.stop()

from links import (  # noqa: E402
    build_mom_body,
    calendar_url,
    format_date,
    group_by_owner,
    mom_email_url,
    owner_email,
    owner_mail_url,
)

MIN_TRANSCRIPT_CHARS = 30
MAX_FILE_BYTES = 200 * 1024

# ---------------------------------------------------------------------------
# Sample transcripts (ported from static/postmeet.js) so a reviewer can try the
# app in one click without pasting anything.
# ---------------------------------------------------------------------------

SAMPLE_TRANSCRIPTS: dict[str, str] = {
    "Standup": """Priya: Quick standup, let's go around. Marcus, what's on you?
Marcus: I'm closing out the auth refactor. I'll have the PR ready by Friday May 22 — marcus@example.com if anyone wants to review early.
Priya: Great. Tara, you?
Tara: I'm blocked on the design-system tokens. I'll ping Jamie about merging that branch today.
Jamie: Yeah I can get to that this afternoon. I'll merge by end of day and tag Tara on Slack.
Priya: Perfect. I noticed we're falling behind on QA — I'll set up a dedicated QA channel by tomorrow and pull Jamie in to triage open bugs.
Tara: We also need to decide if we're shipping the dark mode toggle in this release.
Marcus: I'd say yes — it's only two days of work.
Priya: Agreed. We'll include dark mode in the v3 release.
Jamie: Cool, I can take that. I'll have it ready by Wednesday May 27.
Priya: One more thing — we're moving the demo to Friday afternoon instead of Thursday morning. I'll send out the calendar update.""",
    "Planning": """Sarah: Let's talk Q3 priorities. Top of the list is the customer health score. Diego, where are we?
Diego: We have three drafts. I'll narrow it down to one by Wednesday June 3 and circulate to the team. diego@example.com is best for direct feedback.
Sarah: Good. Once we agree on the metric, Lin needs to wire it into the dashboard.
Lin: Yeah, I'll have the dashboard implementation done within two weeks of the metric being finalized.
Sarah: Second priority — onboarding. We're losing 40% of users in the first 7 days. We agreed last week to rebuild the empty-state experience. Karim, that's yours.
Karim: I'll have a clickable Figma prototype ready by Friday June 5, then hand off to Lin for implementation.
Sarah: Lin, can you commit to shipping the new onboarding by end of June?
Lin: Tight but doable. I'll commit to June 30. lin@example.com if anyone needs to file bugs.
Sarah: Perfect. Third priority — the SOC 2 audit. Diego will lead that.
Diego: I'll start the kickoff with the auditor next Monday June 8.
Sarah: We also decided we're delaying the API v2 launch from July to August so we can focus on these three priorities.""",
    "Retro": """Avi: Sprint retro. What went well, what didn't, what to change?
Mei: The new CI pipeline cut deploy time from 12 to 4 minutes. Big win.
Daniel: Agreed. But we had two hotfixes this sprint that should have been caught in QA.
Avi: I'll write up a postmortem on the hotfix patterns by Thursday May 28 — daniel@example.com let me know if I miss anything.
Mei: I'll add a regression test for the auth bug specifically by next Tuesday.
Daniel: We agreed last sprint to start using feature flags for risky changes — but no one used them. Avi, can we make this a hard requirement?
Avi: Yes. We're now requiring feature flags for any change touching billing or auth. I'll update the team handbook by end of week.
Mei: One more thing — I want to propose pair programming Wednesdays. Two hours, optional.
Daniel: I'm in.
Avi: Let's try it. We'll start next Wednesday.""",
}


# ---------------------------------------------------------------------------
# Extraction helper — wraps app.call_llm with reviewer-friendly error messages.
# ---------------------------------------------------------------------------


def run_extraction(text: str) -> tuple[dict | None, str | None]:
    """Return ``(data, None)`` on success or ``(None, friendly_message)`` on failure.

    Never raises — the UI shows the message instead of a traceback.
    """
    try:
        return call_llm(text), None
    except requests.Timeout:
        return None, (
            "The model took too long to respond (it may be cold-starting). "
            "Give it a moment and press **Extract** again."
        )
    except requests.RequestException:
        return None, "Couldn't reach the model service. Check your connection and retry."
    except (RuntimeError, KeyError, IndexError, ValueError) as e:
        return None, f"The model returned an unexpected response: {e}"


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Postmeet — meeting → action items", page_icon="📝", layout="wide")

st.markdown(
    "<h1 style='margin-bottom:0'>Postmeet<span style='color:#c2410c'>.</span></h1>"
    "<p style='color:#78716c;margin-top:4px'>A meeting, <em>distributed</em> in one click — "
    "paste a transcript, extract decisions &amp; action items, then push each to Google "
    "Calendar / Gmail. No sign-in, no OAuth.</p>",
    unsafe_allow_html=True,
)
st.caption(
    "Demo project · powered by NVIDIA NIM (Llama) · nothing is stored — refresh clears everything. "
    "New here? Pick a sample below and press **Extract**."
)

st.session_state.setdefault("data", None)

with st.container(border=True):
    mode = st.radio(
        "Input mode",
        ["Paste transcript", "Google Doc URL", "Upload file"],
        horizontal=True,
        label_visibility="collapsed",
    )

    transcript = ""
    doc_url = ""

    if mode == "Paste transcript":
        sample = st.selectbox(
            "Load a sample", ["— none —", *SAMPLE_TRANSCRIPTS.keys()], key="sample_pick"
        )
        prefill = SAMPLE_TRANSCRIPTS.get(sample, "")
        transcript = st.text_area(
            "Meeting transcript",
            value=prefill,
            height=240,
            placeholder="Paste your meeting transcript here…",
        )
    elif mode == "Google Doc URL":
        doc_url = st.text_input(
            "Public Google Doc URL",
            placeholder="https://docs.google.com/document/d/…  (Anyone-with-the-link)",
        )
        st.caption("The Doc must be shared as **Anyone with the link can view** (no OAuth).")
    else:
        up = st.file_uploader("Upload a transcript (.txt / .md)", type=["txt", "md"])
        if up is not None:
            raw = up.read(MAX_FILE_BYTES + 1)
            if len(raw) > MAX_FILE_BYTES:
                st.warning(f"File is larger than {MAX_FILE_BYTES // 1024} KB — truncating.")
                raw = raw[:MAX_FILE_BYTES]
            transcript = raw.decode("utf-8", errors="replace")
            st.caption(f"Loaded **{up.name}** — {len(transcript):,} characters.")

    if st.button("Extract", type="primary"):
        # Google Doc fetch (only in URL mode)
        if mode == "Google Doc URL":
            if not doc_url.strip():
                st.warning("Paste a Google Doc URL first.")
                st.stop()
            try:
                with st.spinner("Fetching Doc…"):
                    transcript = fetch_google_doc_text(doc_url.strip())
            except PermissionError as e:
                st.error(str(e))
                st.stop()
            except ValueError as e:
                st.error(str(e))
                st.stop()
            except (requests.RequestException, RuntimeError):
                st.error("Couldn't fetch that Doc. Confirm the URL and that it's shared publicly.")
                st.stop()

        if len((transcript or "").strip()) < MIN_TRANSCRIPT_CHARS:
            st.warning(f"Transcript is too short (need at least {MIN_TRANSCRIPT_CHARS} characters).")
            st.stop()

        with st.spinner("Extracting… (first call can take a few seconds while the model warms up)"):
            result, error = run_extraction(transcript.strip())
        if error:
            st.error(error)
        else:
            st.session_state["data"] = result

data = st.session_state.get("data")

if data:
    st.subheader("Summary")
    st.info(data.get("summary") or "(no summary)")

    decisions = data.get("decisions") or []
    if decisions:
        st.subheader(f"Decisions ({len(decisions)})")
        for d in decisions:
            st.markdown(f"- {d}")

    st.subheader("Action items")
    st.caption("Edit any cell before distributing — changes flow into the Calendar/Email links below.")
    edited = st.data_editor(
        data.get("action_items") or [],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "task": st.column_config.TextColumn("Task", width="large"),
            "owner": st.column_config.TextColumn("Owner"),
            "owner_email": st.column_config.TextColumn("Email"),
            "due_date": st.column_config.TextColumn("Due (YYYY-MM-DD)"),
            "context": st.column_config.TextColumn("Context", width="large"),
        },
        key="items_editor",
    )
    # data_editor returns a list of dicts; normalize + push edits back into state.
    items = [dict(r) for r in edited]
    data = {**data, "action_items": items}
    st.session_state["data"] = data

    # ---- Distribute ---------------------------------------------------------
    st.subheader("Distribute")
    st.caption("Each button opens Google Calendar / Gmail in a new tab, fully prefilled — you just click Save / Send.")
    mc1, mc2 = st.columns([1, 3])
    with mc1:
        st.link_button("✉️ Email MOM to all", mom_email_url(data), use_container_width=True)
    with mc2, st.expander("📋 Copy Minutes of Meeting (paste anywhere)"):
        st.code(build_mom_body(data), language=None)

    st.markdown("**Per person**")
    for owner, owner_items in group_by_owner(items).items():
        email = owner_email(owner_items)
        with st.container(border=True):
            head = f"**{owner}**" + (f" · {email}" if email else " · _no email extracted_")
            st.markdown(f"{head} — {len(owner_items)} item{'s' if len(owner_items) != 1 else ''}")
            st.link_button(f"✉️ Email {owner}", owner_mail_url(owner, owner_items))
            for it in owner_items:
                due = f" · due {format_date(it['due_date'])}" if it.get("due_date") else ""
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"• {it.get('task', '')}{due}")
                c2.link_button("📅 Calendar", calendar_url(it), use_container_width=True)
else:
    st.caption("Paste a transcript, drop a public Doc URL, or upload a file — then hit **Extract**.")
