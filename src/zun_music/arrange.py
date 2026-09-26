"""ZUN idiom generators: turn an Arrangement (melody + chords) into a multi-track Song.

Instrument choices follow General MIDI numbering so any GM SoundFont plays the result;
a Touhou-oriented bank (e.g. NeoTHFont, where program 56 is "Romantic Tp") supplies the timbre.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import mido

from .song import DRUM_CHANNEL, Song
from .theory import bar_length_errors, chord_tones, pitch, pitch_class, skeleton_mismatches

# General MIDI programs
TRUMPET, PIANO, FINGERED_BASS, STRINGS = 56, 0, 33, 48
# General MIDI drum keys
KICK, SNARE, CLOSED_HAT, CRASH, RIDE = 36, 38, 42, 49, 51
TOM_HI, TOM_HI_MID, TOM_LO_MID, TOM_LO = 50, 48, 47, 45

ChordSeg = Tuple[str, str, float]  # (root, quality, beats), e.g. ("F", "maj", 2)


@dataclass
class Arrangement:
    title: str
    bpm: float
    melody: List[list]                      # bars of (note name | None, beats)
    chords: List[List[ChordSeg]]            # one list of segments per melody bar
    source: Optional[List[list]] = None     # untouched transcription, for the skeleton check
    skeleton_allow: Sequence[Tuple[int, float]] = ()  # deliberate strong-beat departures
    fills: Sequence[Tuple[int, float, Sequence[str]]] = ()  # (bar, start beat, 16th-note names)
    intro_bars: int = 1
    climax_from_bar: Optional[int] = None   # drums double from this bar; default = second half
    drum_velocity: int = 112
    beats_per_bar: int = 4
    description: str = ""
    lead_program: int = TRUMPET
    expressive_lead: bool = True
    reverb: int = 55
    extra: dict = field(default_factory=dict)


def check(arr: Arrangement) -> List[str]:
    """Structural problems that make an arrangement unusable; empty list means OK."""
    bpb = arr.beats_per_bar
    if bpb != 4:
        return [f"only 4/4 is supported (beats_per_bar={bpb}); drum and intro patterns assume four beats"]
    problems = [f"melody {e}" for e in bar_length_errors(arr.melody, bpb)]
    problems += [f"chords {e}" for e in bar_length_errors(arr.chords, bpb)]
    if len(arr.chords) != len(arr.melody):
        problems.append(f"{len(arr.chords)} chord bars for {len(arr.melody)} melody bars")
    for bar in arr.chords:
        for root, quality, _ in bar:
            try:
                pitch_class(root), chord_tones(quality)
            except ValueError as e:
                problems.append(str(e))
    for bar in arr.melody:
        for name, _ in bar:
            if name is not None:
                try:
                    pitch(name)
                except ValueError as e:
                    problems.append(str(e))
    if arr.source is not None:
        problems += [f"source {e}" for e in bar_length_errors(arr.source, bpb)]
        if len(arr.source) != len(arr.melody):
            problems.append(f"source has {len(arr.source)} bars, melody has {len(arr.melody)}")
        else:
            for bar, beat, src, got in skeleton_mismatches(arr.source, arr.melody, arr.skeleton_allow,
                                                           strong_beats=range(0, bpb, 2)):
                problems.append(f"skeleton: bar {bar + 1} beat {beat + 1}: source pc {src}, arrangement pc {got}")
        cap = max_skeleton_departures(len(arr.melody))
        if len(arr.skeleton_allow) > cap:
            problems.append(f"{len(arr.skeleton_allow)} allowed skeleton departures; at most {cap} "
                            f"(one per four bars) or the tune stops being recognisable")
    return problems


def max_skeleton_departures(n_bars: int) -> int:
    return max(1, n_bars // 4)


def _voice(pc: int, low: int, split: int) -> int:
    """Root placed at ``low + pc`` for pc < split, one octave lower otherwise."""
    return low + pc if pc < split else low - 12 + pc


def add_lead(song: Song, arr: Arrangement, t0: float):
    """Lead on trumpet, doubled an octave up on piano (the signature ZUN pairing)."""
    for bar_i, bar in enumerate(arr.melody):
        t = t0 + bar_i * arr.beats_per_bar
        for name, dur in bar:
            if name is not None:
                p = pitch(name)
                song.note("Lead", arr.lead_program, 0, t, dur, p, 104)
                song.note("Lead Double", PIANO, 3, t, dur, p + 12, 70)
                if arr.expressive_lead and dur >= 1:
                    add_expression(song, arr.lead_program, t, dur)
            t += dur
    for bar_i, start, names in arr.fills:
        for i, name in enumerate(names):
            song.note("Piano Fill", PIANO, 5, t0 + bar_i * arr.beats_per_bar + start + i * .25, .25,
                      pitch(name), 76)


def add_expression(song: Song, program: int, start: float, dur: float):
    """Scoop up from half a semitone below, then vibrato fading in over the second half."""
    for i in range(5):
        song.event("Lead", program, 0, start + i * .03, mido.Message("pitchwheel", pitch=-2048 + i * 512))
    song.event("Lead", program, 0, start, mido.Message("control_change", control=1, value=0))
    if dur >= 1.5:
        for i in range(9):
            t = start + dur * .4 + dur * .55 * i / 8
            song.event("Lead", program, 0, t, mido.Message("control_change", control=1, value=int(10 + 70 * i / 8)))
    song.event("Lead", program, 0, start + dur - .01, mido.Message("control_change", control=1, value=0))


def add_backing(song: Song, arr: Arrangement, t0: float):
    """Eighth-note root/octave bass, block strings, 16th up-down piano arpeggios; last bar sustained."""
    bpb = arr.beats_per_bar
    last = len(arr.chords) - 1
    for bar_i, bar in enumerate(arr.chords):
        t = t0 + bar_i * bpb
        # the final bar sustains its first chord for the bar's full written length
        segments = [(bar[0][0], bar[0][1], sum(s[-1] for s in bar))] if bar_i == last else bar
        for root, quality, beats in segments:
            pc, tones = pitch_class(root), chord_tones(quality)
            bass = _voice(pc, 36, 5)
            strings = _voice(pc, 60, 7)
            piano = _voice(pc, 48, 7)
            # triads get the root doubled on top; 7th chords use their four tones
            upper = [strings + iv for iv in tones] + ([strings + 12] if len(tones) == 3 else [])
            for v in upper:
                song.note("Strings", STRINGS, 2, t, beats, v, 66)
            arp = [piano + iv for iv in tones] + [piano + 12 + iv for iv in tones[:3]] + [piano + 24]
            if bar_i == last:
                song.note("Bass", FINGERED_BASS, 1, t, beats, bass, 100)
                for p in arp:
                    song.note("Piano", PIANO, 4, t, beats, p, 78)
            else:
                i = 0
                while i * .5 < beats - 1e-9:  # eighths, last one clipped to the segment
                    song.note("Bass", FINGERED_BASS, 1, t + i * .5, min(.5, beats - i * .5),
                              bass + (12 if i % 2 else 0), 96)
                    i += 1
                cycle = arp + arp[-2:0:-1]
                for i in range(int(round(beats * 4))):
                    song.note("Piano", PIANO, 4, t + i * .25, .25, cycle[i % len(cycle)], 66)
            t += beats


def add_mechanical_drums(song: Song, arr: Arrangement, t0: float):
    """Step-sequencer drums: one velocity everywhere, 16th hats, syncopated 16th kicks,
    crash on every beat in the climax, 32nd-note snare bursts and tom runs at transitions."""
    vel = arr.drum_velocity
    n = len(arr.melody)
    climax = arr.climax_from_bar if arr.climax_from_bar is not None else n // 2

    def hit(t, key):
        song.note("Drums", 0, DRUM_CHANNEL, t, .125, key, vel)

    # intro: 16th snares -> 32nd snare burst -> toms with kicks, in the last intro bar
    if arr.intro_bars:
        s = t0 - 4
        for i in range(8):
            hit(s + i * .25, SNARE)
        for i in range(8):
            hit(s + 2 + i * .125, SNARE)
        for i, tom in enumerate((TOM_HI, TOM_HI_MID, TOM_LO_MID, TOM_LO)):
            hit(s + 3 + i * .25, tom)
            hit(s + 3 + i * .25, KICK)

    for bar in range(n):
        b0 = t0 + bar * arr.beats_per_bar
        if bar == n - 1:
            for key in (KICK, CRASH, SNARE):
                hit(b0, key)
            continue
        loud = bar >= climax
        if not loud:
            for i in range(16):
                hit(b0 + i * .25, CLOSED_HAT)
        kicks = (0, .5, .75, 1, 1.5, 2, 2.5, 2.75, 3, 3.5) if loud else (0, .75, 1.5, 2, 2.75, 3.5)
        for k in kicks:
            hit(b0 + k, KICK)
        for sn in (1, 3):
            hit(b0 + sn, SNARE)
        if bar in (0, climax):
            hit(b0, CRASH)
        if loud:
            for beat in range(4):
                hit(b0 + beat, CRASH)
                hit(b0 + beat + .5, RIDE)
        if bar == climax - 1:  # transition into the climax
            for i in range(8):
                hit(b0 + 2 + i * .125, SNARE)
            for i, tom in enumerate((TOM_HI, TOM_HI, TOM_HI_MID, TOM_HI_MID, TOM_LO_MID, TOM_LO_MID, TOM_LO, TOM_LO)):
                hit(b0 + 3 + i * .125, tom)
            for i in range(4):
                hit(b0 + 3 + i * .25, KICK)
        elif bar % 2 == 1:
            for i in range(4):
                hit(b0 + 3.5 + i * .125, SNARE)


def add_bass_pickup(song: Song, arr: Arrangement, t0: float):
    """Four eighth notes in the last two intro beats walking up to the first chord root."""
    if not arr.intro_bars:
        return
    target = _voice(pitch_class(arr.chords[0][0][0]), 36, 5)
    if target < 36:  # keep the walk-up out of the mud; it resolves down an octave
        target += 12
    for i, step in enumerate((-7, -5, -3, -1)):
        song.note("Bass", FINGERED_BASS, 1, t0 - 2 + i * .5, .5, target + step, 90)


def build_song(arr: Arrangement) -> Song:
    problems = check(arr)
    if problems:
        raise ValueError(f"{arr.title}: " + "; ".join(problems))
    song = Song(arr.bpm, arr.beats_per_bar)
    t0 = arr.intro_bars * arr.beats_per_bar
    add_lead(song, arr, t0)
    add_backing(song, arr, t0)
    add_mechanical_drums(song, arr, t0)
    add_bass_pickup(song, arr, t0)
    for name, tr in song.tracks.items():
        tr.controls = [(91, 35 if tr.channel == DRUM_CHANNEL else arr.reverb), (93, 20)]
        if name == "Piano":
            tr.controls.append((10, 48))
        elif name in ("Lead Double", "Piano Fill"):
            tr.controls.append((10, 80))
    return song
