"""Build a translated copy of an English guide page.

  python tools/localize.py <page> <lang>
  e.g. python tools/localize.py video-to-sticker tr  ->  tr/video-to-sticker/index.html

Translations live in tools/i18n/<page>.<lang>.json as {"English text": "translation"}.
Only whole text nodes (>text<) and whole JSON/attribute strings ("text") are replaced,
so partial words are never touched. The English page gets the new hreflang link too.
"""
import json, re, sys, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://gifsticker.me"
PLAY_HL = {"tr": "tr", "ar": "ar", "es": "es", "pt": "pt-BR", "id": "id", "de": "de", "fr": "fr", "it": "it", "ru": "ru", "hi": "hi", "vi": "vi", "th": "th", "ms": "ms", "bn": "bn", "ur": "ur", "fa": "fa"}
HREFLANG = {"tr": "tr", "ar": "ar", "es": "es", "pt": "pt-BR", "id": "id", "de": "de", "fr": "fr", "it": "it", "ru": "ru", "hi": "hi", "vi": "vi", "th": "th", "ms": "ms", "bn": "bn", "ur": "ur", "fa": "fa"}


def localize(page, lang):
    src = os.path.join(ROOT, page, "index.html")
    t = open(src, encoding="utf-8").read()
    tr = {}
    common = os.path.join(ROOT, "tools", "i18n", f"common.{lang}.json")  # nav/footer shared by all pages
    if os.path.exists(common): tr.update(json.load(open(common, encoding="utf-8")))
    tr.update(json.load(open(os.path.join(ROOT, "tools", "i18n", f"{page}.{lang}.json"), encoding="utf-8")))
    missing = []
    for a, b in tr.pop("__raw__", {}).items():  # exact HTML fragments, e.g. words between two links
        t = t.replace(a, b)
    for en in sorted(tr, key=len, reverse=True):
        loc = tr[en]
        enc_html, loc_html = html.escape(en, quote=False), html.escape(loc, quote=False)
        n = 0
        for a, b in ((f">{enc_html}<", f">{loc_html}<"), (f">{en}<", f">{loc}<"),
                     (f'"{html.escape(en)}"', f'"{html.escape(loc)}"'), (f'"{en}"', f'"{json.dumps(loc, ensure_ascii=False)[1:-1]}"')):
            c = t.count(a)
            if c: t = t.replace(a, b); n += c
        if not n and t.count(f">{en} "):  # text followed by an inline link
            t = t.replace(f">{en} ", f">{loc} "); n = 1
        if not n: missing.append(en)
    url_en, url_loc = f"{SITE}/{page}/", f"{SITE}/{lang}/{page}/"
    t = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang}"' + (' dir="rtl"' if lang in ("ar", "ur", "fa") else ""), t, count=1)
    t = t.replace(f'<link rel="canonical" href="{url_en}">', f'<link rel="canonical" href="{url_loc}">')
    t = t.replace(f'<meta property="og:url" content="{url_en}">', f'<meta property="og:url" content="{url_loc}">')
    t = t.replace(f'"{url_en}"', f'"{url_loc}"').replace(f'"@id":"{url_en}', f'"@id":"{url_loc}')
    # hreflang block: en + x-default + this language
    alt = (f'<link rel="alternate" hreflang="en" href="{url_en}"><link rel="alternate" hreflang="{HREFLANG[lang]}" href="{url_loc}">'
           f'<link rel="alternate" hreflang="x-default" href="{url_en}">')
    t = re.sub(r'(<link rel="alternate" hreflang="[^"]+" href="[^"]+">)+', alt, t, count=1)
    t = t.replace(f"&amp;hl=en&amp;referrer=utm_source%3Dwebsite%26utm_medium%3Den%26utm_campaign%3D{page}",
                  f"&amp;hl={PLAY_HL[lang]}&amp;referrer=utm_source%3Dwebsite%26utm_medium%3D{lang}%26utm_campaign%3D{page}")
    # localized screenshots when they exist (s/shots/*-en.webp -> *-<lang>.webp)
    for m in set(re.findall(r'/s/shots/([a-z0-9-]+)-en\.webp', t)):
        if os.path.exists(os.path.join(ROOT, "s", "shots", f"{m}-{lang}.webp")):
            t = t.replace(f"/s/shots/{m}-en.webp", f"/s/shots/{m}-{lang}.webp")
    out = os.path.join(ROOT, lang, page, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(t)
    # add the new language to the English page's hreflang set
    e = open(src, encoding="utf-8").read()
    tag = f'<link rel="alternate" hreflang="{HREFLANG[lang]}" href="{url_loc}">'
    if tag not in e:
        e = e.replace(f'<link rel="alternate" hreflang="x-default"', tag + '<link rel="alternate" hreflang="x-default"', 1)
        open(src, "w", encoding="utf-8").write(e)
    print(out, "| untranslated:", missing or "none")


if __name__ == "__main__":
    localize(sys.argv[1], sys.argv[2])
