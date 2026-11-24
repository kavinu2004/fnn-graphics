"""Render a gameweek's carousel in the FNN chrome style (the story-slide brief, every slide).

    python chrome.py gameweeks/gw11.json                       # writes out/gw11-chrome/
    python chrome.py gameweeks/gw11.json --out ~/Desktop/FNN/GW11-chrome --only 01 Star

Reads the same gwN.json as build.py, plus its "chrome" section (photos, short chrome
headlines, star point breakdowns, trades). Exports at 2x (2160x2700), sRGB.
Every number in a headline, deck, kicker or footnote is a {placeholder} filled from the data.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

import story
from build import ROOT, W, H, ordinal, serve, slug

HEAD = story.HEAD.replace('</head>', '<link rel="stylesheet" href="/styles/chrome.css"></head>')
UP, DOWN = "▲", "▼"


def esc(s):
    return html.escape(str(s))


def fmt(text, ctx):
    return text.format(**ctx)


def words(text):
    return len(re.sub(r"<[^>]+>", " ", text).split())


class Checker:
    """Word budgets and the no-typed-numbers rule, collected across the whole carousel."""

    def __init__(self):
        self.errors = []

    def copy(self, where, template, ctx, limit):
        if template is None:
            return ""
        raw = template if isinstance(template, str) else " ".join(t for t, tone in template if tone != "br")
        if re.search(r"\d", raw):
            self.errors.append(f"{where}: number typed into the copy ({raw!r}); use a {{placeholder}}")
        text = fmt(raw, ctx)
        if words(text) > limit:
            self.errors.append(f"{where}: {words(text)} words, budget is {limit}: {text}")
        return text


def photo(spec):
    """spec: {"photo": file, "place": {"width", "left", "top"}} -> the photo layer."""
    if not spec or not spec.get("photo"):
        return '<div class="atmos"></div>'
    p = spec.get("place") or {"width": W, "left": 0, "top": 0}
    return (f'<img class="photo placed" src="/assets/photos/{esc(spec["photo"])}" '
            f'style="width:{p["width"]}px;height:auto;left:{p["left"]}px;top:{p["top"]}px">')


def headline(segments, ctx, size, width):
    spans = " ".join("<br>" if tone == "br" else f'<span class="chrome {tone}">{esc(w)}</span>'
                     for t, tone in segments for w in (fmt(t, ctx).split() or [""]))
    return f'<h1 style="font-size:{size}px;max-width:{width}px">{spans}</h1>'


def shell(n, total, gw, *, photo_html, kicker, head, deck="", content="", foot=""):
    label, span = kicker
    deck_html = f'<p class="deck">{deck}</p>' if deck else ""
    foot_html = f'<div class="foot">{esc(foot)}</div>' if foot else ""
    return f'''{photo_html}<div class="grain"></div><div class="rim"></div><div class="lfade"></div><div class="vfade"></div><div class="frame"></div>
<div class="mast"><div class="plate"></div>{story.CREST}<div class="fl">FARMERS LEAGUE</div><div class="fnn">FNN</div><div class="chip">GW{gw}</div></div>
<div class="kick"><i></i><b>{esc(label)}</b><span>{esc(span)}</span></div>
<div class="lede">{head}{deck_html}</div>
{content}{foot_html}
<div class="brand">FARMERS NEWS NETWORK · EST 2019</div>
<div class="tab"><span>{n} / {total}</span></div>'''


def bars(rows, *, label_w=330, bar_max=520, top=50, row_h=54, ref=None):
    """rows: [(label_html, value, tone or None, note)] -> flat horizontal bars, values at the bar ends."""
    vmax = max(v for _, v, _, _ in rows) or 1
    x = lambda v: label_w + v / vmax * bar_max
    out = []
    if ref:
        value, text = ref
        out.append(f'<div class="ref" style="left:{x(value):.1f}px;top:{top - 6}px;height:{len(rows) * row_h}px"></div>'
                   f'<div class="reflbl" style="left:{x(value):.1f}px">{esc(text)}</div>')
    for i, (label, v, tone, note) in enumerate(rows):
        note_html = f'<span class="note">{esc(note)}</span>' if note else ""
        out.append(f'<div class="row{" on " + tone if tone else ""}" style="top:{top + i * row_h}px;height:{row_h}px">'
                   f'<div class="nm" style="width:{label_w - 10}px;line-height:{row_h}px">{label}</div>'
                   f'<div class="bar" style="left:{label_w}px;width:{v / vmax * bar_max:.1f}px;top:{(row_h - 32) / 2}px">{note_html}</div>'
                   f'<div class="val" style="left:{x(v) + 14:.1f}px;line-height:{row_h}px">{v}</div></div>')
    return f'<div class="chart">{"".join(out)}</div>'


def team_ctx(table, prev_points):
    """Per-team numbers the chrome headlines can use."""
    ctxs = {}
    for i, row in enumerate(table):
        rank = i + 1
        c = {"rank": rank, "ordinal": ordinal(rank).upper(), "total": row["total"], "points": row["points"],
             "prev_rank": row["prev_rank"], "prev_points": prev_points.get(row["team"]),
             "team": row["team"], "manager": row["manager"],
             "gap_top": table[0]["total"] - row["total"],
             "gap_above": table[i - 1]["total"] - row["total"] if i else 0,
             "gap_below": row["total"] - table[i + 1]["total"] if i + 1 < len(table) else 0}
        if rank == 1:
            c["lead"] = row["total"] - table[1]["total"]
        ctxs[row["team"]] = c
    return ctxs


def move(rank, was):
    if rank < was:
        return f'<b class="up">{UP}{was - rank}</b>'
    if rank > was:
        return f'<b class="down">{DOWN}{rank - was}</b>'
    return '<b class="same">–</b>'


# ---- slides -------------------------------------------------------------------------------

def cover(c, ctx, chk, contents):
    rows = "".join(f'<div class="item"><b>{n:02d}</b><span>{esc(t)}</span></div>' for n, t in contents)
    return dict(photo_html=photo(c), kicker=(c.get("kicker", "IN THIS ISSUE"), f"GW{ctx['gw']}"),
                head=headline(c["headline"], ctx, c.get("size", 176), c.get("width", 640)),
                deck=esc(chk.copy("cover deck", c.get("deck"), ctx, 14)),
                content=f'<div class="contents">{rows}</div>',
                foot="")


def standings(c, ctx, chk, table, tctx):
    hl = c.get("highlight", table[0]["team"])
    rows = []
    for i, row in enumerate(table):
        on = row["team"] == hl
        rows.append(f'<div class="trow{" on" if on else ""}" style="top:{44 + i * 54}px">'
                    f'<span class="rk">{i + 1}</span><span class="mv">{move(i + 1, row["prev_rank"])}</span>'
                    f'<span class="tm">{esc(row["team"])}</span><span class="gw">{row["points"]}</span>'
                    f'<span class="pt">{row["total"]}</span></div>')
    hdr = (f'<div class="thead"><span class="tm">TEAM</span><span class="gw">GW{ctx["gw"]}</span>'
           f'<span class="pt">PTS</span></div>')
    hc = {**ctx, **tctx[hl]}
    chk.copy("standings headline", c["headline"], hc, 5)
    return dict(photo_html=photo(c), kicker=("THE TABLE", f"GW{ctx['gw']}"),
                head=headline(c["headline"], hc, c.get("size", 150), c.get("width", 620)),
                deck=esc(chk.copy("standings deck", c.get("deck"), hc, 14)),
                content=f'<div class="chart table">{hdr}{"".join(rows)}</div>',
                foot=chk.copy("standings footnote", c.get("footnote"), hc, 12))


def star(c, s, i, n_stars, ctx, chk, team):
    parts = c["breakdown"]
    if sum(p for _, _, p in parts) != s["points"]:
        sys.exit(f"star {s['name']}: breakdown adds to {sum(p for _, _, p in parts)}, not {s['points']}")
    top = max(p for _, _, p in parts)
    rows = [(f'{esc(label)} <i>{esc(stat)}</i>', p, "gold" if p == top else None, None) for label, stat, p in parts]
    sc = {**ctx, "short": c["short"], "name": s["name"], "points": s["points"], "fixture": s["fixture"],
          "manager": s["manager"].replace(" ", "\u00a0"), "team": team, "i": i, "n": n_stars}
    chk.copy(f"star {s['name']} headline", [["{short} {points}.", ""]], sc, 5)
    return dict(photo_html=photo({"photo": s["photo"], "place": c["place"]}),
                kicker=("GW{gw} STAR".format(**sc), f"{i} OF {n_stars}"),
                head=headline([["{short}", "silver"], ["{points}.", "gold"]], sc, c.get("size", 150), c.get("width", 760)),
                deck=esc(chk.copy(f"star {s['name']} deck", "{fixture}. Drafted by {manager}.", sc, 14)),
                content=bars(rows, label_w=380, bar_max=460),
                foot=chk.copy(f"star {s['name']} footnote", c.get("footnote", "Points by category, from the PL app."), sc, 12))


def waivers(c, ctx, chk, groups, trades, first):
    moves = [(first[g["manager"]], m) for g in groups for m in g["moves"]]
    wc = {**ctx, "claims": len(moves), "trades": len(trades), "trade_word": "TRADE." if len(trades) == 1 else "TRADES."}
    rows, y = [], 44
    for who, m in moves:
        fa = '<em>FA</em>' if "FA" in m[2:] else ""
        rows.append(f'<div class="wrow" style="top:{y}px"><span class="who">{esc(who)}</span>'
                    f'<span class="in">{esc(m[0])}{fa}</span><span class="ar">→</span><span class="out">{esc(m[1])}</span></div>')
        y += 54
    for t in trades:
        y += 14
        rows.append(f'<div class="wsub" style="top:{y}px">TRADE</div>')
        y += 46
        for a, gets, gives in ((t["a"], t["a_gets"], t["b_gets"]), (t["b"], t["b_gets"], t["a_gets"])):
            rows.append(f'<div class="wrow" style="top:{y}px"><span class="who">{esc(first[a])}</span>'
                        f'<span class="in">{esc(", ".join(gets))}</span><span class="ar">→</span>'
                        f'<span class="out">{esc(", ".join(gives))}</span></div>')
            y += 54
    hdr = '<div class="thead"><span class="who">MANAGER</span><span class="in">IN</span><span class="out">OUT</span></div>'
    return dict(photo_html=photo(c), kicker=("WAIVERS", f"GW{ctx['gw']}"),
                head=headline(c["headline"], wc, c.get("size", 150), c.get("width", 620)),
                deck=esc(chk.copy("waivers deck", c.get("deck"), wc, 14)),
                content=f'<div class="chart wv">{hdr}{"".join(rows)}</div>',
                foot=chk.copy("waivers footnote", c.get("footnote"), wc, 12)), wc


def team_news(c, ctx, chk, table):
    order = sorted(table, key=lambda r: -r["points"])
    scores = [r["points"] for r in order]
    top3, bot3 = scores[2], scores[-3]
    if scores[3] == top3 or scores[-4] == bot3:
        sys.exit("team news chart: a tie crosses the top-three or bottom-three line; pick colours by hand")
    rows = [(esc(r["team"]), r["points"], "lime" if r["points"] >= top3 else "red" if r["points"] <= bot3 else None, None)
            for r in order]
    return dict(photo_html=photo(c), kicker=("TEAM NEWS", f"GW{ctx['gw']}"),
                head=headline(c["headline"], ctx, c.get("size", 176), c.get("width", 640)),
                deck=esc(chk.copy("team news deck", c.get("deck"), ctx, 14)),
                content=bars(rows),
                foot=chk.copy("team news footnote", c.get("footnote"), ctx, 12))


def card(c, row, rank, ctx, chk, tctx):
    cc = {**ctx, **tctx[row["team"]], **c.get("facts", {})}
    chk.copy(f"{row['team']} headline", c["headline"], cc, 5)
    tiles = (f'<div class="tile"><i>OVERALL</i><b>{cc["ordinal"]}</b>{move(rank, row["prev_rank"])}</div>'
             f'<div class="tile"><i>TOTAL</i><b>{row["total"]}</b></div>'
             f'<div class="tile hl"><i>GW{ctx["gw"]}</i><b>{row["points"]}</b></div>')
    body = "".join(f"<p>{p}</p>" for p in row["body"])
    return dict(photo_html=photo(c), kicker=(cc["ordinal"], row["team"]),
                head=headline(c["headline"], cc, c.get("size", 150), c.get("width", 620)),
                deck=esc(row["manager"]),
                content=f'<div class="tiles">{tiles}</div><div class="cbody">{body}</div>')


def slides(data):
    gw, table, ch = data["gw"], data["table"], data["chrome"]
    ctx = {"gw": gw}
    teams = {r["manager"]: r["team"] for r in table}
    first = {r["manager"]: r["manager"].split()[0] for r in table}
    prev_file = ROOT / "gameweeks" / f"gw{gw - 1}.json"
    prev_points = {r["team"]: r["points"] for r in json.loads(prev_file.read_text())["table"]} if prev_file.exists() else {}
    tctx = team_ctx(table, prev_points)
    chk = Checker()

    plan = [("Cover", None), ("Table", None)]
    plan += [(f"Star-{s['file']}", s) for s in data["stars"]]
    if ch.get("bench"):
        plan.append(("Bench", None))
    plan += [("Waivers", None), ("Team-News", None)]
    plan += [(f"{i:02d}-{slug(r['team'])}", r) for i, r in enumerate(table, 1)]
    total = len(plan)
    num = {name: i for i, (name, _) in enumerate(plan, 1)}
    contents = [(num["Table"], "The table"), (num[f"Star-{data['stars'][0]['file']}"], "Stars of the week")]
    if ch.get("bench"):
        contents.append((num["Bench"], "Bench watch"))
    contents += [(num["Waivers"], "Waivers"), (num["Team-News"], "Team news")]

    out = []
    for n, (name, item) in enumerate(plan, 1):
        if name == "Cover":
            chk.copy("cover headline", ch["cover"]["headline"], ctx, 5)
            parts = cover(ch["cover"], ctx, chk, contents)
        elif name == "Table":
            parts = standings(ch["standings"], ctx, chk, table, tctx)
        elif name.startswith("Star-"):
            i = data["stars"].index(item) + 1
            parts = star(ch["stars"][item["file"]], item, i, len(data["stars"]), ctx, chk, teams[item["manager"]])
        elif name == "Bench":
            sd = json.loads((ROOT / ch["bench"]).read_text())
            sd["slide"] = [n, total]
            out.append((name, story.slide(sd)))
            continue
        elif name == "Waivers":
            parts, _ = waivers(ch["waivers"], ctx, chk, data["waivers"], ch.get("trades", []), first)
        elif name == "Team-News":
            chk.copy("team news headline", ch["team_news"]["headline"], ctx, 5)
            parts = team_news(ch["team_news"], ctx, chk, table)
        else:
            rank = table.index(item) + 1
            parts = card(ch["cards"][item["team"]], item, rank, ctx, chk, tctx)
        out.append((name, shell(n, total, gw, **parts)))
    if chk.errors:
        sys.exit("chrome copy has problems:\n  " + "\n  ".join(chk.errors))
    return out


def render(path, out, only):
    data = json.loads(Path(path).read_text())
    gw = data["gw"]
    pages = ROOT / "build" / f"gw{gw}-chrome"
    pages.mkdir(parents=True, exist_ok=True)
    out = Path(out or ROOT / "out" / f"gw{gw}-chrome").expanduser()
    out.mkdir(parents=True, exist_ok=True)
    names = []
    for i, (name, inner) in enumerate(slides(data), 1):
        full = f"{i:02d}-{name}" if not name[:2].isdigit() else f"{i:02d}-Card-{name[3:]}"
        if only and not any(o.lower() in full.lower() for o in only):
            continue
        (pages / f"{full}.html").write_text(HEAD + inner + story.TAIL)
        names.append(full)

    from playwright.sync_api import sync_playwright

    server = serve()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            for full in names:
                page.goto(f"http://127.0.0.1:{server.server_port}/build/gw{gw}-chrome/{full}.html", wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(250)
                dest = out / f"FNN-GW{gw}-{full}.png"
                page.screenshot(path=dest, clip={"x": 0, "y": 0, "width": W, "height": H})
                print("wrote", dest)
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render a gameweek's carousel in the FNN chrome style.")
    ap.add_argument("gameweek", help="gameweeks/gwN.json (with a chrome section)")
    ap.add_argument("--out", help="output folder (default out/gwN-chrome)")
    ap.add_argument("--only", nargs="+", default=[], help="render only slides whose name contains one of these")
    args = ap.parse_args()
    render(args.gameweek, args.out, args.only)
