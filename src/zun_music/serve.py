"""Listening page: every MP3 in a folder, with its .txt description and download links.

If ``<name>.mp4`` exists (see ``video.py``) the page embeds the video instead of a bare audio player.
Binds 0.0.0.0 so a phone on the same network can open it, and answers HTTP Range requests, which
iOS Safari requires before it will play a <video>. New renders appear on refresh.
"""
from __future__ import annotations

import html
import re
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

_RANGE = re.compile(r"bytes=(\d*)-(\d*)$")


def render_page(folder: Path, title: str = "Arrangement versions") -> str:
    items = []
    for mp3 in sorted(folder.glob("*.mp3")):
        note = mp3.with_suffix(".txt")
        desc = html.escape(note.read_text(encoding="utf-8").strip()) if note.exists() else ""
        mp4, mid = mp3.with_suffix(".mp4"), mp3.with_suffix(".mid")
        links = [f'<a href="/files/{quote(mp3.name)}" download>MP3</a>']
        if mp4.exists():
            links.append(f'<a href="/files/{quote(mp4.name)}" download>Video (MP4)</a>')
        if mid.exists():
            links.append(f'<a href="/files/{quote(mid.name)}" download>MIDI</a>')
        player = (f'<video controls playsinline preload="metadata" src="/files/{quote(mp4.name)}"></video>'
                  if mp4.exists() else
                  f'<audio controls preload="metadata" src="/files/{quote(mp3.name)}"></audio>')
        items.append(f"<section><h2>{html.escape(mp3.stem)}</h2><p>{desc}</p>{player}"
                     f"<p class=dl>Download: {' · '.join(links)}</p></section>")
    body = "\n".join(items) or "<p>No renders yet.</p>"
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>
body{{font-family:-apple-system,sans-serif;max-width:640px;margin:auto;padding:16px;background:#faf8f5;color:#222}}
section{{background:#fff;border-radius:12px;padding:12px 16px;margin:14px 0;box-shadow:0 1px 3px #0002}}
h2{{font-size:17px;margin:4px 0}} p{{font-size:14px;line-height:1.5;color:#555}}
audio,video{{width:100%;border-radius:8px;background:#000}} .dl{{font-size:15px}} .dl a{{color:#b0413e;font-weight:600}}
</style></head><body><h1>{html.escape(title)}</h1>{body}
<script>document.addEventListener('play',e=>{{for(const a of document.querySelectorAll('audio,video'))if(a!==e.target)a.pause()}},true);</script>
</body></html>"""


def parse_range(header: str, size: int):
    """(start, end) inclusive for a single 'bytes=' range, None for no/unsupported range,
    or 'unsatisfiable'."""
    m = _RANGE.match((header or "").strip())
    if not m or not (m.group(1) or m.group(2)):
        return None
    if m.group(1):
        start = int(m.group(1))
        end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
    else:  # suffix form: bytes=-N
        start, end = max(0, size - int(m.group(2))), size - 1
    return (start, end) if start <= end else "unsatisfiable"


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
            self._send_file(unquote(self.path[len("/files/"):].split("?")[0]))
        else:
            self.send_error(404)

    def _send_file(self, name: str):
        root = Path(self.directory).resolve()
        path = (root / name).resolve()
        if path.parent != root or not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        rng = parse_range(self.headers.get("Range", ""), size)
        if rng == "unsatisfiable":
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        start, end = rng or (0, size - 1)
        self.send_response(206 if rng else 200)
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with path.open("rb") as fh:
            fh.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)


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


def make_server(folder, port: int = 8766, title: str = "Arrangement versions", host: str = "0.0.0.0"):
    folder = Path(folder).resolve()
    handler = type("Handler", (_Handler,), {"title": title})
    return ThreadingHTTPServer((host, port), partial(handler, directory=str(folder)))


def serve(folder, port: int = 8766, title: str = "Arrangement versions"):
    try:
        server = make_server(folder, port, title)
    except OSError as e:
        raise SystemExit(f"cannot bind port {port}: {e}. Another process may own it; pick another --port.")
    print(f"serving {Path(folder).resolve()} on http://{lan_address()}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
