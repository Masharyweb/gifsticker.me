"""Copy the EXTENDED user token, then run: python meta_token.py"""
import json, subprocess, urllib.parse, urllib.request, urllib.error
V = "https://graph.facebook.com/v23.0"
def get(path, **p):
    try:
        return json.load(urllib.request.urlopen(f"{V}/{path}?" + urllib.parse.urlencode(p)))
    except urllib.error.HTTPError as e:
        print("\nFACEBOOK ERROR:", e.read().decode("utf-8", "replace")); raise SystemExit(1)
tok = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True).stdout.strip()
print("token length:", len(tok), "starts:", tok[:3])
print("user:", get("me", fields="name", access_token=tok).get("name"))
perms = get("me/permissions", access_token=tok)["data"]
print("permissions:", ", ".join(x["permission"] for x in perms if x["status"] == "granted"))
pages = get("me/accounts", fields="id,name,access_token,instagram_business_account{id,username}", access_token=tok)["data"]
if not pages: print("NO PAGES: re-generate the token and tick the page + Instagram account")
for p in pages:
    ig = p.get("instagram_business_account") or {}
    print(f"\n== {p['name']} ==\nFB_PAGE_ID = {p['id']}\nFB_PAGE_TOKEN = {p['access_token']}\nIG_USER_ID = {ig.get('id')}  (@{ig.get('username')})")