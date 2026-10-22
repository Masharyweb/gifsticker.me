import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
CH = "https://www.youtube.com/@gif_sticker"
P = {"index.html": ("Y9fuI6Mxz4Q", "Watch how it works", "Subscribe on YouTube", "GIF Sticker Maker - Animated stickers from any video", "ltr"),
     "ar/index.html": ("1egx5M_MlDQ", "شاهد طريقة العمل", "اشترك في القناة", "صانع ملصقات متحركة GIF من الفيديو - GIF Sticker", "rtl")}
for f, (vid, h, sub, name, d) in P.items():
    fp = os.path.join(R, f)
    if not os.path.exists(fp): print("مو موجود:", f); continue
    t = open(fp, encoding="utf-8").read()
    t = re.sub(r"<!--G4S-VIDEO-->.*?<!--/G4S-VIDEO-->", "", t, flags=re.S)
    box = f'''<!--G4S-VIDEO--><section id="video" dir="{d}" style="max-width:960px;margin:48px auto;padding:0 16px;text-align:center">
<h2>{h}</h2>
<div style="position:relative;padding-top:56.25%;border-radius:16px;overflow:hidden">
<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{name}" loading="lazy" allow="encrypted-media; picture-in-picture" allowfullscreen style="position:absolute;inset:0;width:100%;height:100%;border:0"></iframe></div>
<p><a href="{CH}?sub_confirmation=1" target="_blank" rel="noopener" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#FF0000;color:#fff;border-radius:999px;text-decoration:none;font-weight:700">▶ {sub}</a></p>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"VideoObject","name":"{name}","description":"{name}","thumbnailUrl":"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg","uploadDate":"2026-10-21","embedUrl":"https://www.youtube.com/embed/{vid}","contentUrl":"https://www.youtube.com/watch?v={vid}"}}</script>
</section><!--/G4S-VIDEO-->'''
    m = re.search(r"<footer", t, re.I) or re.search(r"</body>", t, re.I)
    t = t[:m.start()] + box + "\n" + t[m.start():]
    if CH not in t.split("<!--G4S-VIDEO-->")[0] + t.split("<!--/G4S-VIDEO-->")[-1]:
        pass
    open(fp, "w", encoding="utf-8").write(t); print("تم:", f)