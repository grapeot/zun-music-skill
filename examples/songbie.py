"""《送别》 (Songbie, "Farewell"), climax phrase, arranged in ZUN style.

Provenance: the melody is John P. Ordway's "Dreaming of Home and Mother" (published 1868; Ordway
died 1880), set to Chinese lyrics by Li Shutong around 1915. The melody is in the public domain.
Transcribed from a numbered-notation score in C major, 4/4; this is the "天之涯 … 今宵别梦寒" phrase.

This version was accepted by a human listener after seven rounds; see skills/zun_music.md for
what each round taught.
"""
from zun_music.arrange import Arrangement

# Untouched transcription (jianpu: 6 i i - | 7 67 i - | 67 i6 65 31 | 2 - - - |
#                                   5 35 i. 7 | 6 i 5 - | 5 23 4. 7 | 1 - - - )
SOURCE = [
    [("A5", 1), ("C6", 1), ("C6", 2)],
    [("B5", 1), ("A5", .5), ("B5", .5), ("C6", 2)],
    [("A5", .5), ("B5", .5), ("C6", .5), ("A5", .5), ("A5", .5), ("G5", .5), ("E5", .5), ("C5", .5)],
    [("D5", 4)],
    [("G5", 1), ("E5", .5), ("G5", .5), ("C6", 1.5), ("B5", .5)],
    [("A5", 1), ("C6", 1), ("G5", 2)],
    [("G5", 1), ("D5", .5), ("E5", .5), ("F5", 1.5), ("B4", .5)],
    [("C5", 4)],
]

# Strong-beat pitches kept; ZUN idioms placed between them.
MELODY = [
    # 3-3-2, long note entered early, 16th turn at the tail
    [("A5", .75), ("C6", .75), ("C6", 1.5), ("D6", .25), ("C6", .25), ("B5", .25), ("C6", .25)],
    # B-A-B turn, C anticipated by half a beat, descending 16ths into the next phrase
    [("B5", .75), ("A5", .25), ("B5", .5), ("C6", 1.5), ("D6", .25), ("C6", .25), ("B5", .25), ("G5", .25)],
    [("A5", .5), ("B5", .5), ("C6", .5), ("A5", .5), ("A5", .5), ("G5", .25), ("A5", .25), ("E5", .5), ("C5", .5)],
    # held note, then an ascending run that launches the second half
    [("D5", 2.5), ("E5", .25), ("F5", .25), ("G5", .25), ("A5", .25), ("B5", .25), ("D6", .25)],
    [("G5", .75), ("E5", .25), ("G5", .5), ("C6", 2), ("B5", .5)],
    [("A5", .75), ("C6", .75), ("G5", 1.5), ("G5", .25), ("A5", .25), ("G5", .25), ("F5", .25)],
    # F held across the change to E7: a flat-9 tension typical of harmonic-minor cadences
    [("G5", .75), ("D5", .25), ("E5", .5), ("F5", 1.5), ("E5", .5), ("B4", .5)],
    # end on A instead of C: the phrase closes in A minor
    [("C5", 2), ("E5", .5), ("A5", 1.5)],
]

# IV-V-vi (the major-key reading of the ZUN progression), borrowed E7 -> Am cadences.
CHORDS = [
    [("F", "maj", 2), ("F", "maj", 2)],
    [("G", "maj", 2), ("A", "min", 2)],
    [("F", "maj", 2), ("A", "min", 2)],
    [("D", "m7", 2), ("E", "7", 2)],
    [("C", "maj", 2), ("A", "min", 2)],
    [("F", "maj", 2), ("G", "maj", 2)],
    [("D", "m7", 2), ("E", "7", 2)],
    [("A", "min", 4)],
]

ARRANGEMENT = Arrangement(
    title="songbie",
    bpm=144,
    melody=MELODY,
    chords=CHORDS,
    source=SOURCE,
    skeleton_allow=[(7, 2)],  # the final A-minor landing
    fills=[(3, .5, ["D6", "E6", "F6", "A6", "G6", "F6", "E6", "D6"])],
    description="《送别》climax phrase, ZUN style: strong-beat skeleton kept; 3-3-2 syncopation, "
                "anticipations, 16th turns and runs, trumpet scoop + vibrato; IV-V-vi with E7->Am; "
                "mechanical drums. 144 BPM.",
)
