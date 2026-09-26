"""Render an EQ-meter MP4 for every MP3 in a folder that lacks an up-to-date one.

    python scripts/make_videos.py [folder] [--force] [--name NAME ...]

Needs the video extra (pip install -e '.[video]') and ffmpeg with libx265.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from zun_music.render import RenderError  # noqa: E402
from zun_music.video import render_folder  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default=str(ROOT / "out"))
    ap.add_argument("--name", action="append", default=[], help="only this stem (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-render even if the MP4 is newer than the MP3")
    a = ap.parse_args()
    try:
        written = render_folder(a.folder, a.name, a.force)
    except RenderError as e:
        sys.exit(f"video render failed: {e}")
    for p in written:
        print(f"mp4:  {p}")
    if not written:
        print("nothing to do (all videos up to date)")
