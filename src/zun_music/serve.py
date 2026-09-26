"""Listening page: every MP3 in a folder, with its .txt description and .mid link.

Binds 0.0.0.0 so a phone on the same network can open it. New renders appear on refresh.
"""
from __future__ import annotations

import html
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


def render_page(folder: Path, title: str = "Arrangement versions") -> str:
    items = []
    for mp3 in sorted(folder.glob("*.mp3")):
        note = mp3.with_suffix(".txt")
        desc = html.escape(note.read_text(encoding="utf-8").strip()) if note.exists() else ""
        mid = mp3.with_suffix(".mid")
        link = f'<p class=small><a href="/files/{quote(mid.name)}">MIDI</a></p>' if mid.exists() else ""
        items.append(f"<section><h2>{html.escape(mp3.stem)}</h2><p>{desc}</p>"
                     f'<audio controls preload="metadata" src="/files/{quote(mp3.name)}"></audio>{link}</section>')
    body = "\n".join(items) or "<p>No renders yet.</p>"
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>
body{{font-family:-apple-system,sans-serif;max-width:640px;margin:auto;padding:16px;background:#faf8f5;color:#222}}
section{{background:#fff;border-radius:12px;padding:12px 16px;margin:14px 0;box-shadow:0 1px 3px #0002}}
h2{{font-size:17px;margin:4px 0}} p{{font-size:14px;line-height:1.5;color:#555}} audio{{width:100%}} .small{{font-size:12px}}
</style></head><body><h1>{html.escape(title)}</h1>{body}
<script>document.addEventListener('play',e=>{{for(const a of document.querySelectorAll('audio'))if(a!==e.target)a.pause()}},true);</script>
</body></html>"""


class _Handler(SimpleHTTPRequestHandler):
    title = "Arrangement versions"

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            data = render_page(Path(self.directory), self.title).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/files/"):
            self.path = self.path[len("/files"):]
            super().do_GET()
        else:
            self.send_error(404)


def lan_address() -> str:
    """Best-effort LAN IP (no packets are sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def serve(folder, port: int = 8766, title: str = "Arrangement versions"):
    folder = Path(folder).resolve()
    handler = type("Handler", (_Handler,), {"title": title})
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), partial(handler, directory=str(folder)))
    except OSError as e:
        raise SystemExit(f"cannot bind port {port}: {e}. Another process may own it; pick another --port.")
    print(f"serving {folder} on http://{lan_address()}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
