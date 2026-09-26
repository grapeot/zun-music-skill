"""Note names, chord qualities, bar validation and the strong-beat skeleton check."""
from __future__ import annotations

import re
from typing import Iterable, Optional, Sequence, Tuple

Note = Tuple[Optional[str], float]  # (note name or None for a rest, beats)
Bar = Sequence[Note]

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NOTE_RE = re.compile(r"^([A-G])([#b]?)(-?\d)$")

QUALITIES = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "sus4": (0, 5, 7),
    "7": (0, 4, 7, 10),
    "m7": (0, 3, 7, 10),
    "maj7": (0, 4, 7, 11),
}


def pitch(name: str) -> int:
    """'A5' -> 81, 'Bb4' -> 70, 'C#5' -> 73 (C4 = 60)."""
    m = _NOTE_RE.match(name)
    if not m:
        raise ValueError(f"bad note name {name!r}; expected e.g. 'C4', 'F#5', 'Bb3'")
    letter, acc, octave = m.groups()
    return 12 * (int(octave) + 1) + _PC[letter] + {"": 0, "#": 1, "b": -1}[acc]


def pitch_class(root: str) -> int:
    """'Bb' -> 10, 'F#' -> 6."""
    return pitch(root + "4") % 12


def chord_tones(quality: str) -> Tuple[int, ...]:
    if quality not in QUALITIES:
        raise ValueError(f"unknown chord quality {quality!r}; known: {sorted(QUALITIES)}")
    return QUALITIES[quality]


def bar_length_errors(bars: Sequence[Sequence[tuple]], beats_per_bar: float = 4,
                      allow_short_last: bool = True) -> list:
    """Return human-readable errors for bars whose durations do not sum to the meter.

    Works for melody bars ``(note, beats)`` and chord bars ``(root, quality, beats)``;
    the duration is always the last element.
    """
    errors = []
    for i, bar in enumerate(bars):
        total = sum(item[-1] for item in bar)
        last = i == len(bars) - 1
        if abs(total - beats_per_bar) < 1e-9:
            continue
        if last and allow_short_last and 0 < total < beats_per_bar:
            continue
        errors.append(f"bar {i + 1}: {total} beats, expected {beats_per_bar}")
    return errors


def sounding_at(bar: Bar, beat: float) -> Optional[int]:
    """MIDI pitch sounding at ``beat`` within the bar (None for a rest or past the end)."""
    t = 0.0
    for name, dur in bar:
        if t - 1e-9 <= beat < t + dur - 1e-9:
            return None if name is None else pitch(name)
        t += dur
    return None


def skeleton(melody: Sequence[Bar], strong_beats: Iterable[float] = (0, 2)) -> list:
    """[(bar_index, beat, pitch_class or None), ...] at every strong beat."""
    out = []
    for i, bar in enumerate(melody):
        for b in strong_beats:
            p = sounding_at(bar, b)
            out.append((i, b, None if p is None else p % 12))
    return out


def skeleton_mismatches(source: Sequence[Bar], arranged: Sequence[Bar],
                        allow: Iterable[Tuple[int, float]] = (),
                        strong_beats: Iterable[float] = (0, 2)) -> list:
    """Strong-beat positions where the arrangement's pitch class differs from the source.

    ``allow`` lists (bar_index, beat) positions that are deliberate departures.
    Octave changes are not mismatches.
    """
    if len(source) != len(arranged):
        return [("bar-count", len(source), len(arranged))]
    allowed = {(b, float(x)) for b, x in allow}
    strong = tuple(strong_beats)
    return [
        (bar, beat, s, a)
        for (bar, beat, s), (_, _, a) in zip(skeleton(source, strong), skeleton(arranged, strong))
        if s != a and (bar, float(beat)) not in allowed
    ]
