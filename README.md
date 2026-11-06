# FNN graphics

The weekly Farmers League / FNN Instagram carousel (1080×1350), built from one JSON file per gameweek.

Each slide is an HTML page laid over `assets/template.jpg`. Headless Chromium screenshots each page, so every name and number on a slide is exactly what's in the JSON.

## Setup (once)

```bash
./setup.sh
```

This creates `.venv` with Playwright 1.64.1 and installs its headless Chromium. Fonts load from Google Fonts at build time, so you need to be online.

## Each gameweek

1. Start the new week's file from the previous week's table:

   ```bash
   .venv/bin/python build.py new 10
   ```

   This writes `gameweeks/gw10.json`. Each team's `prev_rank` is filled in from the GW9 order.

2. Fill in `gameweeks/gw10.json` from the app:
   - **`table`**: reorder the rows into the new standings order. Then fill in each team's `total`, `points` (points this week), `headline` (a white line and a lime line) and `body` (two short paragraphs).
   - **`stars`**: up to three players. Each one needs a `photo` in `assets/photos/` and a `focus` (the CSS `object-position` for the crop).
   - **`waivers`**: one entry per manager, in the form `[in, out]`, or `[in, out, "FA"]` for a free agent.

3. Build the slides:

   ```bash
   .venv/bin/python build.py gameweeks/gw10.json --out ~/Desktop/FNN
   ```

   To redo just some slides, add `--only`:

   ```bash
   .venv/bin/python build.py gameweeks/gw10.json --out ~/Desktop/FNN --only Standings 05-
   ```

The build stops before rendering if any numbers or copy are missing, if the table is out of order, or if a manager or photo can't be found.

## Slides

Files are named `Farmers-League-GW{N}-…png`, in carousel order:

| Slide | Notes |
|---|---|
| `FNN` | series cover: white GAMEWEEK N, FNN, FARMERS NEWS NETWORK |
| `Standings` | rank, movement pill (green ▲N / red ▼N / grey dot), team over manager, PTS |
| one per star (`Van-Hecke`…) | full-bleed photo, points, stat line, fixture, drafted by |
| `Waivers` | two-column grid, IN → OUT, FA tag |
| `00-Team-News` | team-news cover |
| `01-…` to `10-…` | one card per team: Overall, Total, GW points, headline, two paragraphs |

## Copy markup

The `headline` and `body` fields are HTML:
- `<b>Player</b>` makes a name bold white.
- `<em>12</em>` makes a number lime.

Keep each card to two short paragraphs: what happened, then the joke. Everyone has the PL app, so the cards don't need a stat dump.

## Archive

`archive/` holds the graphics that shipped before this template existed:
- **gw6**: series cover, stars, waivers and the old weekly standings.
- **gw7**: the team-news set, whose card header and cover spacing this template copies.
- **gw8**: the full set, plus `build_gw8.py`, the Pillow script that made it. GW8's fonts were dropped, so treat it as history, not as a reference.

## Layout

All measurements live in `styles/base.css`. They're calibrated against the GW6/GW7 PNGs:
- The card header and covers match GW7 exactly.
- The body text is Barlow Semi Condensed 36/47, the version approved for GW9.

Captures use `--force-color-profile=display-p3-d65` so the lime comes out as (222, 254, 107), matching earlier weeks. `gameweeks/gw9.json` re-renders the shipped GW9 set pixel for pixel, so use it as a reference after any CSS change.
