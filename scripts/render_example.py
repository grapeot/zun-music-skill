"""Build an example arrangement to MIDI and (optionally) render it to MP3.

    python scripts/render_example.py songbie --soundfont /path/to/neothfont.sf2
    python scripts/render_example.py songbie --midi-only

Writes <out>/<name>.mid, <name>.mp3 and <name>.txt (the description shown on the listening page).
"""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from zun_music.arrange import build_song  # noqa: E402
from zun_music.render import RenderError, render  # noqa: E402


def load_example(name: str):
    path = ROOT / "examples" / f"{name}.py"
    if not path.exists():
        known = sorted(p.stem for p in (ROOT / "examples").glob("*.py"))
        sys.exit(f"no example {name!r}; available: {known}")
    spec = importlib.util.spec_from_file_location(f"examples.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ARRANGEMENT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("example")
    ap.add_argument("--soundfont", help="path to .sf2 (default: $ZUN_MUSIC_SOUNDFONT)")
    ap.add_argument("--out", default=str(ROOT / "out"))
    ap.add_argument("--name", help="output file stem (default: example name)")
    ap.add_argument("--note", help="one-line description for the listening page (default: the arrangement's)")
    ap.add_argument("--midi-only", action="store_true", help="build + check only, no audio")
    args = ap.parse_args()

    arr = load_example(args.example)
    stem = args.name or args.example
    out = Path(args.out)
    try:
        song = build_song(arr)  # runs check(); raises on structural or skeleton problems
    except ValueError as e:
        sys.exit(f"arrangement check failed: {e}")
    mid = song.save(out / f"{stem}.mid")
    (out / f"{stem}.txt").write_text(args.note or arr.description, encoding="utf-8")
    seconds = song.length_beats() * 60 / arr.bpm
    print(f"midi: {mid} ({seconds:.1f}s)")
    if args.midi_only:
        return
    try:
        mp3 = render(mid, out / f"{stem}.mp3", args.soundfont)
    except RenderError as e:
        sys.exit(f"render failed: {e}")
    print(f"mp3:  {mp3}")


if __name__ == "__main__":
    main()
