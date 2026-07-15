"""Render the case-study markdown into styled HTML pages served from our own site.

Source of truth stays the .md files (still readable on GitHub). This produces a
sibling .html for each, in the same design system as the deck + hub, so links
never leave the site.
"""
import re
import pathlib
import markdown

BASE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "case-study"

DOCS = [
    ("01-product-vision.md",       "Product Vision",            "Ideation"),
    ("02-mrd.md",                  "MRD — Market Requirements", "Ideation"),
    ("03-prd.md",                  "PRD — Product Requirements","Ideation"),
    ("04-user-guide.md",           "User Guide & Manual",       "Ideation"),
    ("05-research-plan.md",        "Research Plan",             "Planning & Strategy"),
    ("06-methodology.md",          "Methodology",               "Planning & Strategy"),
    ("07-7p-analysis.md",          "7P Analysis",               "Planning & Strategy"),
    ("08-development-execution.md","Development & Execution",   "Development & Execution"),
    ("09-launch-plan.md",          "Launch Plan",               "Development & Execution"),
    ("10-post-launch.md",          "Post-Launch",               "Development & Execution"),
]

CSS = """
  :root{
    --bg:#FAFAFB; --panel:#FFFFFF; --panel-2:#F1F2F5;
    --ink:#16181F; --muted:#5A616E; --faint:#8B919D; --line:#E4E6EB;
    --accent:#C2410C; --accent-soft:rgba(194,65,12,.07); --accent-line:rgba(194,65,12,.28);
    --shadow:rgba(20,22,30,.07);
    --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --font-mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
    --font-serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  }
  @media (prefers-color-scheme:dark){
    :root{ --bg:#0D0E12; --panel:#14161C; --panel-2:#1B1E26;
      --ink:#ECEEF2; --muted:#9AA1AE; --faint:#666D7A; --line:#262A33;
      --accent:#F2764B; --accent-soft:rgba(242,118,75,.09); --accent-line:rgba(242,118,75,.34);
      --shadow:rgba(0,0,0,.4); }
  }
  :root[data-theme="dark"]{ --bg:#0D0E12; --panel:#14161C; --panel-2:#1B1E26;
    --ink:#ECEEF2; --muted:#9AA1AE; --faint:#666D7A; --line:#262A33;
    --accent:#F2764B; --accent-soft:rgba(242,118,75,.09); --accent-line:rgba(242,118,75,.34);
    --shadow:rgba(0,0,0,.4); }
  :root[data-theme="light"]{ --bg:#FAFAFB; --panel:#FFFFFF; --panel-2:#F1F2F5;
    --ink:#16181F; --muted:#5A616E; --faint:#8B919D; --line:#E4E6EB;
    --accent:#C2410C; --accent-soft:rgba(194,65,12,.07); --accent-line:rgba(194,65,12,.28);
    --shadow:rgba(20,22,30,.07); }

  *{box-sizing:border-box}
  html{scroll-behavior:smooth;scroll-padding-top:5rem}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-sans);
    line-height:1.68;-webkit-font-smoothing:antialiased}
  .rule{height:3px;background:var(--accent);position:sticky;top:0;z-index:20}

  .topbar{position:sticky;top:3px;z-index:19;background:color-mix(in srgb,var(--bg) 88%,transparent);
    backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
  .topbar .in{max-width:860px;margin:0 auto;padding:.7rem clamp(1.1rem,4vw,2rem);
    display:flex;align-items:center;justify-content:space-between;gap:1rem}
  .crumb{font-family:var(--font-mono);font-size:.74rem;color:var(--faint);text-decoration:none;
    display:flex;align-items:center;gap:.5rem;min-width:0}
  .crumb:hover{color:var(--accent)}
  .crumb b{color:var(--ink);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .tools{display:flex;gap:.5rem;flex-shrink:0}
  .tool{font-family:var(--font-mono);font-size:.7rem;background:var(--panel);color:var(--muted);
    border:1px solid var(--line);border-radius:4px;padding:.32rem .6rem;cursor:pointer;text-decoration:none}
  .tool:hover{border-color:var(--accent);color:var(--accent)}

  main{max-width:860px;margin:0 auto;padding:clamp(1.8rem,5vw,3rem) clamp(1.1rem,4vw,2rem) 1rem}

  /* prose */
  main h1{font-size:clamp(1.9rem,4.4vw,2.8rem);line-height:1.1;letter-spacing:-.025em;
    margin:0 0 1rem;font-weight:680;text-wrap:balance}
  main h2{font-size:clamp(1.3rem,2.6vw,1.7rem);letter-spacing:-.018em;margin:2.8rem 0 .9rem;
    padding-top:1.4rem;border-top:1px solid var(--line);font-weight:660;text-wrap:balance}
  main h3{font-size:1.08rem;margin:1.9rem 0 .6rem;font-weight:640;letter-spacing:-.01em}
  main h4{font-size:.95rem;margin:1.4rem 0 .5rem;font-weight:640;color:var(--muted)}
  main p{margin:.9rem 0}
  main ul,main ol{margin:.9rem 0;padding-left:1.4rem}
  main li{margin:.35rem 0}
  main li::marker{color:var(--accent)}
  main a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-line)}
  main a:hover{border-bottom-color:var(--accent)}
  main strong{font-weight:660;color:var(--ink)}
  main hr{border:0;border-top:1px solid var(--line);margin:2.4rem 0}
  main blockquote{margin:1.4rem 0;padding:.9rem 1.2rem;border-left:2px solid var(--accent);
    background:var(--accent-soft);border-radius:0 4px 4px 0;color:var(--muted)}
  main blockquote p{margin:.4rem 0}
  main blockquote strong{color:var(--ink)}
  main code{font-family:var(--font-mono);font-size:.86em;background:var(--panel-2);
    border:1px solid var(--line);border-radius:3px;padding:.1em .38em}
  main pre{background:var(--panel-2);border:1px solid var(--line);border-radius:6px;
    padding:1rem 1.1rem;overflow-x:auto;margin:1.3rem 0;line-height:1.45}
  main pre code{background:none;border:0;padding:0;font-size:.8rem}
  .tablewrap{overflow-x:auto;margin:1.3rem 0;border:1px solid var(--line);border-radius:6px;background:var(--panel)}
  main table{border-collapse:collapse;width:100%;font-size:.9rem}
  main th{text-align:left;font-family:var(--font-mono);font-size:.7rem;letter-spacing:.06em;
    text-transform:uppercase;color:var(--faint);font-weight:600;
    padding:.7rem .9rem;border-bottom:1px solid var(--line);white-space:nowrap;background:var(--panel-2)}
  main td{padding:.7rem .9rem;border-bottom:1px solid var(--line);vertical-align:top;color:var(--muted)}
  main tr:last-child td{border-bottom:0}
  main td strong{color:var(--ink)}
  main img{max-width:100%}

  .docnav{max-width:860px;margin:0 auto;padding:1rem clamp(1.1rem,4vw,2rem) 3.5rem;
    display:flex;gap:.8rem;justify-content:space-between;border-top:1px solid var(--line)}
  .docnav a{flex:1;text-decoration:none;border:1px solid var(--line);border-radius:6px;
    padding:.9rem 1rem;background:var(--panel);transition:border-color .15s,transform .15s}
  .docnav a:hover{border-color:var(--accent-line);transform:translateY(-2px)}
  .docnav .k{font-family:var(--font-mono);font-size:.66rem;letter-spacing:.1em;
    text-transform:uppercase;color:var(--accent);display:block}
  .docnav .v{color:var(--ink);font-size:.95rem;font-weight:600;display:block;margin-top:.25rem}
  .docnav .next{text-align:right}
  @media (max-width:640px){.docnav{flex-direction:column}}
"""

SCRIPT = """
  var tb=document.getElementById('themebtn'), root=document.documentElement;
  tb.onclick=function(){
    var t=root.getAttribute('data-theme');
    var next=t==='dark'?'light':'dark';
    root.setAttribute('data-theme',next);
    tb.textContent=(next==='dark'?'☾':'☀');
  };
"""

TPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Postmeet Case Study</title>
<meta name="description" content="{title} — part of the Postmeet product-management case study by Shubham Mittal.">
<meta property="og:title" content="{title} — Postmeet Case Study">
<meta property="og:description" content="{title}: part of an end-to-end AI product-management case study.">
<style>{css}</style>
</head>
<body>
<div class="rule"></div>
<div class="topbar"><div class="in">
  <a class="crumb" href="./">← <span>Case study</span> · <b>{phase}</b></a>
  <div class="tools">
    <a class="tool" href="https://postmeet.onrender.com/" target="_blank" rel="noopener">Live app ↗</a>
    <a class="tool" href="{md}" target="_blank" rel="noopener">.md ↗</a>
    <button class="tool" id="themebtn" aria-label="Toggle theme">◐</button>
  </div>
</div></div>

<main>
{body}
</main>

<nav class="docnav">
{prev}
{next}
</nav>

<script>{script}</script>
</body>
</html>
"""


def gh_slugify(value, separator="-"):
    """Slugify headings the way GitHub does, so anchors match in BOTH the rendered
    site and the .md on GitHub.

    Key difference from python-markdown's default: GitHub does NOT collapse runs of
    separators. "9. Risks & assumptions" → "9-risks--assumptions" (the '&' leaves a
    gap), whereas the default would give "9-risks-assumptions".
    """
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)      # drop punctuation, keep the spaces it occupied
    return re.sub(r"\s", separator, value)      # one separator per space — no collapsing


def render():
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"slugify": gh_slugify}},
    )
    for i, (fname, title, phase) in enumerate(DOCS):
        src = (BASE / fname).read_text()
        md.reset()
        body = md.convert(src)

        # keep links inside our own site: 02-mrd.md#x -> 02-mrd.html#x
        body = re.sub(r'href="(\d\d-[a-z0-9-]+)\.md(#[^"]*)?"',
                      lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', body)
        # tables need a scroll container so wide ones never break the page
        body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")

        prev_html = next_html = '<span></span>'
        if i > 0:
            p = DOCS[i - 1]
            prev_html = (f'<a class="prev" href="{p[0].replace(".md", ".html")}">'
                         f'<span class="k">← Previous</span><span class="v">{p[1]}</span></a>')
        if i < len(DOCS) - 1:
            n = DOCS[i + 1]
            next_html = (f'<a class="next" href="{n[0].replace(".md", ".html")}">'
                         f'<span class="k">Next →</span><span class="v">{n[1]}</span></a>')

        out = TPL.format(title=title, phase=phase, css=CSS, script=SCRIPT, body=body,
                         md=f"https://github.com/Shubham-33/postmeet/blob/main/docs/case-study/{fname}",
                         prev=prev_html, next=next_html)
        (BASE / fname.replace(".md", ".html")).write_text(out)
        print(f"  ✓ {fname} → {fname.replace('.md', '.html')}  ({len(out):,} bytes)")


if __name__ == "__main__":
    print("Rendering case-study docs → HTML")
    render()
    print("done")
