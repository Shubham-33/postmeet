import json
import os
import re
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY in .env")

MODEL_NAME = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

DOC_ID_RE = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")

RESPONSE_SCHEMA = {
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
                },
                "required": ["task", "owner", "owner_email", "due_date"],
            },
        },
    },
    "required": ["summary", "decisions", "action_items"],
}


def system_instruction() -> str:
    return f"""You extract structured outputs from meeting transcripts.

Today's date is {date.today().isoformat()}. Use this when resolving relative dates (e.g. "Friday", "next Monday", "by end of month") to absolute YYYY-MM-DD.

For each meeting, return:
- summary: 1-2 sentence summary
- decisions: explicit decisions made ("we decided X")
- action_items: each with task, owner (first name or "Unassigned"), owner_email, due_date

Field rules:
- owner_email: scan the entire transcript for any email address whose local-part (before @) matches or contains the owner's first name (case-insensitive). If found, use that email even if it appears elsewhere in the transcript than the action item itself. Otherwise empty string.
- due_date: YYYY-MM-DD if stated or strongly implied. Empty string if no deadline.

Behavior:
- Only extract action items that are explicit commitments, not vague ideas
- One assignee per action item — split if multiple people share ownership
- Use the speaker's first name when 'I will...' is said
- Empty arrays if no transcript content
"""


def fetch_google_doc_text(url: str) -> str:
    """Fetch plain text from a publicly-shared Google Doc.

    Works for any Doc shared as 'Anyone with the link can view'. No OAuth needed —
    Google's public export endpoint returns text/plain when ?format=txt is set.
    """
    m = DOC_ID_RE.search(url)
    if not m:
        raise ValueError("Could not find a Doc ID in that URL. Expected something like https://docs.google.com/document/d/DOC_ID/...")
    doc_id = m.group(1)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export"
    r = requests.get(export_url, params={"format": "txt"}, timeout=15, allow_redirects=True)
    if r.status_code == 401 or r.status_code == 403:
        raise PermissionError("This Google Doc isn't public. Set sharing to 'Anyone with the link can view' and try again.")
    if not r.ok:
        raise RuntimeError(f"Could not fetch Doc (HTTP {r.status_code}). Check the URL.")
    text = r.text.strip()
    if "<!DOCTYPE html>" in text[:200].lower() or "<html" in text[:200].lower():
        raise PermissionError("That URL returned a login page — the Doc isn't shared publicly.")
    return text


def call_gemini(text: str) -> dict:
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "systemInstruction": {"parts": [{"text": system_instruction()}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0,
        },
    }
    r = requests.post(GEMINI_URL, params={"key": API_KEY}, json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
    body = r.json()
    raw = body["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json(silent=True) or {}
    transcript = (data.get("transcript") or "").strip()
    doc_url = (data.get("doc_url") or "").strip()

    if doc_url:
        try:
            transcript = fetch_google_doc_text(doc_url)
        except PermissionError as e:
            return jsonify({"error": str(e)}), 403
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except (requests.RequestException, RuntimeError) as e:
            return jsonify({"error": f"Doc fetch failed: {e}"}), 502

    if len(transcript) < 30:
        return jsonify({"error": "Transcript is too short (need at least 30 characters)."}), 400

    try:
        result = call_gemini(transcript)
        return jsonify(result)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Model returned malformed output: {e}"}), 502
    except (requests.RequestException, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
