# SmartWork reel factory (@smartwork.ai.in)

Faceless Instagram page: daily AI hacks. EVERY reel is about AI (tools, prompts, AI hacks), no pure office-humour reels. Owner: Shubhangi.
Goal: secondary income (affiliate links, brand deals, prompt PDFs) via consistent daily reels.

## How posting works (don't touch)
- `.github/workflows/post-reel.yml` runs daily at 13:30 UTC (7 PM IST) and posts `reels/<today IST>/reel.mp4` + `caption.txt`.
- Cover = frame at 2.0 s (the hook screen). Optional `reels/<date>/cover.jpg` overrides it.
- Token is a never-expiring system-user token in the `IG_ACCESS_TOKEN` secret. Never print, commit or ask for it.
- Do not edit `src/`, `.github/`, secrets, or run the post workflow unless the owner asks in chat.

## Weekly batch: the whole job
1. Find the dates to fill: tomorrow through 7 days ahead (Asia/Kolkata). Skip dates that already have `reels/<date>/`.
2. Take ideas from `content/ideas.md` in order (first unticked ones). **All 7 reels must be AI reels.**
   Office, student or career situations are fine only as the setting for an AI tool or prompt.
3. Write `specs/<date>.json` for each date (format below; copy the style of an existing spec).
4. Run `python3 tools/make_week.py`. It validates, renders, verifies audio and video, and writes `review/week_sheet.jpg`.
   Fix any reported errors and re-run. Look at the ONE sheet image (not the individual frames) and fix any overflowing text.
5. Tick the used ideas in `content/ideas.md` (`- [x] ... (<date>)`). If fewer than 10 unticked ideas are left, append 15 new ones in the same style.
6. `git add specs reels content && git commit -m "Queue reels for <first> to <last>" && git push`.
7. Reply with a short table: date, topic, music.

## Spec format (tools/reel_engine.py)
```json
{"tag": "AI HACK #7", "music": "upbeat|chill|dramatic|funky",
 "caption": "hook line + emoji\n\ncomment prompt\n\n#tag1 ... #smartwork",
 "scenes": [
  {"type": "hook", "lines": ["line 1", "line 2", "line 3"], "accent": 1, "sub": "(optional teaser)", "dur": 3},
  {"type": "item", "num": 1, "title": "Short title", "text": "One-line benefit.", "tag": "punchline", "dur": 3.2},
  {"type": "chat", "title": "Copy this prompt", "text": "the prompt with [brackets]", "dur": 7},
  {"type": "result", "title": "AI's version:", "text": "realistic output", "footer": "short win", "tip": "optional", "dur": 4.5},
  {"type": "text", "title": "Big line", "text": "small line", "color": "accent|white|red|green|muted", "size": 110, "dur": 3},
  {"type": "cta", "big": "SAVE this", "sub": "...", "pill": "Comment PROMPT", "pill_sub": "...", "follow": "Follow for daily AI hacks", "dur": 4}
 ]}
```

## Rules (make_week.py enforces the starred ones)
- * First scene is the hook (`hook` or big `text`), at least 2.5 s. It is the cover, so it must be readable at a glance.
- * Total length 15-25 s. * Music is one of the 4 tracks in `music/`.
- * No emoji in on-screen text (they render as boxes). Emoji are fine in captions.
- * Caption: hook, a comment prompt ("Comment PROMPT" / "Comment 1-3" / "Tag a colleague"), 7-9 hashtags ending `#smartwork`.
- Music by mood: upbeat = AI tools/hacks, chill = prompts/tips, dramatic = before-vs-after, funky = light/funny AI reels.
- Tag numbering: continue from the highest number used in `specs/` (e.g. AI HACK #6, PROMPT #5).
- Facts: no prices, "free", version numbers or rankings. Describe tools only in general terms, and only name well-known tools.
- Humour (if any): relatable, kind, with no real people, companies or insults, and always tied to an AI tip.
- Language: simple English, Indian context (INR, Indian names, Diwali, appraisal, standups, WFH).
