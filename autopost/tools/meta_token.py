"""Run on your PC once: python meta_token.py <APP_ID> <APP_SECRET> <SHORT_USER_TOKEN>
Prints FB_PAGE_ID, FB_PAGE_TOKEN (non-expiring) and IG_USER_ID for each page."""
import sys, json, urllib.parse, urllib.request
V = "https://graph.facebook.com/v23.0"
app, sec, short = sys.argv[1:4]
def get(path, **p): return json.load(urllib.request.urlopen(f"{V}/{path}?" + urllib.parse.urlencode(p)))
long_user = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app, client_secret=sec, fb_exchange_token=short)["access_token"]
pages = get("me/accounts", fields="id,name,access_token,instagram_business_account{id,username}", access_token=long_user)["data"]
for p in pages:
    ig = p.get("instagram_business_account") or {}
    print(f"\n== {p['name']} ==\nFB_PAGE_ID = {p['id']}\nFB_PAGE_TOKEN = {p['access_token']}\nIG_USER_ID = {ig.get('id')}  (@{ig.get('username')})")
