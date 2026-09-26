"""Render MIDI to MP3 with FluidSynth + ffmpeg."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

SOUNDFONT_ENV = "ZUN_MUSIC_SOUNDFONT"


class RenderError(RuntimeError):
    pass


def resolve_soundfont(path: Optional[str] = None) -> Path:
    candidate = path or os.environ.get(SOUNDFONT_ENV)
    if not candidate:
        raise RenderError(f"no SoundFont given: pass --soundfont or set {SOUNDFONT_ENV}")
    sf = Path(candidate).expanduser()
    if not sf.is_file():
        raise RenderError(f"SoundFont not found: {sf}")
    with sf.open("rb") as f:
        head = f.read(12)
    if head[:4] != b"RIFF" or head[8:12] != b"sfbk":
        raise RenderError(f"{sf} is not a SoundFont 2 file (header {head!r}); "
                          "a download may have returned an HTML challenge page instead")
    return sf


def _run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError(f"command failed ({proc.returncode}): {' '.join(map(str, cmd))}\n"
                          f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc


def render(midi_path, mp3_path, soundfont: Optional[str] = None, gain: float = 0.5,
           keep_wav: bool = False) -> Path:
    """MIDI -> WAV (FluidSynth) -> trimmed, loudness-normalised MP3 (ffmpeg)."""
    for tool in ("fluidsynth", "ffmpeg"):
        if shutil.which(tool) is None:
            raise RenderError(f"{tool} not found on PATH")
    sf = resolve_soundfont(soundfont)
    mp3 = Path(mp3_path)
    mp3.parent.mkdir(parents=True, exist_ok=True)
    wav = mp3.with_suffix(".wav")
    try:
        _run(["fluidsynth", "-ni", "-g", str(gain), "-r", "44100", "-F", str(wav), str(sf), str(midi_path)])
        # trim trailing silence only (reverse, strip leading silence, reverse back), then normalise
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af",
              "areverse,silenceremove=start_periods=1:start_threshold=-60dB,areverse,loudnorm=I=-16",
              "-b:a", "192k", str(mp3)])
    finally:
        if not keep_wav and wav.exists():
            wav.unlink()
    return mp3
