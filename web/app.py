"""Postmeet — Flask backend.

Extracts decisions and action items from meeting transcripts (or shared
Google Doc URLs) using NVIDIA NIM's Llama 3.1 (8B primary + 70B fallback,
OpenAI-compatible endpoint, JSON response mode). Renders a single-page UI;
dispatches per-action Calendar / Gmail prefills client-side via URL specs (no OAuth).

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
from typing import Any, Final

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, render_template, request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY: Final[str | None] = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NIM_API_KEY")
if not API_KEY:
    raise RuntimeError("Set NVIDIA_API_KEY in .env")

# Fast primary for low, predictable latency (~2-3s), with a higher-capacity
# fallback tried only if the primary errors — keeps the app responsive for
# anyone testing it, even months later. Override with NIM_MODEL to pin one model.
PRIMARY_MODEL: Final[str] = "meta/llama-3.1-8b-instruct"
FALLBACK_MODEL: Final[str] = "meta/llama-3.1-70b-instruct"
MODEL_NAME: Final[str] = os.environ.get("NIM_MODEL", "").strip() or PRIMARY_MODEL
# If the user pinned a model, honor only that; otherwise try primary then fallback.
MODEL_CHAIN: Final[tuple[str, ...]] = (
    (MODEL_NAME,) if os.environ.get("NIM_MODEL", "").strip() else (PRIMARY_MODEL, FALLBACK_MODEL)
)
NIM_URL: Final[str] = "https://integrate.api.nvidia.com/v1/chat/completions"

# HTTP / behavior tunables
DOC_FETCH_TIMEOUT_S: Final[int] = 15
NIM_TIMEOUT_S: Final[int] = 30
MIN_TRANSCRIPT_LENGTH: Final[int] = 30
GZIP_MIN_BYTES: Final[int] = 500
GZIP_COMPRESS_LEVEL: Final[int] = 6
INDEX_CACHE_SECONDS: Final[int] = 300

# Google Doc URL → Doc ID. Permits any of /edit, /view, /pub, /export.
DOC_ID_RE: Final[re.Pattern[str]] = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")

# Extraction contract — inlined into the system prompt so the model returns
# exactly this shape (NIM JSON mode guarantees the output is a JSON object).
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
    """Return the system prompt for the model, with today's date inlined for relative-date resolution."""
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

Output ONLY a single JSON object (no markdown fences, no prose) with exactly these keys:
{{"summary": string, "decisions": [string], "action_items": [{{"task": string, "owner": string, "owner_email": string, "due_date": string, "context": string}}]}}
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


def parse_extraction(raw: str) -> dict[str, Any]:
    """Parse the model's text output into a dict, tolerating stray prose / fences.

    Slices from the first ``{`` to the last ``}`` before parsing, so a response
    wrapped in ```` ```json ```` fences or accompanied by chatter still decodes.

    :raises json.JSONDecodeError: No JSON object present, or the slice isn't valid JSON.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object in model output", raw, 0)
    return json.loads(raw[start : end + 1])


def complete(model: str, text: str) -> dict[str, Any]:
    """Run one extraction against a single NVIDIA NIM ``model``.

    Uses the OpenAI-compatible chat-completions endpoint in JSON response mode.
    Temperature is 0 for determinism; the system prompt pins the exact JSON shape.

    :raises RuntimeError: Non-2xx HTTP response from NVIDIA.
    :raises KeyError, IndexError: Response shape missing ``choices[0].message.content``.
    :raises json.JSONDecodeError: Model output contains no valid JSON object.
    :raises requests.RequestException: Network / timeout error.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction()},
            {"role": "user", "content": text},
        ],
        "temperature": 0,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        NIM_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"},
        json=payload,
        timeout=NIM_TIMEOUT_S,
    )
    if not response.ok:
        raise RuntimeError(f"NVIDIA API {response.status_code}: {response.text[:300]}")
    body = response.json()
    raw = body["choices"][0]["message"]["content"]
    return parse_extraction(raw)


def call_llm(text: str) -> dict[str, Any]:
    """Extract structured output, trying each model in :data:`MODEL_CHAIN` in order.

    Transient failures (timeouts, connection errors, upstream 5xx) on one model
    fall through to the next — so a cold or overloaded primary model degrades to
    a faster fallback instead of failing the request. Malformed *content* from a
    model is NOT retried (a fresh model won't fix a parsing contract issue); it
    propagates so the caller returns a clear 502.

    :raises requests.RequestException, RuntimeError: All models in the chain failed.
    :raises KeyError, IndexError, json.JSONDecodeError: The reached model returned
        an unparseable response.
    """
    last_transient: Exception | None = None
    for model in MODEL_CHAIN:
        try:
            return complete(model, text)
        except (requests.RequestException, RuntimeError) as e:
            last_transient = e
            continue
    raise last_transient  # type: ignore[misc]  # chain is non-empty, so this is set


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
        return jsonify(call_llm(transcript))
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Model returned malformed output: {e}"}), 502
    except (requests.RequestException, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
