"""Render an MP3 into a small EQ-meter video (H.265 + AAC in MP4), e.g. for sharing to a phone.

The picture is a 24-band LED level meter with peak hold and a one-line title. Frames are drawn with
Pillow and piped to ffmpeg; the encode is tagged ``hvc1`` so iOS/macOS players accept it.
Requires the ``video`` extra (numpy, Pillow) and ffmpeg built with libx265.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Sequence

from .render import RenderError

W, H, FPS, SR = 640, 360, 30, 44100
BANDS, SEGS = 24, 18
BG, CELL, TEXT, PEAK = (18, 14, 24), (34, 28, 44), (225, 215, 235), (240, 235, 250)
# Fonts tried in order for the title; the first that exists wins (CJK-capable ones first).
FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _deps():
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise RenderError(f"video rendering needs the 'video' extra: pip install -e '.[video]' ({e})")
    return np, Image, ImageDraw, ImageFont


def band_levels(samples, sr: int = SR, fps: int = FPS, bands: int = BANDS, range_db: float = 48.0):
    """Per-frame levels for ``bands`` log-spaced bands (50 Hz–12 kHz), normalised to [0, 1].

    The top of the scale is the 99.5th percentile over the whole clip, so the meter uses its full
    height regardless of mastering loudness.
    """
    np = _deps()[0]
    x = np.asarray(samples, dtype=np.float32)
    hop, n = sr // fps, 4096
    frames = max(1, int(np.ceil(len(x) / hop)))
    x = np.pad(x, (n // 2, n))
    win = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    edges = np.geomspace(50, min(12000, sr / 2 - 1), bands + 1)
    idx = [np.where((freqs >= lo) & (freqs < hi))[0] for lo, hi in zip(edges[:-1], edges[1:])]
    out = np.zeros((frames, bands))
    for f in range(frames):
        spec = np.abs(np.fft.rfft(x[f * hop:f * hop + n] * win))
        out[f] = [spec[i].mean() if len(i) else 0.0 for i in idx]
    db = 20 * np.log10(out + 1e-9)
    top = np.percentile(db, 99.5)
    return np.clip((db - (top - range_db)) / range_db, 0, 1)


def _segment_color(k: int):
    r = k / (SEGS - 1)
    return (60, 200, 110) if r < .6 else (235, 190, 70) if r < .85 else (230, 70, 70)


def _font(ImageFont, font_path: Optional[str], size: int = 18):
    for cand in ([font_path] if font_path else []) + list(FONT_CANDIDATES):
        if cand and Path(cand).is_file():
            return ImageFont.truetype(cand, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def frames(levels, title: str = "", font_path: Optional[str] = None):
    """Yield RGB frames (bytes, W×H×3) for the given per-frame band levels."""
    np, Image, ImageDraw, ImageFont = _deps()
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    if title:
        d.text((20, 14), title, font=_font(ImageFont, font_path), fill=TEXT)
    x0, x1, y0, y1 = 24, W - 24, 56, H - 24
    bands = levels.shape[1]
    bw, sh = (x1 - x0) / bands, (y1 - y0) / SEGS
    for b in range(bands):
        for k in range(SEGS):
            bx, by = x0 + b * bw + 2, y1 - (k + 1) * sh + 2
            d.rectangle([bx, by, bx + bw - 4, by + sh - 4], fill=CELL)
    shown = np.zeros(bands)
    peak = np.zeros(bands)
    hold = np.zeros(bands)
    for lv in levels:
        shown = np.maximum(lv, shown - 0.06)            # fast attack, slow release
        rising = shown >= peak
        hold = np.where(rising, 18, hold - 1)            # hold the peak ~0.6 s, then let it fall
        peak = np.where(rising, shown, np.where(hold > 0, peak, np.maximum(shown, peak - 0.02)))
        img = base.copy()
        d = ImageDraw.Draw(img)
        for b in range(bands):
            bx = x0 + b * bw + 2
            for k in range(int(round(shown[b] * SEGS))):
                by = y1 - (k + 1) * sh + 2
                d.rectangle([bx, by, bx + bw - 4, by + sh - 4], fill=_segment_color(k))
            pk = min(SEGS - 1, int(round(peak[b] * SEGS)))
            if pk > 0:
                by = y1 - (pk + 1) * sh + 2
                d.rectangle([bx, by + sh * .35, bx + bw - 4, by + sh * .65], fill=PEAK)
        yield img.tobytes()


def _decode(mp3) -> "object":
    np = _deps()[0]
    proc = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mp3), "-f", "f32le", "-ac", "1",
                           "-ar", str(SR), "-"], capture_output=True)
    if proc.returncode != 0:
        raise RenderError(f"ffmpeg could not decode {mp3}:\n{proc.stderr.decode(errors='replace')}")
    return np.frombuffer(proc.stdout, dtype=np.float32)


def render_video(mp3_path, mp4_path=None, title: str = "", font_path: Optional[str] = None,
                 crf: int = 28) -> Path:
    """MP3 -> MP4 (640x360, 30 fps, H.265/hvc1 + AAC 160k) with an EQ-meter picture."""
    if shutil.which("ffmpeg") is None:
        raise RenderError("ffmpeg not found on PATH")
    mp3 = Path(mp3_path)
    mp4 = Path(mp4_path) if mp4_path else mp3.with_suffix(".mp4")
    levels = band_levels(_decode(mp3))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(mp3), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx265", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
           "-x265-params", "log-level=error", "-c:a", "aac", "-b:a", "160k", "-shortest",
           "-movflags", "+faststart", str(mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for frame in frames(levels, title, font_path):
            proc.stdin.write(frame)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode(errors="replace")
    if proc.wait() != 0:
        raise RenderError(f"ffmpeg video encode failed (is it built with libx265?):\n{err}")
    return mp4


def title_from(stem: str, description: str = "", max_len: int = 40) -> str:
    """'songbie · <first clause of the description>' trimmed to fit the frame."""
    head = description.strip()
    for sep in (":", "：", ".", "。", ";", "；"):
        head = head.split(sep)[0]
    head = head.strip()
    text = f"{stem}  ·  {head}" if head else stem
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def render_folder(folder, names: Sequence[str] = (), force: bool = False) -> list:
    """Render videos for MP3s in ``folder`` that lack an up-to-date MP4; returns written paths."""
    folder = Path(folder)
    targets = [folder / f"{n}.mp3" for n in names] if names else sorted(folder.glob("*.mp3"))
    written = []
    for mp3 in targets:
        mp4 = mp3.with_suffix(".mp4")
        if mp4.exists() and not force and mp4.stat().st_mtime >= mp3.stat().st_mtime:
            continue
        note = mp3.with_suffix(".txt")
        desc = note.read_text(encoding="utf-8") if note.exists() else ""
        written.append(render_video(mp3, mp4, title_from(mp3.stem, desc)))
    return written
