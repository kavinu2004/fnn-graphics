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
  - No jokes about bodies, ethnicity or relationships.
  - Don't invent personal facts.
- Never say who writes the graphics.
- Check every claim against the data: points, who signed whom, which week.
- Reword lines so they don't break on a hyphen at the card width. Check the rendered PNG.
