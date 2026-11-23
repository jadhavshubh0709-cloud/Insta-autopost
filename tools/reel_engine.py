"""Reel engine for @smartwork.ai.in: turns a small JSON spec into a 1080x1920 reel with music.

Usage:
  python3 tools/reel_engine.py spec.json out_dir/          -> out_dir/reel.mp4 + out_dir/caption.txt
  python3 tools/reel_engine.py spec.json out_dir/ preview  -> preview JPGs of each scene's last frame

Spec:
{
  "tag": "AI HACK #2",
  "music": "chill",                        # upbeat | chill | dramatic | funky
  "caption": "....",
  "scenes": [
    {"type": "hook",  "lines": ["5 AI tools", "that feel", "illegal to know"], "accent": 1, "sub": "(save this)", "dur": 3},
    {"type": "item",  "num": 1, "title": "Gamma", "text": "Type one line, get a full PPT", "dur": 3},
    {"type": "chat",  "title": "Copy this prompt", "text": "....", "dur": 6},
    {"type": "result","title": "AI's version:", "text": "....", "footer": "Same work. 10x stronger.", "tip": "...", "dur": 4},
    {"type": "text",  "title": "Big line", "text": "smaller line", "color": "accent", "dur": 3},
    {"type": "cta",   "big": "SAVE this", "sub": "...", "pill": "Comment PROMPT", "pill_sub": "...", "follow": "Follow for daily AI hacks", "dur": 4}
  ]
}
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
def font(name, size): return ImageFont.truetype(F + name, size)

BG1, BG2 = (14, 12, 30), (38, 20, 70)
WHITE = (245, 245, 250); MUTED = (170, 165, 195)
ACCENT = (255, 196, 0); RED = (255, 82, 82); GREEN = (46, 213, 115); PURPLE = (150, 110, 255)
COLORS = {"white": WHITE, "accent": ACCENT, "red": RED, "green": GREEN, "purple": PURPLE, "muted": MUTED}
HANDLE = "@smartwork.ai.in"

_bg = None
def background():
    global _bg
    if _bg is None:
        img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(BG1[i] + (BG2[i] - BG1[i]) * t) for i in range(3)))
        _bg = img
    return _bg.copy()

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3

def wrap(d, text, fnt, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            test = (cur + " " + w).strip()
            if d.textlength(test, font=fnt) <= maxw: cur = test
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def centered(d, y, text, fnt, fill, maxw=920, gap=1.18):
    for ln in wrap(d, text, fnt, maxw):
        d.text(((W - d.textlength(ln, font=fnt)) / 2, y), ln, font=fnt, fill=fill)
        y += int(fnt.size * gap)
    return y

def fit_font(d, text, name, size, maxw, max_lines):
    while size > 30:
        f = font(name, size)
        if len(wrap(d, text, f, maxw)) <= max_lines: return f
        size -= 4
    return font(name, size)

class Ctx:
    def __init__(self, tag, step, total): self.tag, self.step, self.total = tag, step, total

def chrome(d, ctx):
    tag = font("Inter-Bold.otf", 34)
    tw = d.textlength(ctx.tag, font=tag)
    d.rounded_rectangle([(W - tw) / 2 - 30, 150, (W + tw) / 2 + 30, 214], 32, fill=PURPLE)
    d.text(((W - tw) / 2, 162), ctx.tag, font=tag, fill=WHITE)
    h = font("Inter-Medium.otf", 32)
    d.text(((W - d.textlength(HANDLE, font=h)) / 2, 1420), HANDLE, font=h, fill=MUTED)
    n = ctx.total; gap = 40
    for i in range(n):
        x = W / 2 - gap * (n - 1) / 2 + i * gap
        d.ellipse([x - 8, 1480, x + 8, 1496], fill=ACCENT if i <= ctx.step else (80, 70, 110))

def fade_in(img, t, dur=0.25):
    return img if t >= dur else Image.blend(background(), img, ease(t / dur))

# ---------------- scene types ----------------
def s_hook(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    big = font("InterDisplay-Black.otf", s.get("size", 104))
    layer = Image.new("RGBA", (W, 760), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    yy = 0
    for i, ln in enumerate(s["lines"]):
        yy = centered(ld, yy, ln, big, ACCENT if i == s.get("accent", 1) else WHITE)
    k = 0.85 + 0.15 * ease(t / 0.4)
    lw, lh = int(W * k), int(760 * k)
    layer = layer.resize((lw, lh))
    top = 380 + (900 - yy) // 2
    img.paste(layer, ((W - lw) // 2, top + (760 - lh) // 2), layer)
    if s.get("sub") and t > 0.9:
        centered(d, 1250, s["sub"], font("Inter-SemiBold.otf", 44), MUTED)
    return fade_in(img, t)

def s_item(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    k = ease(t / 0.35)
    r = 110
    cx, cy = W // 2, 470
    rr = int(r * (0.6 + 0.4 * k))
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=ACCENT)
    num = font("InterDisplay-Black.otf", int(130 * (0.6 + 0.4 * k)))
    ns = str(s["num"])
    bb = d.textbbox((0, 0), ns, font=num)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), ns, font=num, fill=BG1)
    title_f = fit_font(d, s["title"], "InterDisplay-Black.otf", 112, 920, 2)
    y = centered(d, 650 + int(40 * (1 - k)), s["title"], title_f, WHITE)
    if t > 0.5:
        card_top = y + 40
        body = fit_font(d, s["text"], "Inter-SemiBold.otf", 58, 800, 4)
        lines = wrap(d, s["text"], body, 800)
        hgt = len(lines) * int(body.size * 1.25) + 90
        d.rounded_rectangle([90, card_top, 990, card_top + hgt], 36, fill=(30, 26, 50), outline=PURPLE, width=3)
        yy = card_top + 45
        for ln in lines:
            d.text(((W - d.textlength(ln, font=body)) / 2, yy), ln, font=body, fill=WHITE); yy += int(body.size * 1.25)
    if s.get("tag") and t > 1.0:
        centered(d, 1300, s["tag"], font("Inter-Bold.otf", 44), ACCENT)
    return fade_in(img, t)

def s_chat(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    centered(d, 300, s.get("title", "Copy this prompt"), font("InterDisplay-Black.otf", 92), ACCENT)
    d.rounded_rectangle([70, 470, 1010, 1130], 32, fill=(18, 16, 34), outline=PURPLE, width=4)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([110 + i * 44, 505, 136 + i * 44, 531], fill=c)
    d.text((260, 498), "AI chat", font=font("Inter-Medium.otf", 32), fill=MUTED)
    text = s["text"]; dur = s.get("dur", 6)
    n = int(len(text) * min(1, max(0, (t - 0.3) / (dur * 0.7))))
    mono = ImageFont.truetype(MONO, 44)
    y = 580; lines = wrap(d, text[:n], mono, 840)
    for ln in lines:
        d.text((120, y), ln, font=mono, fill=WHITE); y += 62
    if int(t * 2) % 2 == 0 and lines:
        x = 120 + d.textlength(lines[-1], font=mono)
        d.rectangle([x + 4, y - 58, x + 26, y - 10], fill=ACCENT)
    return fade_in(img, t)

def s_result(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    centered(d, 330, s.get("title", "AI's version:"), font("InterDisplay-Bold.otf", 72), MUTED)
    k = ease(t / 0.5); top = 520 + int(60 * (1 - k))
    body = fit_font(d, s["text"], "Inter-Bold.otf", 58, 800, 6)
    lines = wrap(d, s["text"], body, 800)
    hgt = len(lines) * int(body.size * 1.18) + 140
    d.rounded_rectangle([80, top, 1000, top + hgt], 36, fill=(16, 48, 38), outline=GREEN, width=5)
    centered(d, top + 70, s["text"], body, WHITE, maxw=800)
    if s.get("footer") and t > 1.0:
        centered(d, top + hgt + 80, s["footer"], font("InterDisplay-Black.otf", 76), GREEN)
    if s.get("tip") and t > 1.8:
        centered(d, 1300, s["tip"], font("Inter-SemiBold.otf", 44), ACCENT)
    return fade_in(img, t)

def s_text(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    big = fit_font(d, s["title"], "InterDisplay-Black.otf", s.get("size", 110), 920, 4)
    y = centered(d, 520, s["title"], big, COLORS.get(s.get("color", "white"), WHITE))
    if s.get("text") and t > 0.7:
        centered(d, y + 50, s["text"], font("Inter-SemiBold.otf", 52), MUTED, maxw=860)
    return fade_in(img, t)

def s_cta(s, ctx, t):
    img = background(); d = ImageDraw.Draw(img); chrome(d, ctx)
    y = centered(d, 430, s.get("big", "SAVE this"), font("InterDisplay-Black.otf", 130), ACCENT)
    if s.get("sub"): centered(d, y + 10, s["sub"], font("Inter-SemiBold.otf", 56), WHITE, maxw=860)
    if s.get("pill") and t > 0.8:
        pill = font("Inter-Bold.otf", 54); txt = s["pill"]; tw = d.textlength(txt, font=pill)
        p = 1 + 0.04 * math.sin(t * 6); pw, ph = (tw + 100) * p, 120 * p
        d.rounded_rectangle([(W - pw) / 2, 900, (W + pw) / 2, 900 + ph], int(ph / 2), fill=PURPLE)
        d.text(((W - tw) / 2, 900 + (ph - 66) / 2), txt, font=pill, fill=WHITE)
        if s.get("pill_sub"): centered(d, 1060, s["pill_sub"], font("Inter-Medium.otf", 46), MUTED)
    if t > 1.6:
        centered(d, 1200, s.get("follow", "Follow for daily AI hacks"), font("Inter-Bold.otf", 52), WHITE)
    return fade_in(img, t)

SCENES = {"hook": s_hook, "item": s_item, "chat": s_chat, "result": s_result, "text": s_text, "cta": s_cta}

def render_scene(fn, s, ctx, path):
    tmp = path + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for i in range(int(s.get("dur", 3) * FPS)):
        p.stdin.write(fn(s, ctx, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0: raise SystemExit("ffmpeg failed on " + path)
    os.replace(tmp, path)

def build(spec, out_dir, preview=False):
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(out_dir, ".work"); os.makedirs(work, exist_ok=True)
    scenes = spec["scenes"]
    if preview:
        for i, s in enumerate(scenes):
            SCENES[s["type"]](s, Ctx(spec["tag"], i, len(scenes)), s.get("dur", 3) - 0.05).save(
                os.path.join(out_dir, f"prev_{i:02d}_{s['type']}.jpg"), quality=85)
        return
    files = []
    for i, s in enumerate(scenes):
        path = os.path.join(work, f"{i:02d}.mp4")
        render_scene(SCENES[s["type"]], s, Ctx(spec["tag"], i, len(scenes)), path); files.append(path)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for x in files: f.write(f"file '{os.path.abspath(x)}'\n")
    silent = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    dur = sum(s.get("dur", 3) for s in scenes)
    music = os.path.join(ROOT, "music", spec.get("music", "upbeat") + ".m4a")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", music,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", f"volume=0.8,afade=t=out:st={max(0, dur - 1.5)}:d=1.5", "-c:a", "aac", "-b:a", "160k",
                    "-t", str(dur), "-movflags", "+faststart", os.path.join(out_dir, "reel.mp4")], check=True)
    with open(os.path.join(out_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(spec["caption"].strip() + "\n")
    for x in os.listdir(work): os.remove(os.path.join(work, x))
    os.rmdir(work)

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    build(spec, sys.argv[2], preview=len(sys.argv) > 3 and sys.argv[3] == "preview")
