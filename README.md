# Postmeet

**Paste a meeting transcript → get a clean board of decisions and action items → push each one to Google Calendar / Gmail in one click.** No sign-in, no OAuth.

> 🔗 **Live demo:** **[postmeet.onrender.com](https://postmeet.onrender.com/)**
> 📊 **[Pitch deck](https://shubham-33.github.io/postmeet/)** · 📚 **[Full PM case study](https://shubham-33.github.io/postmeet/case-study/)** (Vision · MRD · PRD · Research · 7P · Launch)
> ⏱️ Try it in 30s: open the demo → **Load sample** → press **Extract** → click **📅 Calendar** on any card.
> _(Free-tier host — the first load after idle may take ~40s to wake, then it's fast.)_

Meeting commitments get forgotten because they live in someone's notes. Postmeet turns a raw transcript into a shared, distributable plan in a few seconds — extract the decisions and per-owner action items with an LLM, then hand each person a prefilled calendar event or email they just click *Save* / *Send* on.

---

## What it does

| Step | |
|---|---|
| **1. Input** | Paste a transcript, drop a **public Google Doc URL**, or upload a `.txt`/`.md` file |
| **2. Extract** | NVIDIA NIM (Llama 3.1) returns a structured summary, decisions, and action items — each with owner, email, due date, and context |
| **3. Edit** | Every field is editable inline before you send anything |
| **4. Distribute** | One click opens Google Calendar / Gmail **fully prefilled** — the "no-OAuth trick" (see below) |

## Why it's interesting (engineering highlights)

- **Structured LLM output, no retry loop** — calls NVIDIA NIM's OpenAI-compatible endpoint in JSON response mode with the schema pinned in the system prompt, plus a tolerant `{…}` parser. One model call per extraction.
- **Reliability by design** — a fast **Llama-3.1-8B** primary (~2–3s) with **automatic fallback to 70B** on any error, so the app stays responsive even if a model is cold. Model is env-overridable.
- **The no-OAuth trick** — Google Calendar and Gmail both accept prefilled actions via URL (`calendar/render?...`, `mail/?view=cm&...`). Click → your already-logged-in Google opens in a new tab, everything filled in. Looks like a real integration; needs zero auth setup, so anyone can test it in seconds.
- **Tested** — **69 tests, 100% line + branch coverage** on the backend (`app.py`) and the link builders (`links.py`), gated in CI. All HTTP is mocked; the suite runs in <150ms.
- **Two front ends, one core** — a polished Flask/HTML app and a Streamlit app share the same pure extraction + link-building logic.

## The product-management case study

The full PM record behind this product — **[read it here](https://shubham-33.github.io/postmeet/case-study/)** (or [browse on GitHub](docs/case-study/)):

| Phase | Documents |
|---|---|
| **Ideation** | [Product Vision](docs/case-study/01-product-vision.md) · [MRD](docs/case-study/02-mrd.md) · [PRD](docs/case-study/03-prd.md) · [User Guide](docs/case-study/04-user-guide.md) |
| **Planning & Strategy** | [Research Plan](docs/case-study/05-research-plan.md) · [Methodology](docs/case-study/06-methodology.md) · [7P Analysis](docs/case-study/07-7p-analysis.md) |
| **Development & Execution** | [Development & ADRs](docs/case-study/08-development-execution.md) · [Launch Plan](docs/case-study/09-launch-plan.md) · [Post-Launch](docs/case-study/10-post-launch.md) |

They're real working documents — including the decisions that were wrong, the metric that shipped unmeasured, and the assumptions still waiting on evidence.

## Tech stack

Python · Flask · **Streamlit** (deployed UI) · NVIDIA NIM (Llama 3.1) · Google Docs / Calendar / Gmail URL APIs · Google Cloud Run + Secret Manager · pytest (100% coverage) · ruff · GitHub Actions CI

## Run it locally

```bash
cd web
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# free NVIDIA key at https://build.nvidia.com
echo 'NVIDIA_API_KEY=nvapi-...' > ../.env

streamlit run streamlit_app.py        # Streamlit UI  → http://localhost:8501
# — or —
python app.py                         # Flask UI + JSON API → http://localhost:5050
```

Run the test suite:

```bash
cd web && pip install -r requirements-dev.txt && pytest      # 69 tests, 100% coverage gate
```

## Repo layout

| Path | What |
|---|---|
| [`web/app.py`](web/app.py) | Flask backend + the extraction pipeline (`call_llm`, `complete`, `parse_extraction`, `fetch_google_doc_text`) |
| [`web/links.py`](web/links.py) | Pure Calendar / Gmail / MOM URL builders (framework-free, 100% tested) |
| [`web/streamlit_app.py`](web/streamlit_app.py) | Streamlit UI — the deployed front end |
| [`web/templates/`](web/templates/), [`web/static/`](web/static/) | Flask single-page UI (editorial theme, inline editing, drag-drop) |
| [`web/tests/`](web/tests/) | pytest suite (`test_app.py`, `test_links.py`) |
| [`web/deploy.sh`](web/deploy.sh) | One-shot Cloud Run deploy |
| [`docs/case-study/`](docs/case-study/) | **The full PM case study** — Vision, MRD, PRD, User Guide, Research Plan, Methodology, 7P, ADRs, Launch & Post-Launch |
| [`web/README.md`](web/README.md) | Deeper technical notes, architecture, and rubric mapping |

## Deploy your own (free)

Hosted on **Render** via the [`render.yaml`](render.yaml) blueprint — a genuinely public URL, no viewer login:

1. Push to GitHub (already done if you're reading this here).
2. Go to **[dashboard.render.com](https://dashboard.render.com)** → **New → Blueprint** → connect this repo.
3. Render reads `render.yaml` and provisions the web service. Set the one secret it asks for:
   ```
   NVIDIA_API_KEY = nvapi-...your key...
   ```
4. Deploy → you get a public `https://<name>.onrender.com` URL. Paste it into the **Live demo** line at the top of this file.

> The Streamlit app (`web/streamlit_app.py`) also runs locally, but **Streamlit Community Cloud now gates every app behind a mandatory viewer sign-in**, so it isn't used for the public demo.

---

<sub>Built during PromptWars 2026 (a vibe-coding hackathon), then hardened for reliability and test coverage. No meeting data is stored — a refresh clears everything.</sub>
