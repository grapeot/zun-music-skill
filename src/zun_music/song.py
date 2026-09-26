"""Minimal multi-track container that writes a type-1 MIDI file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import mido

TPB = 480
DRUM_CHANNEL = 9


@dataclass
class Track:
    program: int
    channel: int
    notes: List[Tuple[float, float, int, int]] = field(default_factory=list)  # start, dur, pitch, vel
    events: List[Tuple[float, mido.Message]] = field(default_factory=list)
    controls: List[Tuple[int, int]] = field(default_factory=list)  # CCs sent at t=0


class Song:
    def __init__(self, bpm: float, beats_per_bar: int = 4):
        self.bpm = bpm
        self.beats_per_bar = beats_per_bar
        self.tracks: Dict[str, Track] = {}

    def track(self, name: str, program: int, channel: int) -> Track:
        tr = self.tracks.get(name)
        if tr is None:
            tr = self.tracks[name] = Track(program, channel)
        elif (tr.program, tr.channel) != (program, channel):
            raise ValueError(f"track {name!r} already uses program {tr.program} on channel {tr.channel}")
        return tr

    def note(self, name: str, program: int, channel: int, start: float, dur: float, pitch: int, vel: int):
        if not 0 <= pitch <= 127:
            raise ValueError(f"pitch {pitch} out of MIDI range on track {name!r}")
        self.track(name, program, channel).notes.append((start, dur, pitch, max(1, min(127, vel))))

    def event(self, name: str, program: int, channel: int, start: float, msg: mido.Message):
        self.track(name, program, channel).events.append((start, msg))

    def length_beats(self) -> float:
        return max((s + d for tr in self.tracks.values() for s, d, _, _ in tr.notes), default=0.0)

    def to_midi(self) -> mido.MidiFile:
        mid = mido.MidiFile(ticks_per_beat=TPB)
        meta = mido.MidiTrack()
        meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm), time=0))
        meta.append(mido.MetaMessage("time_signature", numerator=self.beats_per_bar, denominator=4, time=0))
        mid.tracks.append(meta)
        for name, tr in self.tracks.items():
            mt = mido.MidiTrack()
            mt.append(mido.MetaMessage("track_name", name=name, time=0))
            if tr.channel != DRUM_CHANNEL:
                mt.append(mido.Message("program_change", program=tr.program, channel=tr.channel, time=0))
            for cc, val in tr.controls:
                mt.append(mido.Message("control_change", control=cc, value=val, channel=tr.channel, time=0))
            timed = []
            for start, dur, p, vel in tr.notes:
                on = int(round(start * TPB))
                off = max(on + 20, int(round((start + dur) * TPB)) - 12)
                timed.append((on, 2, mido.Message("note_on", note=p, velocity=vel, channel=tr.channel)))
                timed.append((off, 0, mido.Message("note_off", note=p, velocity=0, channel=tr.channel)))
            for start, msg in tr.events:
                timed.append((int(round(start * TPB)), 1, msg.copy(channel=tr.channel)))
            timed.sort(key=lambda x: (x[0], x[1]))
            now = 0
            for t, _, msg in timed:
                msg.time = t - now
                now = t
                mt.append(msg)
            mid.tracks.append(mt)
        return mid

    def save(self, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_midi().save(path)
        return path
