"""GIF Sticker social factory: renders a short video and publishes it to YouTube / Instagram / Facebook.
Runs hourly on GitHub Actions. Usage:
  python autopost/autopost.py run            # post today's slot if due
  python autopost/autopost.py run --dry-run  # render + print, no posting
  python autopost/autopost.py fonts          # build Cairo fonts (needs npm)
Secrets (env): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, FB_PAGE_ID, FB_PAGE_TOKEN, IG_USER_ID, [IG_TOKEN], [GRAPH_VER]
"""
import os, sys, json, time, glob, subprocess, tempfile, datetime as dt
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content.json")
STATE = os.path.join(HERE, "state.json")
QUEUE = os.path.join(HERE, "queue.json")
FONT_DIR = os.path.join(HERE, "fonts")
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VER", "v23.0")
RUPLOAD_VER = os.environ.get("GRAPH_VER", "v23.0")
PLAY = "https://play.google.com/store/apps/details?id=com.whatsappstickers.stickermakerforwhatsapp"
MAX_ATTEMPTS = 3

def jload(p, default):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return default

def jsave(p, data):
    with open(p, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------- fonts ----------------
def build_fonts():
    if os.path.exists(os.path.join(FONT_DIR, "Cairo-900.ttf")): return
    from fontTools.ttLib import TTFont
    from fontTools.merge import Merger
    tmp = tempfile.mkdtemp()
    subprocess.run(["npm", "pack", "@fontsource/cairo", "--silent"], cwd=tmp, check=True)
    tgz = glob.glob(os.path.join(tmp, "*.tgz"))[0]
    subprocess.run(["tar", "xzf", tgz], cwd=tmp, check=True)
    files = os.path.join(tmp, "package", "files")
    os.makedirs(FONT_DIR, exist_ok=True)
    for w in ("700", "900"):
        parts = []
        for sub in ("arabic", "latin", "latin-ext"):
            f = TTFont(os.path.join(files, f"cairo-{sub}-{w}-normal.woff")); f.flavor = None
            p = os.path.join(tmp, f"{sub}-{w}.ttf"); f.save(p); parts.append(p)
        Merger().merge(parts).save(os.path.join(FONT_DIR, f"Cairo-{w}.ttf"))
    print("fonts ok")

# ---------------- plan ----------------
def todays_plan(now):
    c = jload(CONTENT, None)
    today = now.date()
    start = dt.date.fromisoformat(c["start_date"])
    if today < start: return None, f"before start_date {start}"
    key = today.isoformat()
    idx = (today - start).days
    lang = c["order"][idx % len(c["order"])]
    L = c["langs"][lang]
    var = L["variants"][(idx // len(c["order"])) % len(L["variants"])]
    plan = dict(key=key, lang=lang, texts={k: var[k] for k in ("h1", "h2", "hs", "laugh") if k in var},
                title=var["title"], caption=var["caption"], cta_line=L["cta_line"], hashtags=L["hashtags"],
                tags=L["tags"], networks=c["networks"][lang], hour=c["post_hour_utc"][lang], seed=idx)
    q = jload(QUEUE, {}).get(key)  # manual override for this date
    if q:
        if "lang" in q and q["lang"] != lang:
            L = c["langs"][q["lang"]]
            plan.update(lang=q["lang"], cta_line=L["cta_line"], hashtags=L["hashtags"], tags=L["tags"],
                        networks=c["networks"][q["lang"]], hour=c["post_hour_utc"][q["lang"]])
        plan.update({k: v for k, v in q.items() if k != "lang"})
    if now.hour < plan["hour"]: return None, f"{key} {plan['lang']}: waits until {plan['hour']:02d}:00 UTC"
    return plan, "due"

def text_for(plan):
    return f"{plan['caption']}\n{plan['cta_line']}\n\n{plan['hashtags']}"

# ---------------- YouTube ----------------
def yt_upload(video, plan):
    tok = requests.post("https://oauth2.googleapis.com/token", data=dict(
        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
        refresh_token=os.environ["YT_REFRESH_TOKEN"], grant_type="refresh_token"), timeout=60).json()
    if "access_token" not in tok: raise RuntimeError(f"youtube token: {tok}")
    h = {"Authorization": "Bearer " + tok["access_token"]}
    desc = text_for(plan) + f"\n\n🌐 https://gifsticker.me\n📲 {PLAY}"
    meta = {"snippet": {"title": plan["title"][:100], "description": desc[:4900], "tags": plan["tags"],
                        "categoryId": "26", "defaultLanguage": plan["lang"], "defaultAudioLanguage": "zxx"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}}
    size = os.path.getsize(video)
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**h, "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      data=json.dumps(meta), timeout=60)
    if r.status_code >= 300: raise RuntimeError(f"youtube init {r.status_code}: {r.text[:300]}")
    with open(video, "rb") as f:
        r2 = requests.put(r.headers["Location"], headers={**h, "Content-Type": "video/mp4"}, data=f, timeout=600)
    if r2.status_code >= 300: raise RuntimeError(f"youtube upload {r2.status_code}: {r2.text[:300]}")
    return {"id": r2.json()["id"], "url": "https://youtube.com/shorts/" + r2.json()["id"]}

# ---------------- Instagram Reels (resumable binary upload) ----------------
def ig_upload(video, plan):
    ig, token = os.environ["IG_USER_ID"], os.environ.get("IG_TOKEN") or os.environ["FB_PAGE_TOKEN"]
    r = requests.post(f"{GRAPH}/{ig}/media", data=dict(media_type="REELS", upload_type="resumable",
                      caption=text_for(plan), share_to_feed="true", access_token=token), timeout=60).json()
    if "id" not in r: raise RuntimeError(f"ig container: {r}")
    cid, size = r["id"], os.path.getsize(video)
    with open(video, "rb") as f:
        u = requests.post(f"https://rupload.facebook.com/ig-api-upload/{RUPLOAD_VER}/{cid}",
                          headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, data=f, timeout=600)
    if u.status_code >= 300: raise RuntimeError(f"ig upload {u.status_code}: {u.text[:300]}")
    for _ in range(60):
        s = requests.get(f"{GRAPH}/{cid}", params=dict(fields="status_code,status", access_token=token), timeout=60).json()
        if s.get("status_code") == "FINISHED": break
        if s.get("status_code") == "ERROR": raise RuntimeError(f"ig processing: {s}")
        time.sleep(10)
    else: raise RuntimeError("ig processing timeout")
    p = requests.post(f"{GRAPH}/{ig}/media_publish", data=dict(creation_id=cid, access_token=token), timeout=60).json()
    if "id" not in p: raise RuntimeError(f"ig publish: {p}")
    return {"id": p["id"]}

# ---------------- Facebook Reels ----------------
def fb_upload(video, plan):
    page, token = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    s = requests.post(f"{GRAPH}/{page}/video_reels", data=dict(upload_phase="start", access_token=token), timeout=60).json()
    if "video_id" not in s: raise RuntimeError(f"fb start: {s}")
    vid, size = s["video_id"], os.path.getsize(video)
    with open(video, "rb") as f:
        u = requests.post(f"https://rupload.facebook.com/video-upload/{RUPLOAD_VER}/{vid}",
                          headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, data=f, timeout=600)
    if u.status_code >= 300: raise RuntimeError(f"fb upload {u.status_code}: {u.text[:300]}")
    fin = requests.post(f"{GRAPH}/{page}/video_reels", data=dict(upload_phase="finish", video_id=vid, video_state="PUBLISHED",
                        description=text_for(plan), access_token=token), timeout=60).json()
    if not fin.get("success"): raise RuntimeError(f"fb finish: {fin}")
    return {"id": vid}

UPLOADERS = {"youtube": yt_upload, "instagram": ig_upload, "facebook": fb_upload}

# ---------------- main ----------------
def run(dry=False):
    now = dt.datetime.fromisoformat(os.environ["FAKE_NOW"]) if os.environ.get("FAKE_NOW") else dt.datetime.now(dt.timezone.utc)
    plan, why = todays_plan(now)
    print("plan:", why)
    if not plan: return 0
    state = jload(STATE, {})
    rec = state.setdefault(plan["key"], {"lang": plan["lang"], "title": plan["title"]})
    todo = [n for n in plan["networks"]
            if not rec.get(n, {}).get("ok") and rec.get(n, {}).get("attempts", 0) < MAX_ATTEMPTS]
    if not todo and not dry: print("nothing to do"); return 0
    build_fonts()
    os.environ["FONT_DIR"] = FONT_DIR
    sys.path.insert(0, HERE)
    import render
    video = os.path.join(tempfile.gettempdir(), f"{plan['key']}_{plan['lang']}.mp4")
    if not os.path.exists(video):
        render.render(plan["lang"], video, plan["texts"], seed=plan["seed"])
    print("video:", video, os.path.getsize(video), "bytes")
    if dry:
        print(json.dumps({k: plan[k] for k in ("key", "lang", "title", "networks")}, ensure_ascii=False))
        print(text_for(plan)); return 0
    failed = 0
    for n in todo:
        r = rec.setdefault(n, {"attempts": 0})
        r["attempts"] = r.get("attempts", 0) + 1
        try:
            r.update(UPLOADERS[n](video, plan), ok=True, at=now.isoformat(timespec="minutes")); r.pop("error", None)
            print(f"{n}: OK {r.get('id')}")
        except Exception as e:
            r["error"] = str(e)[:500]; failed += 1
            print(f"{n}: FAIL {e}")
        jsave(STATE, state)
    return 1 if failed else 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "fonts": build_fonts()
    else: sys.exit(run(dry="--dry-run" in sys.argv))
