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


def nim_success_body(summary="Summary.", decisions=None, action_items=None, content=None):
    """Shape of a real NVIDIA NIM chat-completions response with valid extraction JSON.

    Pass ``content`` to override the raw message text (e.g. for fenced / malformed cases).
    """
    if content is None:
        payload = {
            "summary": summary,
            "decisions": decisions if decisions is not None else ["We agreed."],
            "action_items": action_items if action_items is not None else [
                {
                    "task": "Do X",
                    "owner": "Alice",
                    "owner_email": "",
                    "due_date": "2026-12-01",
                    "context": "Unblocks the v3 launch",
                }
            ],
        }
        content = json.dumps(payload)
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


# ---------- module-level: missing API key ----------

def test_missing_api_key_raises(monkeypatch):
    """Reimporting app.py without NVIDIA_API_KEY/NIM_API_KEY must raise RuntimeError."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("NIM_API_KEY", raising=False)
    # Block dotenv from re-loading the project's .env (which would set the key back).
    with patch("dotenv.load_dotenv", lambda *a, **kw: None):
        # Drop cached module so the top-level guard runs again.
        sys.modules.pop("app", None)
        with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
            importlib.import_module("app")
    # Restore the module for downstream tests.
    sys.modules.pop("app", None)
    os.environ["NVIDIA_API_KEY"] = "test-key-fixture"
    importlib.import_module("app")


# ---------- system_instruction ----------

def test_system_instruction_includes_today(app_mod):
    s = app_mod.system_instruction()
    assert date.today().isoformat() in s
    assert "summary" in s
    assert "decisions" in s
    assert "action_items" in s
    # New: context field must be requested in the prompt
    assert "context" in s


def test_response_schema_includes_context(app_mod):
    """Schema must require a context field on each action item."""
    item_props = app_mod.RESPONSE_SCHEMA["properties"]["action_items"]["items"]
    assert "context" in item_props["properties"]
    assert "context" in item_props["required"]


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


# ---------- parse_extraction ----------

def test_parse_extraction_happy(app_mod):
    assert app_mod.parse_extraction('{"a": 1}') == {"a": 1}


def test_parse_extraction_strips_fences_and_prose(app_mod):
    """Model may wrap JSON in ```json fences or add chatter — we slice { … }."""
    raw = 'Sure! ```json\n{"a": 1, "b": [2]}\n``` done'
    assert app_mod.parse_extraction(raw) == {"a": 1, "b": [2]}


def test_parse_extraction_no_object_raises(app_mod):
    """No braces at all → JSONDecodeError (surfaces as 502 'malformed' upstream)."""
    with pytest.raises(json.JSONDecodeError):
        app_mod.parse_extraction("just some text, no json here")


def test_parse_extraction_open_brace_only_raises(app_mod):
    """Opening brace but no closing brace → JSONDecodeError."""
    with pytest.raises(json.JSONDecodeError):
        app_mod.parse_extraction("not json{")


# ---------- call_llm ----------

def test_call_llm_happy(app_mod):
    body = nim_success_body()
    with patch("app.requests.post", return_value=make_response(200, json_body=body)):
        result = app_mod.call_llm("transcript text")
    assert "summary" in result
    assert result["decisions"] == ["We agreed."]


def test_call_llm_http_error(app_mod):
    """Every model in the chain returns 5xx → the last error propagates."""
    with patch("app.requests.post", return_value=make_response(500, text="quota")):
        with pytest.raises(RuntimeError, match="NVIDIA API 500"):
            app_mod.call_llm("transcript text")


def test_call_llm_falls_back_on_primary_timeout(app_mod):
    """Primary model times out → the fallback model is tried and succeeds."""
    good = make_response(200, json_body=nim_success_body(summary="via fallback"))
    with patch("app.requests.post", side_effect=[requests.Timeout("cold"), good]) as mp:
        result = app_mod.call_llm("transcript text")
    assert result["summary"] == "via fallback"
    assert mp.call_count == 2
    assert mp.call_args_list[0].kwargs["json"]["model"] == app_mod.PRIMARY_MODEL
    assert mp.call_args_list[1].kwargs["json"]["model"] == app_mod.FALLBACK_MODEL


def test_call_llm_all_models_fail_raises_last(app_mod):
    """When every model errors transiently, the final exception is re-raised."""
    with patch("app.requests.post", side_effect=requests.ConnectionError("down")):
        with pytest.raises(requests.ConnectionError):
            app_mod.call_llm("transcript text")


def test_call_llm_malformed_content_not_retried(app_mod):
    """A parse error is the model's, not transient — do NOT waste the fallback on it."""
    bad = make_response(200, json_body=nim_success_body(content="no json here"))
    with patch("app.requests.post", return_value=bad) as mp:
        with pytest.raises(json.JSONDecodeError):
            app_mod.call_llm("transcript text")
    assert mp.call_count == 1  # stopped at the first model


def test_nim_model_env_override_pins_single_model(monkeypatch):
    """Setting NIM_MODEL pins exactly that model and disables the fallback chain."""
    monkeypatch.setenv("NIM_MODEL", "meta/custom-model")
    with patch("dotenv.load_dotenv", lambda *a, **kw: None):
        sys.modules.pop("app", None)
        mod = importlib.import_module("app")
    assert mod.MODEL_NAME == "meta/custom-model"
    assert mod.MODEL_CHAIN == ("meta/custom-model",)
    # Restore the shared (no-override) module for downstream tests.
    monkeypatch.delenv("NIM_MODEL", raising=False)
    sys.modules.pop("app", None)
    importlib.import_module("app")


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
    body = nim_success_body()
    with patch("app.requests.post", return_value=make_response(200, json_body=body)):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 200
    out = res.get_json()
    assert out["summary"] == "Summary."
    assert out["action_items"][0]["owner"] == "Alice"


# ---------- /extract — model failure modes ----------

def test_extract_model_runtime_error_502(client):
    with patch("app.requests.post", return_value=make_response(500, text="quota exceeded")):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "NVIDIA API 500" in res.get_json()["error"]


def test_extract_model_network_error_502(client):
    with patch("app.requests.post", side_effect=requests.ConnectionError("boom")):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "boom" in res.get_json()["error"]


def test_extract_model_malformed_json_502(client):
    """Model returns a 200 but its message content is not valid JSON."""
    bad_body = nim_success_body(content="not json{")
    with patch("app.requests.post", return_value=make_response(200, json_body=bad_body)):
        res = client.post("/extract", json={"transcript": "Alice will do X by tomorrow morning."})
    assert res.status_code == 502
    assert "malformed" in res.get_json()["error"]


def test_extract_model_missing_choices_502(client):
    """Model response is missing the 'choices' key entirely (e.g. a content filter)."""
    bad_body = {"error": {"message": "content filtered"}}
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
    body = nim_success_body(summary="Migration discussion.")
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
