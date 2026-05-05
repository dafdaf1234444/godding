#!/usr/bin/env python3
"""godding/swarm/visual_qa.py — visual quality check.

Uses Playwright (sync API) to:
  1. Open each page at desktop (1280x800) and mobile (380x740) viewports
  2. Save a PNG screenshot to data/qa-screens/{viewport}/{page}.png
  3. Run heuristics:
       - any element with overflowing text
       - any horizontal scrollbar (indicates overflow)
       - any console errors
  4. Write data/visual_qa.json with results

Playwright is optional. If it's not installed, the script writes a
data/visual_qa.json with status='skipped' and exits 0 — so the cloud
routine doesn't break.

Install once:
    pip install --break-system-packages playwright
    playwright install chromium

Run after starting a local server (default http://127.0.0.1:8000):
    python serve.py &
    python swarm/visual_qa.py
"""
from __future__ import annotations
import json, sys, os, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ROOT / "pages"
SHOTS = DATA / "qa-screens"

PAGE_LIST = ["index.html"] + [f"pages/{p.name}" for p in sorted(PAGES.glob("*.html"))]
BASE = os.environ.get("GODDING_BASE", "http://127.0.0.1:8000")

VIEWPORTS = {
    "desktop": (1280, 800),
    "mobile":  (380, 740),
}

OVERFLOW_JS = r"""
() => {
  const issues = [];
  const all = document.querySelectorAll('*');
  for (const el of all) {
    if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') continue;
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 50) {
      const r = el.getBoundingClientRect();
      issues.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className || '').toString().slice(0, 60),
        sw: el.scrollWidth, cw: el.clientWidth,
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }
      });
    }
  }
  return {
    horizontal_scroll: document.documentElement.scrollWidth > window.innerWidth + 2,
    page_w: document.documentElement.scrollWidth,
    win_w: window.innerWidth,
    overflow_count: issues.length,
    issues: issues.slice(0, 12),
  };
}
"""

def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "visual_qa.json").write_text(
            json.dumps({"status": "skipped", "reason": f"playwright not available: {e}"}),
            encoding="utf-8")
        print(json.dumps({"status": "skipped", "reason": str(e)}))
        return 0

    SHOTS.mkdir(parents=True, exist_ok=True)
    for k in VIEWPORTS:
        (SHOTS / k).mkdir(parents=True, exist_ok=True)

    out = {
        "generated": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "base": BASE,
        "results": {},
        "issues": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vname, (w, h) in VIEWPORTS.items():
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            console_errors = []
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))
            page.on("console",   lambda m: console_errors.append(m.text) if m.type == "error" else None)
            for url in PAGE_LIST:
                target = f"{BASE}/{url}"
                key = f"{vname}/{url}"
                try:
                    page.goto(target, wait_until="domcontentloaded", timeout=15000)
                    # tiny settle delay so canvases mount
                    page.wait_for_timeout(400)
                    info = page.evaluate(OVERFLOW_JS)
                    shot = SHOTS / vname / (url.replace("/", "_") + ".png")
                    page.screenshot(path=str(shot), full_page=False)
                    out["results"][key] = {
                        "ok": info["overflow_count"] == 0 and not info["horizontal_scroll"] and not console_errors,
                        "horizontal_scroll": info["horizontal_scroll"],
                        "page_w": info["page_w"], "win_w": info["win_w"],
                        "overflow_count": info["overflow_count"],
                        "console_errors": console_errors[:5],
                        "screenshot": str(shot.relative_to(ROOT)),
                        "issues": info["issues"],
                    }
                    if info["overflow_count"] > 0 or info["horizontal_scroll"] or console_errors:
                        out["issues"].append({"viewport": vname, "url": url,
                                              "horizontal_scroll": info["horizontal_scroll"],
                                              "overflow_count": info["overflow_count"],
                                              "console_errors": console_errors[:3]})
                    console_errors.clear()
                except Exception as e:
                    out["results"][key] = {"ok": False, "error": str(e)}
                    out["issues"].append({"viewport": vname, "url": url, "error": str(e)})
            ctx.close()
        browser.close()

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "visual_qa.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "results": len(out["results"]),
        "issues": len(out["issues"]),
        "screens_dir": str(SHOTS.relative_to(ROOT)),
    }))
    return 0

if __name__ == "__main__":
    sys.exit(main())
