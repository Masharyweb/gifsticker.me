import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
PLAY = "https://play.google.com/store/apps/details?id=com.whatsappstickers.stickermakerforwhatsapp"
G = r"C:\AndroidProjects\gifsticker.me"; M = r"C:\AndroidProjects\Masharyweb.github.io"
CSS = "body{margin:0;font:17px/1.75 system-ui,Tahoma,sans-serif;background:#f6f8fc;color:#1a1d21}main{max-width:780px;margin:auto;padding:32px 16px}h1{font-size:30px;line-height:1.3}h2{margin-top:36px}a.btn{display:inline-block;background:#1a73e8;color:#fff;padding:14px 26px;border-radius:999px;text-decoration:none;font-weight:700}.v{position:relative;padding-top:56.25%;border-radius:14px;overflow:hidden;margin:24px 0}.v iframe{position:absolute;inset:0;width:100%;height:100%;border:0}details{background:#fff;border-radius:10px;padding:12px 16px;margin:8px 0}small{color:#6b7280}@media(prefers-color-scheme:dark){body{background:#111418;color:#e8eaed}details{background:#1b1f24}}"
def page(lang, d, url, title, desc, h1, body, faq, vid, cta, note, home, homelbl):
    ld = [{"@context":"https://schema.org","@type":"SoftwareApplication","name":"GIF Sticker Maker","alternateName":["Sticker Maker","ملصقات ستيكرات متحركة"],"operatingSystem":"Android","applicationCategory":"MultimediaApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"url":url,"downloadUrl":PLAY,"author":{"@type":"Person","name":"Mashary M. Mazeid","url":"https://masharyweb.site"}},
          {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}]
    f = "".join(f"<details><summary><b>{q}</b></summary><p>{a}</p></details>" for q,a in faq)
    return f'''<!doctype html><html lang="{lang}" dir="{d}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{url}"><meta property="og:type" content="website">
<style>{CSS}</style><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script></head><body><main>
<p><a href="{home}">{homelbl}</a></p><h1>{h1}</h1>{body}
<div class="v"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{h1}" loading="lazy" allowfullscreen></iframe></div>
<p><a class="btn" href="{PLAY}" rel="noopener">{cta}</a></p>{f}
<p><small>{note}</small></p></main></body></html>'''
EN_BODY = """<p>Most sticker apps hand you the same packs everyone else already has. This sticker maker works the other way round: you bring the moment, and it becomes a sticker. A clip from last night, your cat doing something ridiculous, a friend's face mid-laugh.</p>
<h2>What you can make</h2><ul><li><b>Animated stickers from video</b> – trim the exact second you want and set the speed from 0.5x to 2x.</li><li><b>GIF stickers</b> – search the built-in GIF library or use files from your phone.</li><li><b>Still stickers from photos</b> – AI removes the background in one tap.</li><li><b>Text and emoji</b> – 11 fonts, 18 colors, layers you can move and resize.</li></ul>
<h2>Five steps, about a minute</h2><ol><li>Tap + and start a new pack.</li><li>Pick a video, GIF or photo.</li><li>Trim it and adjust the speed.</li><li>Add text or emoji, remove the background if you like.</li><li>Tap Add and send it in your chats.</li></ol>
<p>No account, no watermark, and editing stays on your phone. Packs hold up to 30 stickers, either all still or all animated.</p>"""
EN_FAQ = [("Is this sticker maker free?","Yes. It is free to download and use, with no sign-up."),("Can I make animated stickers from my own videos?","Yes. Choose any video, keep the part you like, and it becomes an animated sticker."),("Does it work with WhatsApp?","Sticker packs can be added to messaging apps that support third-party stickers, including WhatsApp."),("How many stickers fit in one pack?","Up to 30. A pack is either still or animated.")]
EN_NOTE = "GIF Sticker Maker is independent and is not affiliated with or endorsed by WhatsApp LLC."
AR_BODY = """<p>أغلب تطبيقات الملصقات تعطيك نفس الحزم اللي عند الكل. هنا العكس: أنت تجيب اللحظة، والتطبيق يحوّلها ملصق. مقطع من سهرة البارحة، قطوتك وهي تسوي حركة غريبة، أو ضحكة صاحبك.</p>
<h2>وش تقدر تسوي؟</h2><ul><li><b>ملصقات متحركة من الفيديو</b>: تقص الثانية اللي تبيها، وتضبط السرعة من 0.5x إلى 2x.</li><li><b>ستيكرات GIF</b>: من مكتبة الجيف داخل التطبيق أو من ملفاتك.</li><li><b>ملصقات ثابتة من صورك</b>: والذكاء الاصطناعي يشيل الخلفية بضغطة.</li><li><b>كتابة وإيموجي</b>: 11 خط عربي و18 لون، وتحركها وتكبرها براحتك.</li></ul>
<h2>خمس خطوات، تقريباً دقيقة</h2><ol><li>اضغط + وابدأ حزمة جديدة.</li><li>اختر فيديو أو جيف أو صورة.</li><li>قص المقطع واضبط السرعة.</li><li>اكتب كلمتك أو حط إيموجي، وشيل الخلفية لو تبي.</li><li>اضغط إضافة وأرسله في محادثاتك.</li></ol>
<p>بدون حساب، وبدون علامة مائية، وكل التعديل يصير في جوالك. والحزمة فيها لين 30 ملصق، كلها ثابتة أو كلها متحركة.</p>"""
AR_FAQ = [("هل صانع الملصقات مجاني؟","إيه، مجاني بالكامل وبدون تسجيل."),("أقدر أسوي ملصقات متحركة من فيديوهاتي؟","إيه، اختر أي فيديو واحتفظ بالجزء اللي يعجبك، ويتحول لملصق متحرك."),("يشتغل مع واتساب؟","تقدر تضيف الحزم لتطبيقات المراسلة اللي تدعم الملصقات، ومنها واتساب."),("كم ملصق في الحزمة؟","لين 30، والحزمة إما ثابتة أو متحركة.")]
AR_NOTE = "التطبيق مستقل وغير تابع لشركة WhatsApp LLC ولا معتمد منها."
P = [
 (G, "sticker-maker/index.html", "https://gifsticker.me/sticker-maker/", page("en","ltr","https://gifsticker.me/sticker-maker/","Sticker Maker – Animated Stickers from Video & GIF | GIF Sticker","Free sticker maker for Android: turn videos, GIFs and photos into animated or still stickers with text, emoji and AI background removal.","Sticker Maker: turn your own moments into stickers",EN_BODY,EN_FAQ,"Y9fuI6Mxz4Q","Get Sticker Maker on Google Play",EN_NOTE,"/","← GIF Sticker home"), "index.html", "Sticker Maker", "ltr"),
 (G, "ar/sticker-maker/index.html", "https://gifsticker.me/ar/sticker-maker/", page("ar","rtl","https://gifsticker.me/ar/sticker-maker/","صانع ملصقات ستيكرات متحركة من الفيديو و GIF | Sticker Maker","صانع ملصقات مجاني للأندرويد: حوّل فيديوهاتك وصورك وملفات GIF إلى ستيكرات متحركة وثابتة بخط عربي وإيموجي.","صانع الملصقات: لحظاتك أنت تصير ستيكرات",AR_BODY,AR_FAQ,"1egx5M_MlDQ","حمّل صانع الملصقات من Google Play",AR_NOTE,"/ar/","→ الرئيسية"), "ar/index.html", "صانع الملصقات Sticker Maker", "rtl"),
 (M, "sticker-maker.html", "https://masharyweb.site/sticker-maker.html", page("en","ltr","https://masharyweb.site/sticker-maker.html","Sticker Maker by Mashary M. Mazeid – GIF Sticker for Android","Sticker Maker, an Android app built by Mashary M. Mazeid: make animated stickers from videos, GIFs and photos.","Sticker Maker – a project by masharyweb","<p>I built Sticker Maker (GIF Sticker) because I wanted stickers of my own people and moments, not generic packs. Here is what it does.</p>"+EN_BODY,EN_FAQ,"Y9fuI6Mxz4Q","Get it on Google Play",EN_NOTE+" Official site: https://gifsticker.me","/","← masharyweb.site"), "index.html", "Sticker Maker app", "ltr"),
]
for root, rel, url, html, home, lbl, d in P:
    fp = os.path.join(root, rel); os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf-8").write(html); print("صفحة:", url)
    hp = os.path.join(root, home)
    if os.path.exists(hp):
        t = open(hp, encoding="utf-8").read()
        t = re.sub(r"<!--G4S-SM-->.*?<!--/G4S-SM-->", "", t, flags=re.S)
        link = f'<!--G4S-SM--><p dir="{d}" style="text-align:center;margin:24px 0"><a href="{url}">{lbl}</a></p><!--/G4S-SM-->'
        m = re.search(r"<footer", t, re.I) or re.search(r"</body>", t, re.I)
        t = t[:m.start()] + link + "\n" + t[m.start():]; open(hp, "w", encoding="utf-8").write(t); print("رابط في:", home)
    sm = os.path.join(root, "sitemap.xml")
    if os.path.exists(sm):
        s = open(sm, encoding="utf-8").read()
        if url not in s:
            s = s.replace("</urlset>", f"<url><loc>{url}</loc><lastmod>2026-10-22</lastmod></url>\n</urlset>"); open(sm, "w", encoding="utf-8").write(s); print("sitemap:", url)