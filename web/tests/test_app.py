"""Backend test suite for Postmeet — targets 100% line coverage of app.py."""
import importlib
import json
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests


# ---------- helpers ----------

def make_response(status_code=200, json_body=None, text="", ok=None):
    """Build a mock requests.Response with controllable status and body."""
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.text = text if text else (json.dumps(json_body) if json_body is not None else "")
    r.ok = ok if ok is not None else (200 <= status_code < 300)
    r.json = MagicMock(return_value=json_body if json_body is not None else {})
    return r


def gemini_success_body(summary="Summary.", decisions=None, action_items=None):
    """Shape of a real Gemini generateContent response with valid extraction JSON."""
    payload = {
        "summary": summary,
        "decisions": decisions if decisions is not None else ["We agreed."],
        "action_items": action_items if action_items is not None else [
            {"task": "Do X", "owner": "Alice", "owner_email": "", "due_date": "2026-12-01"}
        ],
    }
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}],
    }


# ---------- module-level: missing API key ----------

def test_missing_api_key_raises(monkeypatch):
    """Reimporting app.py without GOOGLE_API_KEY/GEMINI_API_KEY must raise RuntimeError."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Block dotenv from re-loading the project's .env (which would set the key back).
    with patch("dotenv.load_dotenv", lambda *a, **kw: None):
        # Drop cached module so the top-level guard runs again.
        sys.modules.pop("app", None)
        with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
            importlib.import_module("app")
    # Restore the module for downstream tests.
    sys.modules.pop("app", None)
    os.environ["GOOGLE_API_KEY"] = "test-key-fixture"
    importlib.import_module("app")


# ---------- system_instruction ----------

def test_system_instruction_includes_today(app_mod):
    s = app_mod.system_instruction()
    assert date.today().isoformat() in s
    assert "summary" in s
    assert "decisions" in s
    assert "action_items" in s


# ---------- DOC_ID_RE ----------

@pytest.mark.parametrize("url,expected_id", [
    ("https://docs.google.com/document/d/AbC_123-xyz/edit", "AbC_123-xyz"),
    ("https://docs.google.com/document/d/abc/view?usp=sharing", "abc"),
    ("http://docs.google.com/document/d/zzz/pub", "zzz"),
    ("/document/d/relative-id-too/", "relative-id-too"),
])
def test_doc_id_regex_matches(app_mod, url, expected_id):
    m = app_mod.DOC_ID_RE.search(url)
    assert m is not None
    assert m.group(1) == expected_id


@pytest.mark.parametrize("url", [
    "https://example.com/doc/123",
    "https://docs.google.com/spreadsheet/d/abc",
    "not a url at all",
    "",
])
def test_doc_id_regex_no_match(app_mod, url):
    assert app_mod.DOC_ID_RE.search(url) is None


# ---------- fetch_google_doc_text ----------

def test_fetch_doc_invalid_url(app_mod):
    with pytest.raises(ValueError, match="Doc ID"):
        app_mod.fetch_google_doc_text("https://example.com/no-doc")


def test_fetch_doc_happy(app_mod):
    text = "Alice: action item content."
    fake = make_response(200, text=text)
    with patch("app.requests.get", return_value=fake) as mock_get:
        out = app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")
    assert out == text
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "docs.google.com/document/d/abc/export" in called_url


def test_fetch_doc_401_is_permission_error(app_mod):
    with patch("app.requests.get", return_value=make_response(401, text="auth")):
        with pytest.raises(PermissionError, match="public"):
            app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")


def test_fetch_doc_403_is_permission_error(app_mod):
    with patch("app.requests.get", return_value=make_response(403, text="forbidden")):
        with pytest.raises(PermissionError, match="public"):
            app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")


def test_fetch_doc_500_is_runtime_error(app_mod):
    with patch("app.requests.get", return_value=make_response(500, text="oops")):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")


def test_fetch_doc_html_login_page_is_permission_error(app_mod):
    html = "<!DOCTYPE html><html><body>Sign in</body></html>"
    with patch("app.requests.get", return_value=make_response(200, text=html)):
        with pytest.raises(PermissionError, match="login"):
            app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")


def test_fetch_doc_html_lowercase_login_page(app_mod):
    """Defensive: the heuristic uses lower-cased prefix matching."""
    html = "<html><head><title>Sign in</title></head></html>"
    with patch("app.requests.get", return_value=make_response(200, text=html)):
        with pytest.raises(PermissionError):
            app_mod.fetch_google_doc_text("https://docs.google.com/document/d/abc/edit")


# ---------- call_gemini ----------

def test_call_gemini_happy(app_mod):
    body = gemini_success_body()
    with patch("app.requests.post", return_value=make_response(200, json_body=body)):
        result = app_mod.call_gemini("transcript text")
    assert "summary" in result
    assert result["decisions"] == ["We agreed."]


def test_call_gemini_http_error(app_mod):
    with patch("app.requests.post", return_value=make_response(500, text="quota")):
        with pytest.raises(RuntimeError, match="Gemini 500"):
            app_mod.call_gemini("transcript text")


# ---------- / (index) ----------

def test_index_renders_html(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "<title>Postmeet" in body
    assert "Extract" in body


def test_index_sets_cache_control(client):
    res = client.get("/")
    assert "max-age=300" in res.headers.get("Cache-Control", "")
    assert "public" in res.headers.get("Cache-Control", "")


# ---------- gzip after_request hook ----------

def test_gzip_compresses_when_accepted(client):
    """Large response + Accept-Encoding: gzip → body is compressed."""
    res = client.get("/", headers={"Accept-Encoding": "gzip, deflate"})
    assert res.status_code == 200
    assert res.headers.get("Content-Encoding") == "gzip"
    assert "Accept-Encoding" in res.headers.get("Vary", "")
    # Compressed payload starts with gzip magic bytes \x1f\x8b
    raw = res.get_data()
    assert raw[:2] == b"\x1f\x8b"


def test_gzip_skipped_when_not_accepted(client):
    """No Accept-Encoding header → response is not compressed."""
    res = client.get("/", headers={"Accept-Encoding": "identity"})
    assert res.status_code == 200
    assert res.headers.get("Content-Encoding") != "gzip"


def test_gzip_skipped_when_header_missing(client):
    """Werkzeug test client sends no Accept-Encoding by default → no compression."""
    res = client.get("/", headers={})
    # default test_client sends "Accept-Encoding: " — neither gzip nor None
    if "gzip" not in (res.request.headers.get("Accept-Encoding") or ""):
        assert res.headers.get("Content-Encoding") != "gzip"


def test_gzip_skipped_for_small_payload(app_mod):
    """Responses under GZIP_MIN_BYTES should pass through unchanged."""
    from flask import Response
    with app_mod.app.test_request_context("/", headers={"Accept-Encoding": "gzip"}):
        small = Response("tiny", mimetype="text/plain")
        small.content_length = 4
        out = app_mod.gzip_response(small)
        assert out.headers.get("Content-Encoding") != "gzip"
        assert out.get_data(as_text=True) == "tiny"


def test_gzip_skipped_for_error_response(app_mod):
    """Non-2xx responses are not compressed (saves CPU on error paths)."""
    from flask import Response
    with app_mod.app.test_request_context("/", headers={"Accept-Encoding": "gzip"}):
        err = Response("x" * 1000, status=500, mimetype="text/plain")
        out = app_mod.gzip_response(err)
        assert out.headers.get("Content-Encoding") != "gzip"


def test_gzip_skipped_when_already_encoded(app_mod):
    """Already-encoded responses (e.g. precompressed assets) pass through."""
    from flask import Response
    with app_mod.app.test_request_context("/", headers={"Accept-Encoding": "gzip"}):
        pre = Response(b"x" * 1000, mimetype="text/plain")
        pre.headers["Content-Encoding"] = "br"  # already brotli
        out = app_mod.gzip_response(pre)
        assert out.headers["Content-Encoding"] == "br"  # unchanged


def test_gzip_skipped_for_direct_passthrough(app_mod):
    """Streaming responses (direct_passthrough) cannot be compressed in-place."""
    from flask import Response
    with app_mod.app.test_request_context("/", headers={"Accept-Encoding": "gzip"}):
        streamed = Response("x" * 1000, mimetype="text/plain")
        streamed.direct_passthrough = True
        out = app_mod.gzip_response(streamed)
        assert out.headers.get("Content-Encoding") != "gzip"


# ---------- /extract — transcript path ----------

def test_extract_short_transcript_400(client):
    res = client.post("/extract", json={"transcript": "hi"})
    assert res.status_code == 400
    assert "too short" in res.get_json()["error"]


def test_extract_empty_payload_400(client):
    res = client.post("/extract", json={})
    assert res.status_code == 400


def test_extract_non_json_payload_400(client):
    """Defensive: silent=True returns None which we coerce to {}."""
    res = client.post("/extract", data="garbage", content_type="text/plain")
    assert res.status_code == 400


def test_extract_transcript_happy(client):
    body = gemini_success_body()
    with patch("app.requests.post", return_value=make_response(200, json_body=body)):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 200
    out = res.get_json()
    assert out["summary"] == "Summary."
    assert out["action_items"][0]["owner"] == "Alice"


# ---------- /extract — gemini failure modes ----------

def test_extract_gemini_runtime_error_502(client):
    with patch("app.requests.post", return_value=make_response(500, text="quota exceeded")):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "Gemini 500" in res.get_json()["error"]


def test_extract_gemini_network_error_502(client):
    with patch("app.requests.post", side_effect=requests.ConnectionError("boom")):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "boom" in res.get_json()["error"]


def test_extract_gemini_malformed_json_502(client):
    """Gemini returns a 200 but its inner text is not valid JSON."""
    bad_body = {"candidates": [{"content": {"parts": [{"text": "not json{"}]}}]}
    with patch("app.requests.post", return_value=make_response(200, json_body=bad_body)):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "malformed" in res.get_json()["error"]


def test_extract_gemini_missing_candidates_502(client):
    """Gemini response is missing the 'candidates' key entirely."""
    bad_body = {"promptFeedback": {"blockReason": "SAFETY"}}
    with patch("app.requests.post", return_value=make_response(200, json_body=bad_body)):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "malformed" in res.get_json()["error"]


# ---------- /extract — doc_url path ----------

def test_extract_doc_url_invalid_400(client):
    res = client.post("/extract", json={"doc_url": "https://example.com/not-a-doc"})
    assert res.status_code == 400
    assert "Doc ID" in res.get_json()["error"]


def test_extract_doc_url_private_403(client):
    with patch("app.requests.get", return_value=make_response(403)):
        res = client.post("/extract", json={"doc_url": "https://docs.google.com/document/d/abc/edit"})
    assert res.status_code == 403
    assert "public" in res.get_json()["error"]


def test_extract_doc_url_fetch_5xx_502(client):
    with patch("app.requests.get", return_value=make_response(503)):
        res = client.post("/extract", json={"doc_url": "https://docs.google.com/document/d/abc/edit"})
    assert res.status_code == 502
    assert "Doc fetch failed" in res.get_json()["error"]


def test_extract_doc_url_network_error_502(client):
    with patch("app.requests.get", side_effect=requests.Timeout("slow")):
        res = client.post("/extract", json={"doc_url": "https://docs.google.com/document/d/abc/edit"})
    assert res.status_code == 502
    assert "Doc fetch failed" in res.get_json()["error"]


def test_extract_doc_url_happy(client):
    transcript_text = "Alice: I will ship the migration by Friday May 29."
    fetch = make_response(200, text=transcript_text)
    body = gemini_success_body(summary="Migration discussion.")
    with patch("app.requests.get", return_value=fetch), \
         patch("app.requests.post", return_value=make_response(200, json_body=body)):
        res = client.post("/extract", json={"doc_url": "https://docs.google.com/document/d/abc/edit"})
    assert res.status_code == 200
    assert res.get_json()["summary"] == "Migration discussion."


def test_extract_doc_url_too_short_after_fetch_400(client):
    """Even valid Doc URL + valid fetch can return text shorter than 30 chars."""
    fetch = make_response(200, text="hi")
    with patch("app.requests.get", return_value=fetch):
        res = client.post("/extract", json={"doc_url": "https://docs.google.com/document/d/abc/edit"})
    assert res.status_code == 400
    assert "too short" in res.get_json()["error"]
