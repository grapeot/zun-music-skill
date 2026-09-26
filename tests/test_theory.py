import pytest

from zun_music.theory import (bar_length_errors, chord_tones, pitch, pitch_class, skeleton,
                              skeleton_mismatches, sounding_at)


@pytest.mark.parametrize("name,expected", [("C4", 60), ("A5", 81), ("Bb4", 70), ("C#5", 73), ("B-1", 11)])
def test_pitch(name, expected):
    assert pitch(name) == expected


@pytest.mark.parametrize("bad", ["H4", "C", "c4", "C##4", ""])
def test_pitch_rejects_bad_names(bad):
    with pytest.raises(ValueError):
        pitch(bad)


def test_pitch_class_and_chords():
    assert pitch_class("Bb") == 10
    assert chord_tones("m7") == (0, 3, 7, 10)
    with pytest.raises(ValueError):
        chord_tones("m9")


def test_bar_lengths():
    assert bar_length_errors([[("C4", 4)], [("C4", 2)]]) == []  # short last bar allowed
    assert bar_length_errors([[("C4", 3)], [("C4", 4)]]) == ["bar 1: 3 beats, expected 4"]
    assert bar_length_errors([[("C", "maj", 2), ("F", "maj", 2)]]) == []


def test_sounding_at_and_rests():
    bar = [("A5", .75), (None, .25), ("C6", 3)]
    assert sounding_at(bar, 0) == 81
    assert sounding_at(bar, .8) is None
    assert sounding_at(bar, 2) == 84


def test_skeleton_tolerates_octaves_and_ornaments():
    src = [[("A5", 1), ("C6", 1), ("C6", 2)]]
    arr = [[("A4", .75), ("C6", .75), ("C6", 1.5), ("D6", .25), ("C6", .25), ("B5", .25), ("C6", .25)]]
    assert skeleton(src) == [(0, 0, 9), (0, 2, 0)]
    assert skeleton_mismatches(src, arr) == []


def test_skeleton_flags_changed_strong_beat_unless_allowed():
    src = [[("C5", 4)]]
    arr = [[("C5", 2), ("A5", 2)]]
    assert skeleton_mismatches(src, arr) == [(0, 2, 0, 9)]
    assert skeleton_mismatches(src, arr, allow=[(0, 2)]) == []


def test_skeleton_bar_count_mismatch():
    assert skeleton_mismatches([[("C5", 4)]], []) == [("bar-count", 1, 0)]
