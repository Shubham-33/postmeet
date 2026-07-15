"""Capture the product screenshot used by the deck + case study.

Run:  python tools/capture_screenshot.py     (needs: pip install playwright pillow; uses installed Chrome)
Out:  docs/postmeet-screenshot.png

Composition notes (learned the hard way):
* The board lives in a max-w-6xl container: usable width 1056px, columns are 288px
  + 16px gaps. So 3 columns (896px) fit; 4 (1200px) overflow and get sliced.
  The sample transcript below is chosen to yield exactly 3 columns.
* Clip to summary+board — the *output* is the story, and it's naturally landscape.
  Including the input textarea nearly doubles the height for little payoff.
* clip= is capped at the viewport unless full_page=True is also passed.
* Use domcontentloaded, not networkidle — the Tailwind CDN never goes idle.
"""
import pathlib

from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "postmeet-screenshot.png"
URL = "https://postmeet.onrender.com/"

# Yields: Decisions + Marcus (2 items) + Jamie (1 item) = 3 columns, each card rich
# (task + context + date + email) so the board reads as substantive but never overflows.
SAMPLE = (
    "Priya: Q3 planning. Marcus, where's the auth refactor?\n"
    "Marcus: I'll have the PR ready by Friday July 10 — marcus@example.com for reviews. "
    "I'll also write the migration notes by Monday July 13 so QA isn't blocked.\n"
    "Priya: Good. We decided to ship dark mode in the v3 release.\n"
    "Jamie: I'll merge the design-token branch by Tuesday July 14 and tag Tara — "
    "it's blocking her work. jamie@example.com"
)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1500, "height": 1200}, device_scale_factor=2)
        pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_selector("#transcript", timeout=30000)
        pg.wait_for_timeout(1200)                       # let the Tailwind CDN paint
        pg.fill("#transcript", SAMPLE)
        pg.click("#extractBtn")
        pg.wait_for_selector("#summarySection:not(.hidden)", timeout=90000)
        pg.wait_for_timeout(2000)                       # cards settle

        m = pg.evaluate("""() => {
          const sy=window.scrollY, sx=window.scrollX;
          const sum=document.querySelector('#summarySection');
          const board=document.querySelector('#board');
          const cards=[...board.querySelectorAll('article')];
          const sr=sum.getBoundingClientRect(), br=board.getBoundingClientRect();
          // Clip to the board's own bottom so the column containers close cleanly.
          // (Clipping to the deepest card instead leaves them bleeding off the edge.)
          let deepest=0;
          (cards.length?cards:[board]).forEach(c=>{const r=c.getBoundingClientRect();
             if(r.bottom>deepest) deepest=r.bottom;});
          const bottom=Math.min(br.bottom, deepest+28);   // ...but don't include a tall empty floor
          return {left:Math.min(sr.left,br.left)+sx, top:sr.top+sy,
                  right:Math.max(sr.right,br.right)+sx, bottom:bottom+sy,
                  cols:board.children.length, overflow:board.scrollWidth>board.clientWidth};
        }""")

        assert not m["overflow"], (
            f"board overflows ({m['cols']} columns) — a column would be sliced. "
            "Use a transcript with fewer distinct owners."
        )
        print(f"  columns: {m['cols']}  ·  overflow: {m['overflow']}")

        pad = 16
        clip = {"x": max(0, m["left"] - pad), "y": max(0, m["top"] - pad),
                "width": (m["right"] + pad) - max(0, m["left"] - pad),
                "height": (m["bottom"] + pad) - max(0, m["top"] - pad)}
        pg.screenshot(path=str(OUT), clip=clip, full_page=True)   # full_page: clip isn't viewport-capped
        b.close()

    from PIL import Image
    im = Image.open(OUT)
    print(f"  saved {OUT.name}: {im.size[0]}x{im.size[1]} (ratio {im.size[0]/im.size[1]:.2f})")


if __name__ == "__main__":
    main()
