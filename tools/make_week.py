"""One command for the weekly batch: validate -> render -> verify -> one review sheet.

Usage:
  python3 tools/make_week.py                 # every specs/YYYY-MM-DD.json without a rendered reel
  python3 tools/make_week.py 2026-12-01 ...  # only these dates
  python3 tools/make_week.py --check         # validate specs only, render nothing

Writes review/week_sheet.jpg (one row per reel: cover frame + each scene's last frame)
so the whole week can be checked with a single image. review/ is git-ignored.
"""
import glob, json, os, re, subprocess, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import reel_engine as eng

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMOJI = re.compile("[\U0001F000-\U0010FFFF☀-➿⬀-⯿️]")
TEXT_KEYS = ("lines", "title", "text", "sub", "tag", "footer", "tip", "big", "pill", "pill_sub", "follow")

def validate(date, spec):
    errs = []
    sc = spec.get("scenes", [])
    if not sc: return ["no scenes"]
    for i, s in enumerate(sc):
        if s.get("type") not in eng.SCENES: errs.append(f"scene {i}: unknown type {s.get('type')}")
        for k in TEXT_KEYS:
            v = s.get(k)
            vals = v if isinstance(v, list) else [v] if isinstance(v, str) else []
            if any(EMOJI.search(x) for x in vals): errs.append(f"scene {i}: emoji in on-screen '{k}' (won't render)")
    first = sc[0]
    if first.get("type") not in ("hook", "text"): errs.append("first scene must be hook/text (it is the cover)")
    if first.get("dur", 3) < 2.5: errs.append("first scene must last >= 2.5 s (cover frame is at 2.0 s)")
    total = sum(s.get("dur", 3) for s in sc)
    if not 15 <= total <= 25: errs.append(f"length {total:.1f}s, keep 15-25s")
    if spec.get("music") not in ("upbeat", "chill", "dramatic", "funky"): errs.append("music must be upbeat/chill/dramatic/funky")
    cap = spec.get("caption", "")
    if "#smartwork" not in cap: errs.append("caption must end with #smartwork")
    if not 7 <= cap.count("#") <= 10: errs.append(f"caption has {cap.count('#')} hashtags, use 7-9")
    return errs

def probe_ok(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", mp4],
                         capture_output=True, text=True).stdout.split()
    return "video" in out and "audio" in out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv
    specs = sorted(glob.glob(os.path.join(ROOT, "specs", "*.json")))
    todo = []
    for p in specs:
        d = os.path.basename(p)[:-5]
        if not DATE.match(d): continue
        if args and d not in args: continue
        if not args and os.path.exists(os.path.join(ROOT, "reels", d, "reel.mp4")): continue
        todo.append((d, p))
    if not todo: print("Nothing to do."); return
    bad = False
    for d, p in todo:
        errs = validate(d, json.load(open(p, encoding="utf-8")))
        for e in errs: print(f"[{d}] {e}")
        bad |= bool(errs)
    if bad: sys.exit("Fix the spec errors above, then run again.")
    print("Specs OK:", ", ".join(d for d, _ in todo))
    if check_only: return

    review = os.path.join(ROOT, "review"); os.makedirs(review, exist_ok=True)
    rows = []
    for d, p in todo:
        spec = json.load(open(p, encoding="utf-8"))
        out = os.path.join(ROOT, "reels", d)
        eng.build(spec, out)
        mp4 = os.path.join(out, "reel.mp4")
        if not probe_ok(mp4): sys.exit(f"[{d}] reel.mp4 missing video or audio")
        cover = os.path.join(review, f"{d}_cover.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2.0", "-i", mp4, "-frames:v", "1", "-q:v", "3", cover], check=True)
        frames = [Image.open(cover)]
        n = len(spec["scenes"])
        for i, s in enumerate(spec["scenes"]):
            frames.append(eng.SCENES[s["type"]](s, eng.Ctx(spec["tag"], i, n), s.get("dur", 3) - 0.05))
        rows.append((d, [f.resize((180, 320)) for f in frames]))
        dur = sum(s.get("dur", 3) for s in spec["scenes"])
        print(f"[{d}] rendered {dur:.1f}s, music={spec['music']}, hook: {' / '.join(spec['scenes'][0].get('lines', [spec['scenes'][0].get('title', '')]))}")
    w = max(len(r) for _, r in rows) * 180
    sheet = Image.new("RGB", (w, 320 * len(rows)), (0, 0, 0))
    for j, (_, r) in enumerate(rows):
        for i, im in enumerate(r): sheet.paste(im, (i * 180, j * 320))
    sheet.save(os.path.join(review, "week_sheet.jpg"), quality=80)
    print("Review sheet: review/week_sheet.jpg  (first column of each row = cover)")

if __name__ == "__main__":
    main()
