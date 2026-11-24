"""Render an FNN data-story slide: one headline, one story, one chart, one highlighted team.

    python story.py stories/gw11-bench.json                  # writes out/gw11/
    python story.py stories/gw11-bench.json --out ~/Desktop/FNN

Exports at 2x (2160x2700) per the FNN story brief. Every number in the copy is a
{placeholder} filled from the data, so nothing on the slide is typed by hand.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

from build import ROOT, W, H, serve

FONTS = ("https://fonts.googleapis.com/css2?family=Anton"
         "&family=Archivo:wdth,wght@62..125,100..900"
         "&family=Barlow+Condensed:wght@500;600;700&display=block")
HEAD = (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONTS}">'
        '<link rel="stylesheet" href="/styles/story.css"></head><body><div class="story">')
TAIL = '</div></body></html>'

CREST = '''<svg class="crest" viewBox="0 0 56 64"><path d="M28 2 52 10v20c0 15-10 26-24 32C14 56 4 45 4 30V10Z" fill="#0B0D0C" stroke="#3A403D" stroke-width="2"/>
<path d="M28 9 46 15v15c0 11-7 19-18 24C17 49 10 41 10 30V15Z" fill="none" stroke="#B8F25A" stroke-width="2"/>
<text x="28" y="40" text-anchor="middle" font-family="Anton" font-size="22" fill="#B8F25A">FL</text></svg>'''

# chart geometry (px, 1x): chart zone y 590-1190, 72px side margins
NAME_COL, BAR_MAX, ROW_H, ROWS_TOP = 330, 520, 54, 50


def num(x):
    return f"{x:g}"


def context(data):
    teams = data["teams"]
    for t in teams:
        t["value"] = sum(p for _, p in t["bench"] if p is not None)
    teams.sort(key=lambda t: -t["value"])
    hl = next((t for t in teams if t["team"] == data["highlight"]), None)
    if hl is None:
        sys.exit(f"highlight {data['highlight']!r} is not one of the teams")
    top_player, top_points = max(((n, p) for n, p in hl["bench"] if p is not None), key=lambda x: x[1])
    best_gw = max(t["gw_points"] for t in teams)
    return {
        "gw": data["gw"], "value": hl["value"], "team": hl["team"], "manager": hl["manager"],
        "top_player": top_player, "top_points": top_points,
        "mean": num(round(sum(t["value"] for t in teams) / len(teams), 1)),
        "gw_points": hl["gw_points"], "best_gw_points": best_gw,
    }, teams, hl


def words(text):
    return len(re.sub(r"<[^>]+>", " ", text).split())


def check(data, ctx):
    errors = []
    head = " ".join(t.format(**ctx) for t, _ in data["headline"])
    for label, text, limit in (("headline", head, 5), ("deck", data["deck"].format(**ctx), 14),
                               ("footnote", data["footnote"].format(**ctx), 12)):
        if words(text) > limit:
            errors.append(f"{label} is {words(text)} words, budget is {limit}: {text}")
    if re.search(r"\d", "".join(t for t, _ in data["headline"]) + data["deck"] + data["footnote"]):
        errors.append("a number is typed into the copy; use a {placeholder} from the data")
    if errors:
        sys.exit("story has problems:\n  " + "\n  ".join(errors))


def chart(data, ctx, teams, hl):
    vmax = max(t["value"] for t in teams) or 1
    x = lambda v: NAME_COL + v / vmax * BAR_MAX
    rows = []
    for i, t in enumerate(teams):
        on = t is hl
        w = t["value"] / vmax * BAR_MAX
        note = (f'<span class="note">{html.escape(data["bar_note"].format(**ctx))}</span>'
                if on and data.get("bar_note") else "")
        rows.append(
            f'<div class="row{" on " + data["accent"] if on else ""}" style="top:{ROWS_TOP + i * ROW_H}px">'
            f'<div class="nm">{html.escape(t["team"])}</div>'
            f'<div class="bar" style="left:{NAME_COL}px;width:{w:.1f}px">{note}</div>'
            f'<div class="val" style="left:{x(t["value"]) + 14:.1f}px">{t["value"]}</div></div>')
    ref = ""
    if data.get("reference"):
        rx = x(float(ctx["mean"]))
        ref = (f'<div class="ref" style="left:{rx:.1f}px;top:{ROWS_TOP - 6}px;height:{len(teams) * ROW_H}px"></div>'
               f'<div class="reflbl" style="left:{rx:.1f}px">{html.escape(data["reference"].format(**ctx))}</div>')
    return f'<div class="chart">{ref}{"".join(rows)}</div>'


def slide(data):
    ctx, teams, hl = context(data)
    check(data, ctx)
    place = data.get("photo_place")  # {"width", "left", "top"} in px, to put the subject upper-right, clear of the headline
    style = (f'width:{place["width"]}px;height:auto;left:{place["left"]}px;top:{place["top"]}px' if place
             else f'object-position:{data.get("focus", "70% 30%")}')
    photo = (f'<img class="photo{" placed" if place else ""}" src="/assets/photos/{data["photo"]}" style="{style}">'
             if data.get("photo") else '<div class="atmos"></div>')
    head = " ".join(f'<span class="chrome {tone}">{html.escape(w)}</span>'
                    for t, tone in data["headline"] for w in t.format(**ctx).split())
    label, span = (k.format(**ctx) for k in data["kicker"])
    n, total = data["slide"]
    return f'''{photo}<div class="grain"></div><div class="rim"></div><div class="lfade"></div><div class="vfade"></div><div class="frame"></div>
<div class="mast"><div class="plate"></div>{CREST}<div class="fl">FARMERS LEAGUE</div><div class="fnn">FNN</div><div class="chip">GW{ctx["gw"]}</div></div>
<div class="kick"><i></i><b>{html.escape(label)}</b><span>{html.escape(span)}</span></div>
<div class="lede"><h1 style="font-size:{data.get("headline_size", 150)}px;max-width:{data.get("headline_width", 936)}px">{head}</h1>
<p class="deck">{html.escape(data["deck"].format(**ctx))}</p></div>
{chart(data, ctx, teams, hl)}
<div class="foot">{html.escape(data["footnote"].format(**ctx))}</div>
<div class="brand">FARMERS NEWS NETWORK · EST 2019</div>
<div class="tab"><span>{n} / {total}</span></div>'''


def render(path, out):
    data = json.loads(Path(path).read_text())
    gw = data["gw"]
    pages = ROOT / "build" / f"gw{gw}"
    pages.mkdir(parents=True, exist_ok=True)
    name = f"Story-{data['name']}"
    (pages / f"{name}.html").write_text(HEAD + slide(data) + TAIL)
    out = Path(out or ROOT / "out" / f"gw{gw}").expanduser()
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    server = serve()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()  # sRGB: the brief's hex values render as written
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            page.goto(f"http://127.0.0.1:{server.server_port}/build/gw{gw}/{name}.html", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            dest = out / f"Farmers-League-GW{gw}-{name}.png"
            page.screenshot(path=dest, clip={"x": 0, "y": 0, "width": W, "height": H})
            print("wrote", dest)
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render an FNN data-story slide.")
    ap.add_argument("story", help="stories/gwN-name.json")
    ap.add_argument("--out", help="output folder (default out/gwN)")
    args = ap.parse_args()
    render(args.story, args.out)
