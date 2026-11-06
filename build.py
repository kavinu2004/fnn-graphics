"""Build the Farmers League / FNN carousel for one gameweek.

    python build.py new 10                      # start gameweeks/gw10.json from gw9's table
    python build.py gameweeks/gw10.json         # render every slide to out/gw10/
    python build.py gameweeks/gw10.json --out ~/Desktop/FNN --only Standings Waivers

Each slide is an HTML page over assets/template.jpg, screenshotted by headless Chromium
at 1080x1350, deviceScaleFactor 1, one clip per slide. No image generation, no cropping.
"""
import argparse
import functools
import html
import json
import re
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W, H = 1080, 1350

HEAD = '<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/styles/base.css"></head><body><div class="slide">'
TAIL = '</div></body></html>'
UP = '<svg viewBox="0 0 12 12"><path d="M2.5 7.5 6 4l3.5 3.5"/></svg>'
DOWN = '<svg viewBox="0 0 12 12"><path d="M2.5 4.5 6 8l3.5-3.5"/></svg>'


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


# slides: each returns (output name, inner html). Copy fields are trusted HTML (<b> player, <em> lime number).

def team_cover(gw):
    return "00-Team-News", f'''<div class="cover tcover">
<div class="ln gw lime">Gameweek {gw}</div>
<div class="ln fnn">FNN</div>
<div class="bar"></div>
<div class="ln net">(FARMERS NEWS NETWORK)</div>
<div class="ln tn">TEAM NEWS</div></div>'''


def series_cover(gw):
    return "FNN", f'''<div class="cover scover">
<div class="ln gw">Gameweek {gw}</div>
<div class="ln fnn">FNN</div>
<div class="bar"></div>
<div class="ln net">FARMERS NEWS NETWORK</div></div>'''


def card(gw, rank, row):
    white, lime = row["headline"]
    body = "".join(f"<p>{p}</p>" for p in row["body"])
    return f"{rank:02d}-{slug(row['team'])}", f'''<div class="sheet card">
<div class="team">{html.escape(row["team"])}</div>
<div class="mgr">{html.escape(row["manager"])}</div>
<div class="meta">Overall: <b>{ordinal(rank)}</b><i>|</i>Total: <b>{row["total"]}</b><i>|</i>GW{gw}: <b>{row["points"]}</b></div>
<div class="rule"></div>
<div class="hl"><div>{white}</div><div class="lime">{lime}</div></div>
<div class="body">{body}</div></div>'''


def movement(rank, was):
    if rank < was:
        return f'<div class="mv up">{UP}{was - rank}</div>'
    if rank > was:
        return f'<div class="mv down">{DOWN}{rank - was}</div>'
    return '<div class="mv same"></div>'


def standings(table):
    rows = "".join(
        f'<div class="row"><div class="rk">{r}</div>{movement(r, row["prev_rank"])}'
        f'<div class="tm">{html.escape(row["team"])}</div><div class="mg">{html.escape(row["manager"])}</div>'
        f'<div class="pt">{row["total"]}</div></div>'
        for r, row in enumerate(table, 1)
    )
    return "Standings", f'''<div class="sheet glass tbl">
<div class="hd"><span style="left:0">#</span><span style="left:112px">TEAM</span><span style="right:0">PTS</span></div>
{rows}</div>'''


def star(gw, s, team):
    return s["file"], f'''<div class="sheet star">
<img src="/assets/photos/{s["photo"]}" style="object-position:{s.get("focus", "50% 30%")}"><div class="shade"></div>
<div class="kick">GW{gw} STAR</div>
<div class="info"><div class="nm">{html.escape(s["name"])}</div><div class="pts">{s["points"]}<span>PTS</span></div>
<div class="det">{html.escape(s["detail"])}</div><div class="fx">{html.escape(s["fixture"])}</div>
<div class="by"><i>DRAFTED BY</i><b>{html.escape(s["manager"])}</b> · {html.escape(team)}</div></div></div>'''


def waivers(gw, groups, teams):
    blocks = ""
    for g in groups:
        moves = "".join(
            f'<div class="mv"><span class="n">{html.escape(m[0])}</span>{"<span class=fa>FA</span>" if "FA" in m[2:] else ""}'
            f'<span class="ar">→</span><span class="o">{html.escape(m[1])}</span></div>'
            for m in g["moves"]
        )
        blocks += f'<div class="blk"><div class="who">{html.escape(g["manager"])}</div><div class="tmn">{html.escape(teams[g["manager"]])}</div>{moves}</div>'
    return "Waivers", f'''<div class="sheet glass wv">
<div class="top"><div class="t">WAIVERS</div><div class="g">GW{gw}</div></div>
<div class="cols"><span style="left:0"><b class="lime">IN</b> <b class="lime">→</b> <b style="color:#9a9ea5">OUT</b></span><span style="right:0;color:#9a9ea5"><b class="lime">FA</b> = FREE AGENT</span></div>
<div class="grid">{blocks}</div></div>'''


def check(data):
    """Catch the mistakes that would put a wrong number on a slide."""
    errors = []
    table = data["table"]
    teams = {row["manager"]: row["team"] for row in table}
    for i, row in enumerate(table, 1):
        for key in ("total", "points", "prev_rank"):
            if not isinstance(row.get(key), int):
                errors.append(f"{row['team']}: {key} is missing")
        if not all(row.get("headline", [])) or len(row.get("headline", [])) != 2 or not all(row.get("body", [])):
            errors.append(f"{row['team']}: card copy is empty")
    totals = [row["total"] for row in table if isinstance(row.get("total"), int)]
    if totals != sorted(totals, reverse=True):
        errors.append("table is not in rank order (sort by total, highest first)")
    prev = sorted(row.get("prev_rank") for row in table if isinstance(row.get("prev_rank"), int))
    if prev != list(range(1, len(table) + 1)):
        errors.append(f"prev_rank should be 1..{len(table)} once each, got {prev}")
    for s in data.get("stars", []):
        if s["manager"] not in teams:
            errors.append(f"star {s['name']}: unknown manager {s['manager']}")
        if not (ROOT / "assets/photos" / s["photo"]).exists():
            errors.append(f"star {s['name']}: assets/photos/{s['photo']} not found")
    for g in data.get("waivers", []):
        if g["manager"] not in teams:
            errors.append(f"waivers: unknown manager {g['manager']}")
    if errors:
        sys.exit("gameweek data has problems:\n  " + "\n  ".join(errors))
    return teams


def slides(data):
    gw, table = data["gw"], data["table"]
    teams = check(data)
    yield series_cover(gw)
    yield standings(table)
    for s in data.get("stars", []):
        yield star(gw, s, teams[s["manager"]])
    if data.get("waivers"):
        yield waivers(gw, data["waivers"], teams)
    yield team_cover(gw)
    for rank, row in enumerate(table, 1):
        yield card(gw, rank, row)


def serve():
    handler = functools.partial(type("Quiet", (SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def build(path, out, only):
    data = json.loads(Path(path).read_text())
    gw = data["gw"]
    pages = ROOT / "build" / f"gw{gw}"
    pages.mkdir(parents=True, exist_ok=True)
    out = Path(out or ROOT / "out" / f"gw{gw}").expanduser()
    out.mkdir(parents=True, exist_ok=True)

    names = []
    for name, inner in slides(data):
        if only and not any(o.lower() in name.lower() for o in only):
            continue
        (pages / f"{name}.html").write_text(HEAD + inner + TAIL)
        names.append(name)
    if not names:
        sys.exit(f"--only {' '.join(only)} matched no slides")

    from playwright.sync_api import sync_playwright

    server = serve()
    base = f"http://127.0.0.1:{server.server_port}/build/gw{gw}"
    try:
        with sync_playwright() as p:
            # P3 profile so the lime matches the GW6-GW9 PNGs (222,254,107)
            browser = p.chromium.launch(args=["--force-color-profile=display-p3-d65"])
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            for name in names:
                page.goto(f"{base}/{name}.html", wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(250)
                dest = out / f"Farmers-League-GW{gw}-{name}.png"
                page.screenshot(path=dest, clip={"x": 0, "y": 0, "width": W, "height": H})
                print("wrote", dest)
            browser.close()
    finally:
        server.shutdown()


def new(gw):
    prev = ROOT / "gameweeks" / f"gw{gw - 1}.json"
    dest = ROOT / "gameweeks" / f"gw{gw}.json"
    if dest.exists():
        sys.exit(f"{dest.relative_to(ROOT)} already exists")
    last = json.loads(prev.read_text())
    table = [
        {"team": row["team"], "manager": row["manager"], "total": None, "points": None, "prev_rank": rank,
         "headline": ["", ""], "body": ["", ""]}
        for rank, row in enumerate(last["table"], 1)
    ]
    dest.write_text(json.dumps({"gw": gw, "table": table, "stars": [], "waivers": []}, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {dest.relative_to(ROOT)}: prev_rank is the GW{gw - 1} order; reorder rows by the new table and fill in the rest")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "new":
        new(int(sys.argv[2]))
        sys.exit()
    ap = argparse.ArgumentParser(description="Render a gameweek's FNN slides.")
    ap.add_argument("gameweek", help="gameweeks/gwN.json")
    ap.add_argument("--out", help="output folder (default out/gwN)")
    ap.add_argument("--only", nargs="+", default=[], help="render only slides whose name contains one of these")
    args = ap.parse_args()
    build(args.gameweek, args.out, args.only)
