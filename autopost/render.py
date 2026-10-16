import sys, os, json, math, subprocess, wave, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS, DUR = 1080, 1920, 30, 13.0
N = int(FPS * DUR)
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
F9 = os.path.join(FONT_DIR, "Cairo-900.ttf")
F7 = os.path.join(FONT_DIR, "Cairo-700.ttf")
BG1, BG2 = (10, 18, 48), (33, 20, 90)
BLUE, YEL, PINK, WHITE = (47, 123, 255), (255, 210, 63), (255, 79, 139), (255, 255, 255)

L = {
 "ar": dict(h1="حوّل فيديوك", h2="إلى ملصق متحرك", hs="بثواني بس", steps=["اختر فيديو", "إزالة الخلفية", "اكتب عليه", "ملصقك جاهز!"], laugh="ههههههه", feats=["مجاني", "بدون تسجيل", "بدون علامة مائية"], cta="ابحث في Google Play عن:", kw="ملصقات"),
 "pt": dict(h1="Transforme seu vídeo", h2="em figurinha animada", hs="em segundos", steps=["Escolha um vídeo", "Remova o fundo", "Escreva", "Figurinha pronta!"], laugh="KKKKKK", feats=["Grátis", "Sem cadastro", "Sem marca d'água"], cta="Pesquise no Google Play:", kw="figurinhas"),
 "es": dict(h1="Convierte tu video", h2="en sticker animado", hs="en segundos", steps=["Elige un video", "Quita el fondo", "Escribe", "¡Sticker listo!"], laugh="JAJAJA", feats=["Gratis", "Sin registro", "Sin marca de agua"], cta="Busca en Google Play:", kw="crear stickers"),
 "id": dict(h1="Ubah videomu", h2="jadi stiker animasi", hs="cuma hitungan detik", steps=["Pilih video", "Hapus latar", "Tulis teks", "Stiker siap!"], laugh="WKWKWK", feats=["Gratis", "Tanpa daftar", "Tanpa watermark"], cta="Cari di Google Play:", kw="stiker animasi"),
 "en": dict(h1="Turn any video", h2="into an animated sticker", hs="in seconds", steps=["Pick a video", "Remove background", "Add text", "Sticker ready!"], laugh="LOL", feats=["Free", "No sign-up", "No watermark"], cta="Search on Google Play:", kw="gif sticker maker"),
 "tr": dict(h1="Videonu", h2="hareketli sticker yap", hs="saniyeler içinde", steps=["Video seç", "Arka planı sil", "Yazı ekle", "Sticker hazır!"], laugh="HAHAHA", feats=["Ücretsiz", "Kayıt yok", "Filigran yok"], cta="Google Play'de ara:", kw="sticker yapma"),
 "de": dict(h1="Mach dein Video", h2="zum animierten Sticker", hs="in Sekunden", steps=["Video wählen", "Hintergrund entfernen", "Text hinzufügen", "Sticker fertig!"], laugh="HAHAHA", feats=["Kostenlos", "Ohne Anmeldung", "Ohne Wasserzeichen"], cta="Suche bei Google Play:", kw="sticker machen"),
}

_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(f, a, b): return clamp((f - a) / max(1, (b - a)))
def ease_out(t): return 1 - (1 - t) ** 3
def back(t):
    c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def fit_font(text, size, maxw, path=F9):
    s = size
    while s > 30:
        f = font(path, s)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= maxw: return f
        s -= 4
    return font(path, s)

def text_img(text, size, color, maxw=960, stroke=0, scolor=(0, 0, 0), path=F9):
    f = fit_font(text, size, maxw, path)
    bb = f.getbbox(text, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), text, font=f, fill=color, stroke_width=stroke, stroke_fill=scolor)
    return im

def paste_c(base, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def rrect(size, r, fill, outline=None, width=0):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=fill, outline=outline, width=width)
    return im

# ---------- background ----------
def make_bg():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    t = np.clip(0.6 * y + 0.4 * x, 0, 1)[..., None]
    arr = (np.array(BG1) * (1 - t) + np.array(BG2) * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")
BG = make_bg()
def bg_frame(f):
    im = BG.copy(); d = ImageDraw.Draw(im)
    for i in range(14):  # floating soft dots
        px = (i * 197 + f * (1 + i % 3)) % (W + 200) - 100
        py = (i * 331 + int(40 * math.sin(f / 25 + i))) % H
        r = 6 + (i % 4) * 5
        c = [BLUE, PINK, YEL][i % 3]
        d.ellipse((px - r, py - r, px + r, py + r), fill=c + (70,))
    return im

# ---------- original cat character ----------
def cat_layer(f, s=520):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bob = math.sin(f / 4.0)
    cx, cy = s / 2, s / 2 + 30 + bob * 10
    sq = 1 + 0.04 * bob
    O, OD, P = (255, 159, 67), (230, 120, 40), (255, 140, 170)
    # body
    d.ellipse((cx - 150, cy + 60, cx + 150, cy + 230), fill=O)
    # ears
    tilt = bob * 8
    d.polygon([(cx - 150, cy - 60), (cx - 120, cy - 200 + tilt), (cx - 40, cy - 120)], fill=O)
    d.polygon([(cx + 150, cy - 60), (cx + 120, cy - 200 - tilt), (cx + 40, cy - 120)], fill=O)
    d.polygon([(cx - 128, cy - 85), (cx - 115, cy - 160 + tilt), (cx - 70, cy - 115)], fill=P)
    d.polygon([(cx + 128, cy - 85), (cx + 115, cy - 160 - tilt), (cx + 70, cy - 115)], fill=P)
    # head
    hw, hh = 175 * sq, 150 / sq
    d.ellipse((cx - hw, cy - hh, cx + hw, cy + hh), fill=O)
    d.ellipse((cx - 70, cy - 140, cx + 70, cy - 90), fill=OD)
    # laughing eyes ^ ^
    for ex in (-70, 70):
        d.arc((cx + ex - 38, cy - 50, cx + ex + 38, cy + 10), 200, 340, fill=(40, 25, 20), width=14)
    # cheeks
    d.ellipse((cx - 140, cy + 5, cx - 85, cy + 45), fill=P + (200,))
    d.ellipse((cx + 85, cy + 5, cx + 140, cy + 45), fill=P + (200,))
    # open mouth
    mo = 40 + 18 * abs(math.sin(f / 3.0))
    d.chord((cx - 55, cy + 5, cx + 55, cy + 5 + mo * 2), 0, 180, fill=(120, 30, 40))
    d.ellipse((cx - 25, cy + 5 + mo, cx + 25, cy + 5 + mo * 1.8), fill=(255, 110, 120))
    d.polygon([(cx - 14, cy - 8), (cx + 14, cy - 8), (cx, cy + 8)], fill=(200, 70, 90))
    # whiskers
    for side in (-1, 1):
        for k in (-1, 0, 1):
            d.line((cx + side * 100, cy + 20 + k * 14, cx + side * 190, cy + 10 + k * 26), fill=(60, 35, 25), width=5)
    # paws
    d.ellipse((cx - 110, cy + 180, cx - 40, cy + 230), fill=OD)
    d.ellipse((cx + 40, cy + 180, cx + 110, cy + 230), fill=OD)
    return im

def video_bg(w, h, f):
    y = np.linspace(0, 1, h)[:, None]
    sky = np.array((120, 200, 255)) * (1 - y[..., None]) + np.array((190, 235, 255)) * y[..., None]
    arr = np.repeat(sky, w, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle((0, int(h * 0.72), w, h), fill=(110, 200, 110))  # grass
    d.ellipse((w - 170, 40, w - 60, 150), fill=(255, 230, 90))      # sun
    for i in range(3):
        x = (i * 230 + f * 2) % (w + 200) - 100
        d.ellipse((x, 90 + i * 60, x + 150, 140 + i * 60), fill=(255, 255, 255, 230))
    return im

def checker(w, h, c=36):
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((yy // c + xx // c) % 2).astype(np.uint8)
    arr = np.where(m[..., None] == 1, np.array((70, 76, 100)), np.array((50, 55, 78))).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")

def diecut(layer, pad=22):
    a = layer.getchannel("A")
    small = a.resize((a.width // 4, a.height // 4), Image.BILINEAR).filter(ImageFilter.MaxFilter(pad // 4 * 2 + 1))
    big = small.resize(a.size, Image.BILINEAR).point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.GaussianBlur(1.5))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); sh.putalpha(big.point(lambda v: v // 3))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 12))
    wl = Image.new("RGBA", layer.size, WHITE + (255,)); wl.putalpha(big)
    out.alpha_composite(wl); out.alpha_composite(layer)
    return out

def sticker_content(f, lang, s=640, text_p=1.0):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    im.alpha_composite(cat_layer(f), ((s - 520) // 2, 10))
    if text_p > 0:
        t = L[lang]["laugh"]
        n = max(1, int(round(len(t) * text_p)))
        ti = text_img(t[:n] if lang != "ar" else t[:n], 118, YEL, maxw=560, stroke=10, scolor=(25, 20, 60))
        im.alpha_composite(ti, ((s - ti.width) // 2, s - ti.height - 20))
    return im

# ---------- scenes ----------
def scene_hook(im, f, S):
    p1, p2, p3 = prog(f, 4, 16), prog(f, 14, 26), prog(f, 26, 38)
    paste_c(im, text_img(S["h1"], 120, WHITE, stroke=0), W / 2, 720, back(p1), alpha=p1)
    paste_c(im, text_img(S["h2"], 120, YEL, stroke=0), W / 2, 880, back(p2), alpha=p2)
    pill = text_img(S["hs"], 64, (20, 20, 40), path=F9)
    bgp = rrect((pill.width + 70, pill.height + 26), 50, PINK + (255,))
    bgp.alpha_composite(pill, (35, 13))
    paste_c(im, bgp, W / 2, 1060, back(p3), rot=-4 * (1 - p3), alpha=p3)
    # mini cat teaser
    paste_c(im, cat_layer(f, 520), W / 2, 1380, 0.55 * ease_out(prog(f, 30, 50)))
    # exit
    return im

PH_W, PH_H = 700, 1240
SCR = (40, 40, PH_W - 40, PH_H - 40)
def phone_frame():
    im = rrect((PH_W, PH_H), 90, (18, 20, 30, 255), outline=(90, 100, 140, 255), width=6)
    ImageDraw.Draw(im).rounded_rectangle((PH_W / 2 - 70, 18, PH_W / 2 + 70, 34), 8, fill=(40, 44, 60))
    return im
PHONE = phone_frame()
CHK = checker(SCR[2] - SCR[0], SCR[3] - SCR[1])
SCR_MASK = rrect((SCR[2] - SCR[0], SCR[3] - SCR[1]), 60, (255, 255, 255, 255)).getchannel("A")

def scene_phone(im, f, S, lang):
    lf = f - 75
    enter = ease_out(prog(lf, 0, 14))
    sw, sh = SCR[2] - SCR[0], SCR[3] - SCR[1]
    screen = Image.new("RGBA", (sw, sh), (20, 24, 40, 255))
    step = 0 if lf < 40 else 1 if lf < 80 else 2 if lf < 120 else 3
    # video area
    vbg = video_bg(sw, sh, f)
    if step == 0:
        screen = vbg
    else:
        wipe = ease_out(prog(lf, 42, 72))
        cut = int(sw * wipe)
        screen = CHK.copy()
        if cut < sw: screen.alpha_composite(vbg.crop((cut, 0, sw, sh)), (cut, 0))
        if 0 < wipe < 1:
            ImageDraw.Draw(screen).rectangle((cut - 4, 0, cut + 4, sh), fill=YEL + (255,))
    tp = prog(lf, 84, 112) if step >= 2 else 0.0
    content = sticker_content(f, lang, 640, tp)
    if step == 3:
        content = diecut(content)
    paste_c(screen, content, sw / 2, sh / 2 + 40, 0.92)
    if step == 0:  # play bar
        d = ImageDraw.Draw(screen)
        d.rounded_rectangle((40, sh - 70, sw - 40, sh - 56), 7, fill=(255, 255, 255, 120))
        d.rounded_rectangle((40, sh - 70, 40 + (sw - 80) * prog(lf, 0, 40), sh - 56), 7, fill=PINK + (255,))
    screen.putalpha(ImageChops.multiply(screen.getchannel("A"), SCR_MASK))
    ph = PHONE.copy(); ph.alpha_composite(screen, (SCR[0], SCR[1]))
    pop = ease_out(prog(lf, 128, 150))
    cy = 1020 + (1 - enter) * 900
    paste_c(im, ph, W / 2, cy, 0.95 - 0.08 * pop, alpha=1 - 0.5 * pop)
    # step chip (top)
    chip_t = text_img(f"{step + 1}  ·  {S['steps'][step]}" if lang != "ar" else f"{S['steps'][step]}  ·  {step + 1}", 64, WHITE)
    chip = rrect((chip_t.width + 80, chip_t.height + 30), 50, (BLUE if step < 3 else PINK) + (255,))
    chip.alpha_composite(chip_t, (40, 15))
    sp = back(prog(lf - [0, 40, 80, 120][step], 0, 10))
    paste_c(im, chip, W / 2, 290, sp * enter)
    # big sticker pops out at the end
    if step == 3 and pop > 0:
        big = diecut(sticker_content(f, lang, 640, 1.0))
        paste_c(im, big, W / 2, 1000 - 60 * pop, 0.9 + 0.35 * back(pop), rot=-6 * pop)
        if pop > 0.3:  # sparkles
            d = ImageDraw.Draw(im)
            for i in range(10):
                ang = i * 36 + lf * 3; r = 420 + 30 * math.sin(lf / 3 + i)
                x, y = W / 2 + r * math.cos(math.radians(ang)), 960 + r * math.sin(math.radians(ang))
                k = 14 + 8 * (i % 2)
                d.polygon([(x, y - k), (x + k / 3, y), (x, y + k), (x - k / 3, y)], fill=YEL + (255,))
                d.polygon([(x - k, y), (x, y - k / 3), (x + k, y), (x, y + k / 3)], fill=YEL + (255,))

def mini_sticker(kind, f, lang):
    s = 300
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 0:
        c = cat_layer(f + 7, 520).resize((280, 280)); im.alpha_composite(c, (10, 10))
    elif kind == 1:
        b = 1 + 0.08 * math.sin(f / 3)
        r = 100 * b; cx, cy = 150, 160
        d.ellipse((cx - r, cy - r * 0.9, cx, cy + r * 0.1), fill=PINK); d.ellipse((cx, cy - r * 0.9, cx + r, cy + r * 0.1), fill=PINK)
        d.polygon([(cx - r * 0.98, cy - r * 0.3), (cx + r * 0.98, cy - r * 0.3), (cx, cy + r * 0.95)], fill=PINK)
    elif kind == 2:  # star
        cx, cy, R = 150, 150, 120 + 8 * math.sin(f / 4)
        pts = [(cx + (R if i % 2 == 0 else R * 0.45) * math.cos(math.radians(-90 + i * 36 + f * 2)), cy + (R if i % 2 == 0 else R * 0.45) * math.sin(math.radians(-90 + i * 36 + f * 2))) for i in range(10)]
        d.polygon(pts, fill=YEL)
    else:  # thumbs-like smiley
        cx, cy = 150, 150
        d.ellipse((40, 40, 260, 260), fill=(255, 205, 60))
        d.ellipse((95, 105, 125, 145), fill=(40, 30, 20)); d.ellipse((175, 105, 205, 145), fill=(40, 30, 20))
        d.chord((85, 130, 215, 230), 0, 180, fill=(120, 30, 40))
    return diecut(im, pad=16)

def scene_feats(im, f, S, lang):
    lf = f - 240
    for i in range(4):
        ang = math.radians(i * 90 + 45 + lf * 1.5)
        x, y = W / 2 + 360 * math.cos(ang), 1000 + 520 * math.sin(ang)
        paste_c(im, mini_sticker(i, f, lang), x, y, 0.75 * back(prog(lf, i * 4, i * 4 + 14)), rot=8 * math.sin(lf / 6 + i))
    for i, t in enumerate(S["feats"]):
        p = prog(lf, 8 + i * 9, 20 + i * 9)
        ti = text_img(t, 76, (20, 20, 40))
        ck = Image.new("RGBA", (70, 70), (0, 0, 0, 0)); dk = ImageDraw.Draw(ck)
        dk.ellipse((0, 0, 69, 69), fill=(34, 180, 110)); dk.line((17, 36, 30, 50, 53, 22), fill=WHITE, width=9, joint="curve")
        pw = max(ti.width + 170, 600)
        pill = rrect((pw, ti.height + 36), 60, (YEL if i == 1 else WHITE) + (255,))
        gx = (pw - ti.width - 90) // 2
        if lang == "ar":
            pill.alpha_composite(ti, (gx, 18)); pill.alpha_composite(ck, (gx + ti.width + 20, (pill.height - 70) // 2))
        else:
            pill.alpha_composite(ck, (gx, (pill.height - 70) // 2)); pill.alpha_composite(ti, (gx + 90, 18))
        paste_c(im, pill, W / 2 + (1 - ease_out(p)) * (900 if i % 2 == 0 else -900), 820 + i * 180, 1.0)

def scene_cta(im, f, S, lang):
    lf = f - 315
    p0 = back(prog(lf, 0, 12))
    paste_c(im, text_img(S["cta"], 78, WHITE), W / 2, 700, p0, alpha=prog(lf, 0, 8))
    bw, bh = 940, 170
    bar = rrect((bw, bh), 85, (255, 255, 255, 255))
    d = ImageDraw.Draw(bar)
    kw = S["kw"]; n = int(round(len(kw) * prog(lf, 12, 36)))
    shown = kw[:n]
    ti = text_img(shown if shown else " ", 84, (25, 25, 45), maxw=700) if shown else None
    rtl = lang == "ar"
    # magnifier
    mx = bw - 95 if rtl else 95
    d.ellipse((mx - 34, 52, mx + 22, 108), outline=BLUE, width=12); d.line((mx + 14, 100, mx + 44, 130), fill=BLUE, width=14)
    cur_on = (lf // 8) % 2 == 0
    if ti:
        tx = (bw - 160 - ti.width) if rtl else 160
        bar.alpha_composite(ti, (int(tx), (bh - ti.height) // 2))
        cxp = tx - 8 if rtl else tx + ti.width + 4
    else:
        cxp = bw - 165 if rtl else 165
    if cur_on: d.rectangle((cxp, 45, cxp + 7, bh - 45), fill=BLUE)
    paste_c(im, bar, W / 2, 900, back(prog(lf, 4, 16)))
    # finger tap hint & app name
    p2 = back(prog(lf, 40, 54))
    paste_c(im, text_img("GIF Sticker", 110, YEL), W / 2, 1150, p2)
    paste_c(im, mini_sticker(0, f, lang), W / 2, 1420, 0.9 * p2, rot=6 * math.sin(lf / 5))

def frame(f, lang):
    S = L[lang]
    im = bg_frame(f)
    if f < 75:
        scene_hook(im, f, S)
        if f > 66:  # quick flash out
            a = prog(f, 66, 75); ov = Image.new("RGBA", (W, H), (255, 255, 255, int(120 * a))); im.alpha_composite(ov)
    elif f < 240: scene_phone(im, f, S, lang)
    elif f < 315: scene_feats(im, f, S, lang)
    else: scene_cta(im, f, S, lang)
    # brand tag
    tag = text_img("@gif_sticker", 40, (255, 255, 255, 150), path=F7)
    im.alpha_composite(tag, (60, 120))
    return im.convert("RGB")

# ---------- music (original, generated) ----------
def make_music(path):
    sr = 44100; n = int(sr * DUR); t = np.arange(n) / sr; out = np.zeros(n)
    bpm = 118; beat = 60 / bpm
    def env(length, dec): x = np.arange(int(sr * length)) / sr; return np.exp(-x * dec)
    for b in range(int(DUR / beat) + 1):
        st = int(b * beat * sr)
        k = env(0.25, 18); ph = 2 * np.pi * np.cumsum(55 + 90 * np.exp(-np.arange(len(k)) / sr * 30)) / sr
        seg = np.sin(ph) * k * 0.9; e = min(n, st + len(seg)); out[st:e] += seg[:e - st]
        for h in (0, 0.5):
            hs = int((b + h) * beat * sr + beat * 0.25 * sr * 0); hs = int((b * beat + h * beat + beat / 4) * sr)
            hh = np.random.randn(int(sr * 0.05)) * env(0.05, 80) * 0.18; e = min(n, hs + len(hh))
            if hs < n: out[hs:e] += hh[:e - hs]
        if b % 2 == 1:
            sn = np.random.randn(int(sr * 0.15)) * env(0.15, 25) * 0.35; e = min(n, st + len(sn)); out[st:e] += sn[:e - st]
    notes = [72, 76, 79, 81, 79, 76, 74, 76, 72, 76, 79, 84, 81, 79, 76, 79]
    for i in range(int(DUR / (beat / 2))):
        st = int(i * beat / 2 * sr); m = notes[i % len(notes)]; fr = 440 * 2 ** ((m - 69) / 12)
        ln = int(sr * 0.22); x = np.arange(ln) / sr
        seg = (np.sin(2 * np.pi * fr * x) + 0.4 * np.sin(4 * np.pi * fr * x)) * np.exp(-x * 14) * 0.22
        e = min(n, st + ln); out[st:e] += seg[:e - st]
    # pop sfx at sticker reveal (frame 203) and transitions
    for fr_ in (75, 203, 240, 315):
        st = int(fr_ / FPS * sr); ln = int(sr * 0.18); x = np.arange(ln) / sr
        seg = np.sin(2 * np.pi * (300 + 1500 * x / 0.18) * x) * np.exp(-x * 22) * 0.5
        e = min(n, st + ln); out[st:e] += seg[:e - st]
    out *= np.clip(np.minimum(t / 0.3, (DUR - t) / 0.8), 0, 1)
    out = out / np.max(np.abs(out)) * 0.8
    data = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())

def render(lang, out, texts=None, seed=0):
    """texts: optional dict overriding L[lang] keys (h1,h2,hs,steps,laugh,feats,cta,kw)."""
    if texts:
        L[lang] = dict(L.get(lang, L["en"]), **texts)
    np.random.seed(seed)
    wav = os.path.join(tempfile.gettempdir(), f"music_{lang}_{seed}.wav")
    make_music(wav)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(N): p.stdin.write(frame(f, lang).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode != 0: raise RuntimeError("ffmpeg failed")
    return out

if __name__ == "__main__":
    # python render.py <lang> <out.mp4> [texts.json]
    texts = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 else None
    print("done", render(sys.argv[1], sys.argv[2], texts))
