# FNN graphics: notes for Claude

The weekly Farmers League carousel. See README.md for the build steps.

## Rules
- Render slides only with `build.py`: HTML over the template, Chromium screenshot, deviceScaleFactor 1, one clip per slide.
  - Never use image generation; names and numbers have to be exact.
  - Never crop or resize the PNGs afterwards (no sips, no PIL).
- Copy every number from the user's screenshots. Don't infer or round anything.
- Ask which gameweek the waiver screenshots belong to. GW9 first shipped with GW10's waivers by mistake.
  - The waiver slide shows the moves processed before that week.
  - The following week's waivers are good material for card jokes (how managers reacted).
- Don't touch styles/base.css unless the user asks for a visual change. After any CSS change, rebuild gw9.json and diff it against the shipped GW9 PNGs.

## Card copy
- Two short paragraphs: what happened, then the joke. Skip the stat dump, because everyone has the PL app.
- Roast managers personally for their decisions, and give praise where it's earned. Make it funny.
- The humour should come from what actually happened that week. One good line per card beats several gags.
- Write in loose football-banter vernacular (hauled, blanked, did bits, crocked, rode the pine, bagged a brace, green/red arrow, binned) rather than flat match-report English.
  - No lazy puns on team or player names (e.g. Wirtz / Wirtz Case Scenario).
  - Don't stack comparisons, and don't give every card the same "Like…" analogy.
- Give each card its own angle. Across the set, don't open several cards with "Last week…", and don't stack "X got N, Y got N" lines.
- Callbacks to earlier weeks are fine, but use only one or two per set, and don't reuse a punchline from a previous week.

## Forfeits
- The team that finishes 10th at the end of the season does one big forfeit.
- Every 6 gameweeks there's a mini forfeit for whoever is last over that block:
  - GW1–6: run a 10k. Samithu did it.
  - GW7–12: stare at a wall for an hour. Sandaru was last after GW10.
  - Ask the user who is last in the current block and what the next forfeit is. Don't work it out yourself.
- Forfeits are good material for the bottom-half cards, especially near the end of a block.
  - No jokes about bodies, ethnicity or relationships.
  - Don't invent personal facts.
- Never say who writes the graphics.
- Check every claim against the data: points, who signed whom, which week.
- Reword lines so they don't break on a hyphen at the card width. Check the rendered PNG.
