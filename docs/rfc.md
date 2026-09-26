# RFC — zun-music-skill architecture

## Data model

An arrangement is plain Python data, so an agent can write one without learning a DSL:

- `melody`: list of bars; each bar is a list of `(note_name, beats)` such as `("A5", 0.75)`. Note names use sharps or flats (`C#5`, `Bb4`).
- `chords`: list of bars; each bar is a list of `(root, quality, beats)` segments, for example `("F", "maj", 2)`.
- `fills`: optional piano runs `(bar, start_beat, [note names])` in 16ths.
- `source`: the untouched transcription of the original melody, in the same format, used only for the skeleton check.
- `skeleton_allow`: (bar, beat) strong-beat positions where the arrangement deliberately departs from `source`; capped at one per four bars.
- Meter: 4/4 only; `check()` rejects anything else because the drum and intro patterns assume four beats.

## Modules (`src/zun_music/`)

- `theory.py`: note-name parsing, chord qualities, bar-length validation, strong-beat skeleton extraction and comparison.
- `song.py`: a small multi-track container that writes a type-1 MIDI file with notes plus controller events (pitch bend, modulation, reverb, pan).
- `arrange.py`: `Arrangement`, `check()` and the ZUN idiom generators. Trumpet lead doubled an octave up on piano, trumpet scoop + vibrato on long notes, eighth-note root/octave bass, 16th up-down piano arpeggios, block string chords, mechanical drums with constant velocity.
- `render.py`: FluidSynth → WAV → ffmpeg (trim + loudness normalise) → MP3. Errors from the subprocess are surfaced verbatim.
- `video.py` (optional `video` extra: numpy, Pillow): MP3 → 24-band log-spaced levels (50 Hz–12 kHz, normalised to the clip's 99.5th percentile) → LED-meter frames drawn with Pillow → piped to ffmpeg → 640×360 30 fps H.265 (`hvc1`) + AAC MP4.
- `serve.py`: a tiny listening page bound to `0.0.0.0`. It lists every MP3 in an output folder with its description, embeds the MP4 when present, and offers download links; files are served with HTTP Range support and confined to the folder.

## Key decisions

- **Skeleton check instead of "similarity".** Whether a listener recognises the tune is subjective, but a necessary condition is testable: the pitch sounding at each bar's strong beats (1 and 3 in 4/4) should match the source, up to octave. Deviations must be explicit via an allow-list, so every departure is a deliberate artistic choice.
- **Constant drum velocity.** ZUN's drums were step-programmed; the humanised accents a live-drummer mindset produces are the main reason drums sound "not ZUN". The generator exposes a single velocity.
- **SoundFont is an input, not a dependency.** The good Touhou-oriented banks have unclear sample provenance, so the repo never ships one. The renderer takes a path and fails loudly when it is missing.
- **Scripts over a CLI framework.** `scripts/render_example.py` and `scripts/serve.py` are thin wrappers; examples are ordinary modules exposing an `ARRANGEMENT` object.
