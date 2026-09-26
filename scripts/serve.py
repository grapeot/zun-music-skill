"""Serve a listening page for every MP3 in a folder (default: out/), reachable from the LAN.

    python scripts/serve.py [folder] [--port 8766]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from zun_music.serve import serve  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default=str(ROOT / "out"))
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--title", default="Arrangement versions")
    a = ap.parse_args()
    Path(a.folder).mkdir(parents=True, exist_ok=True)
    serve(a.folder, a.port, a.title)
