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
- **Voice reference:** the user wrote the GW10 cards for Heung Min Dad, Wirtz Case Scenario and Los Porros Hermanos (see `gameweeks/gw10.json`). Match that voice.
  - Present-tense storytelling about the team's week, not a stat recap.
  - Refer to teams the way the league does ("the Heung Min boys", "Los Porros lives in the heat").
  - Bring in the forfeit table and the race around a team, and end on what's next (a squad revamp, someone closing in).
  - Mostly warm. A light roast ("whenever Umar decides to start the right keeper…"), with the occasional throwaway slang line ("the boys are right on his ahh").
- If the user writes any cards themselves, use their text as written, fixing only typos, accents and player-name spellings.
- Two short paragraphs per card. Skip the stat dump, because everyone has the PL app.
- The humour should come from what actually happened that week.
  - No lazy puns on team or player names (e.g. Wirtz / Wirtz Case Scenario).
  - Don't stack comparisons.
  - Don't open several cards with "Last week…".
  - Don't stack "X got N, Y got N" lines.
- No jokes about bodies, ethnicity or relationships. Don't invent personal facts.
- Never say who writes the graphics.
- Check every claim against the data: points, who signed whom, which week.
- Line breaks:
  - Reword lines so they don't break on a hyphen at the card width.
  - Use `&nbsp;` to keep two-word names together (Le&nbsp;Fée, N.&nbsp;Jackson, Split&nbsp;the&nbsp;G).
  - Check the rendered PNG.

## Forfeits
- The team that finishes 10th at the end of the season does one big forfeit.
- Every 6 gameweeks there's a mini forfeit for whoever is last on the forfeit table over that block:
  - GW1–6: run a 10k. Samithu did it.
  - GW7–12: stare at a wall for an hour. After GW10, Sandaru was last and Imad had climbed from 9th to 6th.
- Ask the user for forfeit-table positions. They aren't in the app screenshots, so don't work them out yourself.
- The forfeit race is good material, especially for the bottom-half cards and near the end of a block.
