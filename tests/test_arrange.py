import mido
import pytest

from zun_music.arrange import Arrangement, build_song, check
from zun_music.song import DRUM_CHANNEL


def test_examples_pass_structural_and_skeleton_checks(example):
    assert check(example.ARRANGEMENT) == []


def test_examples_have_provenance(example):
    doc = (example.__doc__ or "").lower()
    assert "public domain" in doc, "every example must state why its melody is public domain"


def test_example_builds_midi(example, tmp_path):
    arr = example.ARRANGEMENT
    song = build_song(arr)
    path = song.save(tmp_path / "x.mid")
    mid = mido.MidiFile(path)
    names = {t.name for t in mid.tracks}
    assert {"Lead", "Lead Double", "Bass", "Strings", "Piano", "Drums"} <= names
    for tr in mid.tracks:
        for m in tr:
            if m.type in ("note_on", "note_off"):
                assert 0 <= m.note <= 127
    expected = (arr.intro_bars + len(arr.melody)) * arr.beats_per_bar * 60 / arr.bpm
    assert abs(mid.length - expected) < 1.0


def test_drums_are_mechanical(example):
    song = build_song(example.ARRANGEMENT)
    drums = song.tracks["Drums"]
    assert drums.channel == DRUM_CHANNEL
    assert len({vel for _, _, _, vel in drums.notes}) == 1


def test_expression_resets_vibrato(example):
    song = build_song(example.ARRANGEMENT)
    cc1 = [m.value for _, m in sorted(song.tracks["Lead"].events, key=lambda e: e[0]) if m.type == "control_change"]
    assert cc1 and cc1[-1] == 0


def _tiny(**kw):
    base = dict(title="t", bpm=120, melody=[[("C5", 4)], [("E5", 4)]],
                chords=[[("C", "maj", 4)], [("A", "min", 4)]])
    base.update(kw)
    return Arrangement(**base)


def test_check_catches_problems():
    assert check(_tiny()) == []
    assert any("melody bar 1" in p for p in check(_tiny(melody=[[("C5", 3)], [("E5", 4)]])))
    assert any("chord bars" in p for p in check(_tiny(chords=[[("C", "maj", 4)]])))
    assert any("unknown chord quality" in p for p in check(_tiny(chords=[[("C", "m9", 4)], [("A", "min", 4)]])))
    assert any("skeleton" in p for p in check(_tiny(source=[[("C5", 4)], [("G5", 4)]])))


def test_check_reports_bar_count_mismatch_instead_of_crashing():
    problems = check(_tiny(source=[[("C5", 4)], [("E5", 4)], [("G5", 4)]]))
    assert any("source has 3 bars" in p for p in problems)


def test_check_rejects_other_meters_and_too_many_departures():
    assert "only 4/4" in check(_tiny(beats_per_bar=3))[0]
    src = [[("C5", 4)], [("E5", 4)]]
    assert any("at most 1" in p for p in check(_tiny(source=src, skeleton_allow=[(0, 0), (1, 0)])))


def test_seventh_chords_sound_their_seventh():
    song = build_song(_tiny(chords=[[("E", "7", 4)], [("A", "min", 4)]], melody=[[("B4", 4)], [("C5", 4)]]))
    pcs = {p % 12 for s, _, p, _ in song.tracks["Strings"].notes if s < 8}
    assert {4, 8, 11, 2} <= pcs  # E G# B D


def test_bass_never_overlaps_segment_boundary():
    arr = _tiny(chords=[[("C", "maj", 1.5), ("F", "maj", 2.5)], [("A", "min", 4)]])
    song = build_song(arr)
    for s, d, _, _ in song.tracks["Bass"].notes:
        if 4 <= s < 5.5:
            assert s + d <= 5.5 + 1e-9


def test_build_song_refuses_broken_arrangement():
    with pytest.raises(ValueError):
        build_song(_tiny(melody=[[("C5", 3)], [("E5", 4)]]))
