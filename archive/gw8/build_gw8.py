#!/usr/bin/env python3
"""GW8 Farmers News Network slides, on the existing Weekly News frame."""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pillow_heif

pillow_heif.register_heif_opener()

OUT = "/Users/kavi/Desktop/FNN"
LEAGUE = "/Users/kavi/Desktop/GW8 League News"
W, H = 1080, 1350
LIME = (222, 254, 107)
WHITE = (255, 255, 255)
MUTED = (168, 174, 168)
INK = (8, 10, 14)
CARD = (52, 286, 1028, 1224)

IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
DIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
GILL = "/System/Library/Fonts/Supplemental/GillSans.ttc"


def font(path, size, index=0):
    if path.endswith(".ttc"):
        return ImageFont.truetype(path, size, index=index)
    return ImageFont.truetype(path, size)


def impact(size):
    return font(IMPACT, size)


def din(size):
    return font(DIN, size)


def av(size, index=2):
    return font(AVENIR, size, index=index)


def futura(size, medium=False):
    return font(FUTURA, size, index=0 if medium else 2)


def gill(size, index=0):
    return font(GILL, size, index=index)


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def center(draw, text, y, fnt, fill, x0=0, x1=W):
    tw = text_w(draw, text, fnt)
    draw.text(((x0 + x1 - tw) / 2, y), text, font=fnt, fill=fill)


def rounded_card(base, box=CARD, radius=34, fill=(6, 8, 10, 255), outline=(255, 255, 255, 80)):
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def plate_from(path):
    return Image.open(path).convert("RGB")


def erase_box(im, box, color=(8, 10, 15)):
    d = ImageDraw.Draw(im)
    d.rectangle(box, fill=color)
    return im


def swap_digit(src, dest, box, color):
    im = plate_from(src)
    erase_box(im, box)
    d = ImageDraw.Draw(im)
    fnt = impact(50)
    label = "8"
    tw = text_w(d, label, fnt)
    th = 50
    x = box[0] + (box[2] - box[0] - tw) / 2
    y = box[1] + (box[3] - box[1] - th) / 2 - 4
    d.text((x, y), label, font=fnt, fill=color)
    im.save(dest, quality=95)
    print("cover", dest)


def new_card(src):
    return rounded_card(plate_from(src))


def wrap_words(draw, words, fnt, max_w):
    """words: list of (text, fill). Returns list of lines, each a list of (text, fill)."""
    lines, cur, width = [], [], 0
    space = text_w(draw, " ", fnt)
    for word, fill in words:
        ww = text_w(draw, word, fnt)
        extra = space if cur else 0
        if cur and width + extra + ww > max_w:
            lines.append(cur)
            cur = [(word, fill)]
            width = ww
        else:
            if cur:
                width += extra
            cur.append((word, fill))
            width += ww
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, leading):
    space = text_w(draw, " ", fnt)
    for line in lines:
        cx = x
        for i, (word, fill) in enumerate(line):
            if i:
                cx += space
            draw.text((cx, y), word, font=fnt, fill=fill)
            cx += text_w(draw, word, fnt)
        y += leading
    return y


def words_from(parts):
    """parts: list of (string, fill). Punctuation stays on the word before it."""
    out = []
    for text, fill in parts:
        for word in text.split():
            if out and word[:1] in ",.;:!?":
                prev, prev_fill = out[-1]
                out[-1] = (prev + word[0], prev_fill)
                rest = word[1:]
                if rest:
                    out.append((rest, fill))
            else:
                out.append((word, fill))
    return out


def body(draw, parts, x, y, max_w, size=27, leading=36, index=2):
    fnt = av(size, index=index)
    lines = wrap_words(draw, words_from(parts), fnt, max_w)
    return draw_lines(draw, lines, x, y, fnt, leading)


def fit_font(draw, text, start, left, right, floor=28):
    size = start
    while size > floor and text_w(draw, text, futura(size)) > (right - left):
        size -= 2
    return futura(size)


def plain_lines(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(draw, trial, fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def team_slide(src, dest, team, first, meta, copy):
    im = new_card(src)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = CARD
    pad = 48
    left, right = x0 + pad, x1 - pad
    width = right - left
    y = y0 + 34
    name = team.upper()
    center(d, name, y, fit_font(d, name, 46, left, right), WHITE, left, right)
    y += 58
    center(d, first, y, futura(24, medium=True), LIME, left, right)
    y += 36
    center(d, meta, y, gill(22), WHITE, left, right)
    y += 36
    d.line((left, y, right, y), fill=LIME, width=3)
    y += 28
    # Demi, not Heavy. Gill Sans drops č and ğ (Horníček, Boscağli).
    fnt = av(30, index=2)
    for line in plain_lines(d, copy, fnt, width):
        d.text((left, y), line, font=fnt, fill=WHITE)
        y += 42
    if y > y1 - 24:
        print("OVERFLOW", dest, y, y1)
    im.save(dest, quality=95)
    print("team", dest, "bottom", y)


def standings(src, dest, rows):
    im = new_card(src)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = CARD
    left, right = x0 + 40, x1 - 40
    y = y0 + 28
    d.text((left, y), "#", font=din(26), fill=MUTED)
    d.text((left + 70, y), "TEAM", font=din(26), fill=MUTED)
    pts_x = right - 150
    avg_x = right - 10
    d.text((pts_x, y), "PTS", font=din(26), fill=MUTED)
    tw = text_w(d, "AVG", din(26))
    d.text((avg_x - tw, y), "AVG", font=din(26), fill=LIME)
    y += 42
    d.line((left, y, right, y), fill=(255, 255, 255, 40), width=1)
    row_h = 78
    for rank, team, manager, pts, avg in rows:
        y += 14
        d.text((left, y + 10), str(rank), font=din(40), fill=LIME)
        d.text((left + 70, y + 4), team, font=futura(26), fill=WHITE)
        d.text((left + 70, y + 36), manager, font=futura(16, medium=True), fill=MUTED)
        pts_s = str(pts)
        d.text((pts_x, y + 8), pts_s, font=din(40), fill=WHITE)
        avg_s = avg
        tw = text_w(d, avg_s, din(34))
        d.text((avg_x - tw, y + 12), avg_s, font=din(34), fill=LIME)
        y += row_h - 14
        d.line((left, y, right, y), fill=(255, 255, 255, 28), width=1)
    im.save(dest, quality=95)
    print("table", dest)


def waivers(src, dest, groups):
    im = new_card(src)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = CARD
    left, right = x0 + 36, x1 - 36
    y = y0 + 22
    d.text((left, y), "WAIVERS", font=futura(32), fill=WHITE)
    gw = "GW8"
    d.text((right - text_w(d, gw, din(28)), y + 6), gw, font=din(28), fill=LIME)
    y += 44
    mid = (left + right) // 2
    col_in = left
    col_out = mid + 56
    d.text((col_in, y), "IN", font=din(20), fill=LIME)
    d.text((col_out, y), "OUT", font=din(20), fill=MUTED)
    y += 24
    name_f = futura(22)
    sub_f = din(18)
    team_f = futura(18)
    first_f = futura(15, medium=True)
    for team, first, moves in groups:
        d.text((left, y), team, font=team_f, fill=WHITE)
        d.text((left + text_w(d, team + "  ", team_f), y + 2), first, font=first_f, fill=MUTED)
        y += 24
        for inn, inn_meta, out, out_meta in moves:
            d.text((col_in, y), inn, font=name_f, fill=WHITE)
            d.text((col_out, y), out, font=name_f, fill=WHITE)
            ax = mid - 6
            d.line((ax - 22, y + 12, ax + 14, y + 12), fill=MUTED, width=2)
            d.polygon([(ax + 14, y + 6), (ax + 26, y + 12), (ax + 14, y + 18)], fill=MUTED)
            y += 26
            d.text((col_in, y), inn_meta, font=sub_f, fill=LIME)
            d.text((col_out, y), out_meta, font=sub_f, fill=MUTED)
            y += 28
        y += 8
    if y > y1 - 20:
        print("WAIVER OVERFLOW", y, y1)
    im.save(dest, quality=95)
    print("waivers", dest, "bottom", y)


def cover_crop(im, tw, th, fx, fy):
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, min(nw - tw, int((nw - tw) * fx)))
    top = max(0, min(nh - th, int((nh - th) * fy)))
    return im.crop((left, top, left + tw, top + th))


def star(src, dest, photo, fx, fy, kicker, name, points, detail, fixture, drafted):
    base = plate_from(src).convert("RGBA")
    x0, y0, x1, y1 = CARD
    # inset the photo slightly inside the frame line
    px0, py0, px1, py1 = x0 + 10, y0 + 10, x1 - 10, y1 - 10
    tw, th = px1 - px0, py1 - py0
    shot = cover_crop(Image.open(photo).convert("RGB"), tw, th, fx, fy).convert("RGBA")
    # bottom gradient so the type sits on the picture
    grad = Image.new("L", (tw, th), 0)
    gd = ImageDraw.Draw(grad)
    start = int(th * 0.40)
    for i, yy in enumerate(range(start, th)):
        a = int(235 * ((i / max(1, th - start)) ** 1.15))
        gd.line((0, yy, tw, yy), fill=a)
    for i, yy in enumerate(range(0, 110)):
        a = int(110 * (1 - i / 110))
        gd.line((0, yy, tw, yy), fill=a)
    black = Image.new("RGBA", (tw, th), (0, 0, 0, 255))
    shot = Image.composite(black, shot, grad)
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, tw - 1, th - 1), radius=28, fill=255)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(shot, (px0, py0), mask)
    frame = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(CARD, radius=34, outline=(255, 255, 255, 150), width=2)
    im = Image.alpha_composite(base, layer)
    im = Image.alpha_composite(im, frame).convert("RGB")
    d = ImageDraw.Draw(im)
    d.text((px0 + 28, py0 + 22), kicker, font=din(26), fill=LIME)
    y = py1 - 250
    d.text((px0 + 32, y), name, font=futura(48), fill=WHITE)
    y += 58
    d.text((px0 + 32, y), str(points), font=futura(68), fill=LIME)
    pw = text_w(d, str(points), futura(68))
    d.text((px0 + 42 + pw, y + 32), "PTS", font=din(26), fill=WHITE)
    y += 80
    d.text((px0 + 32, y), detail, font=gill(22), fill=WHITE)
    y += 30
    d.text((px0 + 32, y), fixture, font=gill(22), fill=WHITE)
    y += 34
    label = "DRAFTED BY"
    d.text((px0 + 32, y), label, font=din(20), fill=LIME)
    d.text((px0 + 40 + text_w(d, label, din(20)), y - 1), drafted, font=futura(20), fill=WHITE)
    im.save(dest, quality=95)
    print("star", dest)


def load_blurbs(path):
    import subprocess
    import re
    raw = subprocess.check_output(
        ["textutil", "-convert", "txt", "-stdout", path],
        text=True,
    )
    chunks = re.split(r"\n(?=\d+\.\s)", raw.strip())
    blurbs = []
    for chunk in chunks:
        lines = [line.strip() for line in chunk.strip().splitlines() if line.strip()]
        head, *rest = lines
        title = re.sub(r"^\d+\.\s*", "", head)
        team, person = [part.strip() for part in title.split("—", 1)]
        person = person.split("(")[0].strip()
        first = person.split()[0]
        blurbs.append((team, first, " ".join(rest)))
    return blurbs


def main():
    league_cover = f"{OUT}/Farmers-League-GW8-FNN.png"
    team_cover = f"{OUT}/Farmers-League-GW8-00-Team-News.png"
    # Digit sits just after GAMEWEEK. Boxes measured off the posted covers.
    swap_digit(
        f"{OUT}/Farmers-League-GW6-FNN.png",
        league_cover,
        (694, 548, 730, 608),
        WHITE,
    )
    swap_digit(
        f"{OUT}/Farmers-League-GW7-00-Team-News.png",
        team_cover,
        (696, 500, 732, 558),
        LIME,
    )
    plate = league_cover

    blurbs = load_blurbs("/Users/kavi/Desktop/GW8 Team News/Team News Descriptions.rtf")
    slugs = [
        "01-Heung-Min-Dad",
        "02-Wirtz-Case-Scenario",
        "03-Los-Porros-Hermanos",
        "04-Chennaiyin-FC",
        "05-Asspine-fc",
        "06-Arsene-Fection",
        "07-Split-the-G-FC",
        "08-Pakason-FC",
        "09-Assnal-Dulaj",
        "10-Saddam-Huijsen",
    ]
    metas = [
        "Overall: 1st    |    Total: 426    |    GW8: 38",
        "Overall: 2nd    |    Total: 365    |    GW8: 44",
        "Overall: 3rd    |    Total: 351    |    GW8: 46",
        "Overall: 4th    |    Total: 335    |    GW8: 62",
        "Overall: 5th    |    Total: 325    |    GW8: 35",
        "Overall: 6th    |    Total: 322    |    GW8: 24",
        "Overall: 7th    |    Total: 319    |    GW8: 38",
        "Overall: 8th    |    Total: 317    |    GW8: 50",
        "Overall: 9th    |    Total: 302    |    GW8: 43",
        "Overall: 10th    |    Total: 301    |    GW8: 48",
    ]
    names = {
        "Saddam Hujisen": "Saddam Huijsen",
    }
    for slug, meta, (team, first, copy) in zip(slugs, metas, blurbs):
        team_slide(
            plate,
            f"{OUT}/Farmers-League-GW8-{slug}.png",
            names.get(team, team),
            first,
            meta,
            copy,
        )

    standings(
        plate,
        f"{OUT}/Farmers-League-GW8-Standings.png",
        [
            (1, "Heung Min Dad", "Imad", 426, "53.3"),
            (2, "Wirtz Case Scenario", "Umar", 365, "45.6"),
            (3, "Los Porros Hermanos", "Rihab", 351, "43.9"),
            (4, "Chennaiyin FC", "Vidhun", 335, "41.9"),
            (5, "Asspine FC", "Munir", 325, "40.6"),
            (6, "Arsene Fection", "Dulaj", 322, "40.3"),
            (7, "Split the G FC", "Kavinu", 319, "39.9"),
            (8, "Pakason FC", "Ometh", 317, "39.6"),
            (9, "Assnal Dulaj", "Samithu", 302, "37.8"),
            (10, "Saddam Huijsen", "Sandaru", 301, "37.6"),
        ],
    )

    waivers(
        plate,
        f"{OUT}/Farmers-League-GW8-Waivers.png",
        [
            ("Wirtz Case Scenario", "Umar", [("Silva", "BOU  ·  DEF", "Maguire", "MUN  ·  DEF")]),
            ("Los Porros Hermanos", "Rihab", [("Kudus", "TOT  ·  MID", "Sarr", "CRY  ·  MID")]),
            ("Split the G FC", "Kavinu", [("Kroupi Jr", "BOU  ·  MID", "Sávio", "TOT  ·  MID")]),
            (
                "Pakason FC",
                "Ometh",
                [
                    ("Ayari", "BHA  ·  MID", "Rayan", "BOU  ·  MID"),
                    ("Hato", "CHE  ·  DEF", "Senesi", "TOT  ·  DEF"),
                    ("Benítez", "CRY  ·  GKP", "Pope", "NEW  ·  GKP"),
                    ("Thomas-Asante", "COV  ·  FWD", "Ekitiké", "LIV  ·  FWD"),
                ],
            ),
            (
                "Assnal Dulaj",
                "Samithu",
                [
                    ("King", "FUL  ·  MID", "Mitoma", "BHA  ·  MID"),
                    ("Ajer", "BRE  ·  DEF", "O'Reilly", "MCI  ·  DEF"),
                    ("Zirkzee", "MUN  ·  FWD", "Emersonn", "IPS  ·  FWD"),
                ],
            ),
            (
                "Saddam Huijsen",
                "Sandaru",
                [
                    ("Mbaye", "AVL  ·  MID", "Willock", "NEW  ·  MID"),
                    ("Cash", "AVL  ·  DEF", "Frimpong", "LIV  ·  DEF"),
                ],
            ),
        ],
    )

    star(
        plate,
        f"{OUT}/Farmers-League-GW8-Gabriel.png",
        f"{LEAGUE}/Gabriel M 8k.avif",
        0.50,
        0.22,
        "GW8 STAR",
        "GABRIEL",
        17,
        "90 mins  ·  1 goal  ·  clean sheet  ·  3 bonus  ·  2 defcon",
        "Arsenal 2–0 Everton",
        "Chennaiyin FC  ·  Vidhun",
    )
    star(
        plate,
        f"{OUT}/Farmers-League-GW8-Konsa.png",
        f"{LEAGUE}/Ezri Konsa 8K.avif",
        0.58,
        0.28,
        "GW8 STAR",
        "EZRI KONSA",
        14,
        "90 mins  ·  1 goal  ·  clean sheet  ·  2 bonus",
        "Arsenal 2–0 Everton",
        "Pakason FC  ·  Ometh",
    )
    star(
        plate,
        f"{OUT}/Farmers-League-GW8-Jackson.png",
        f"{LEAGUE}/Nicolas Jackson 8K.jpg",
        0.34,
        0.18,
        "GW8 STAR",
        "NICOLAS JACKSON",
        13,
        "81 mins  ·  2 goals  ·  3 bonus",
        "Aston Villa 2–1 Man City",
        "Chennaiyin FC  ·  Vidhun",
    )


if __name__ == "__main__":
    main()
