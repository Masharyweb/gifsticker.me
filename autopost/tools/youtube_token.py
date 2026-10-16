"""Run on your PC once: python youtube_token.py <CLIENT_ID> <CLIENT_SECRET>
Opens the browser, you approve @gif_sticker, it prints the REFRESH TOKEN."""
import sys, json, urllib.parse, urllib.request, http.server, webbrowser
cid, sec = sys.argv[1], sys.argv[2]
REDIR = "http://127.0.0.1:8765/"
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(dict(
    client_id=cid, redirect_uri=REDIR, response_type="code", access_type="offline", prompt="consent",
    scope="https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"))
code = {}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code["c"] = q.get("code", [""])[0]
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK - return to PowerShell")
    def log_message(self, *a): pass
webbrowser.open(url); print("Browser opened. If not, open:\n" + url)
http.server.HTTPServer(("127.0.0.1", 8765), H).handle_request()
data = urllib.parse.urlencode(dict(code=code["c"], client_id=cid, client_secret=sec, redirect_uri=REDIR, grant_type="authorization_code")).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
print("\nYT_REFRESH_TOKEN =", tok.get("refresh_token", tok))
