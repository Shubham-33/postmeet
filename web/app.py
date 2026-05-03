"""Postmeet — Flask backend.

Extracts decisions and action items from meeting transcripts (or shared
Google Doc URLs) using Gemini 2.5 Flash with structured output. Renders a
single-page UI; dispatches per-action Calendar / Gmail prefills client-side
via URL specs (no OAuth).

Public surface:

* GET  ``/``         — render the single-page UI (Cache-Control'd, gzipped)
* POST ``/extract``  — accepts ``{"transcript": str}`` or ``{"doc_url": str}``,
                       returns ``{"summary", "decisions", "action_items"}``
"""
from __future__ import annotations

import gzip
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Final, Pattern

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, render_template, request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY: Final[str | None] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY in .env")

MODEL_NAME: Final[str] = "gemini-2.5-flash"
GEMINI_URL: Final[str] = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
)

# HTTP / behavior tunables
DOC_FETCH_TIMEOUT_S: Final[int] = 15
GEMINI_TIMEOUT_S: Final[int] = 30
MIN_TRANSCRIPT_LENGTH: Final[int] = 30
GZIP_MIN_BYTES: Final[int] = 500
GZIP_COMPRESS_LEVEL: Final[int] = 6
INDEX_CACHE_SECONDS: Final[int] = 300

# Google Doc URL → Doc ID. Permits any of /edit, /view, /pub, /export.
DOC_ID_RE: Final[Pattern[str]] = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")

# Gemini structured output schema — guarantees parseable JSON in responses.
RESPONSE_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": "string"},
                    "owner_email": {"type": "string"},
                    "due_date": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["task", "owner", "owner_email", "due_date", "context"],
            },
        },
    },
    "required": ["summary", "decisions", "action_items"],
}


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def system_instruction() -> str:
    """Return the system prompt for Gemini, with today's date inlined for relative-date resolution."""
    return f"""You extract structured outputs from meeting transcripts.

Today's date is {date.today().isoformat()}. Use this when resolving relative dates (e.g. "Friday", "next Monday", "by end of month") to absolute YYYY-MM-DD.

For each meeting, return:
- summary: 1-2 sentence summary
- decisions: explicit decisions made ("we decided X")
- action_items: each with task, owner (first name or "Unassigned"), owner_email, due_date, context

Field rules:
- owner_email: scan the entire transcript for any email address whose local-part (before @) matches or contains the owner's first name (case-insensitive). If found, use that email even if it appears elsewhere in the transcript than the action item itself. Otherwise empty string.
- due_date: YYYY-MM-DD if stated or strongly implied. Empty string if no deadline.
- context: ONE crisp sentence (max ~25 words) explaining WHY this task matters or what it depends on / unblocks. Pull from the surrounding discussion in the transcript. If genuinely no context exists, use empty string. Don't invent context.

Behavior:
- Only extract action items that are explicit commitments, not vague ideas
- One assignee per action item — split if multiple people share ownership
- Use the speaker's first name when 'I will...' is said
- Empty arrays if no transcript content
"""


def fetch_google_doc_text(url: str) -> str:
    """Fetch plain text from a publicly-shared Google Doc.

    Works for any Doc shared as ``Anyone with the link can view`` — Google's
    public export endpoint returns ``text/plain`` when ``?format=txt`` is set.
    No OAuth required.

    :param url: Any Doc URL containing ``/document/d/<DOC_ID>/...``.
    :returns: Plain-text contents of the Doc, stripped.
    :raises ValueError: URL doesn't match the expected Doc URL shape.
    :raises PermissionError: Doc is not publicly shared (401/403, or login redirect).
    :raises RuntimeError: Any other non-2xx fetch result.
    :raises requests.RequestException: Network error.
    """
    match = DOC_ID_RE.search(url)
    if not match:
        raise ValueError(
            "Could not find a Doc ID in that URL. "
            "Expected something like https://docs.google.com/document/d/DOC_ID/..."
        )
    doc_id = match.group(1)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export"
    response = requests.get(
        export_url,
        params={"format": "txt"},
        timeout=DOC_FETCH_TIMEOUT_S,
        allow_redirects=True,
    )
    if response.status_code in (401, 403):
        raise PermissionError(
            "This Google Doc isn't public. "
            "Set sharing to 'Anyone with the link can view' and try again."
        )
    if not response.ok:
        raise RuntimeError(f"Could not fetch Doc (HTTP {response.status_code}). Check the URL.")
    text = response.text.strip()
    if "<!doctype html>" in text[:200].lower() or "<html" in text[:200].lower():
        raise PermissionError(
            "That URL returned a login page — the Doc isn't shared publicly."
        )
    return text


def call_gemini(text: str) -> dict[str, Any]:
    """Send ``text`` to Gemini 2.5 Flash and return the structured-JSON extraction.

    Uses ``responseSchema`` so Gemini's output is guaranteed to match
    :data:`RESPONSE_SCHEMA`. Temperature is 0 for determinism.

    :raises RuntimeError: Non-2xx HTTP response from Gemini.
    :raises KeyError, IndexError: Response shape missing ``candidates[0].content.parts[0].text``.
    :raises json.JSONDecodeError: Inner text is not valid JSON.
    :raises requests.RequestException: Network error.
    """
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "systemInstruction": {"parts": [{"text": system_instruction()}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0,
        },
    }
    response = requests.post(
        GEMINI_URL,
        params={"key": API_KEY},
        json=payload,
        timeout=GEMINI_TIMEOUT_S,
    )
    if not response.ok:
        raise RuntimeError(f"Gemini {response.status_code}: {response.text[:300]}")
    body = response.json()
    raw = body["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Flask app + middleware
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24  # 1 day cache for /static/*

# Build ID injected into templates so cached JS/CSS busts on every restart.
BUILD_ID: Final[str] = str(int(Path(__file__).stat().st_mtime))


@app.context_processor
def inject_build_id() -> dict[str, str]:
    return {"build_id": BUILD_ID}


@app.after_request
def gzip_response(response: Response) -> Response:
    """Compress eligible responses when the client advertises gzip support.

    Skips: streamed responses (``direct_passthrough``), non-2xx, payloads
    under :data:`GZIP_MIN_BYTES` (compression overhead beats the win), and
    already-encoded responses (e.g. precompressed assets).
    """
    if response.direct_passthrough or response.status_code < 200 or response.status_code >= 300:
        return response
    if response.headers.get("Content-Encoding"):
        return response
    if "gzip" not in (request.headers.get("Accept-Encoding") or ""):
        return response
    if response.content_length is not None and response.content_length < GZIP_MIN_BYTES:
        return response
    data = gzip.compress(response.get_data(), compresslevel=GZIP_COMPRESS_LEVEL)
    response.set_data(data)
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = str(len(data))
    response.headers["Vary"] = "Accept-Encoding"
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index() -> Response:
    """Render the single-page UI with a public 5-minute browser cache."""
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = f"public, max-age={INDEX_CACHE_SECONDS}"
    return resp


@app.route("/extract", methods=["POST"])
def extract() -> tuple[Response, int] | Response:
    """Extract decisions and action items from a transcript or Doc URL.

    Request body (JSON):

    * ``{"transcript": str}`` — raw meeting transcript text, or
    * ``{"doc_url": str}`` — public Google Doc URL (we fetch + use the text)

    Returns ``200`` with ``{summary, decisions, action_items}`` on success,
    or ``{error}`` with an appropriate 4xx/5xx status on validation or
    upstream failure.
    """
    data = request.get_json(silent=True) or {}
    transcript: str = (data.get("transcript") or "").strip()
    doc_url: str = (data.get("doc_url") or "").strip()

    if doc_url:
        try:
            transcript = fetch_google_doc_text(doc_url)
        except PermissionError as e:
            return jsonify({"error": str(e)}), 403
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except (requests.RequestException, RuntimeError) as e:
            return jsonify({"error": f"Doc fetch failed: {e}"}), 502

    if len(transcript) < MIN_TRANSCRIPT_LENGTH:
        return jsonify({
            "error": f"Transcript is too short (need at least {MIN_TRANSCRIPT_LENGTH} characters)."
        }), 400

    try:
        return jsonify(call_gemini(transcript))
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Model returned malformed output: {e}"}), 502
    except (requests.RequestException, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
