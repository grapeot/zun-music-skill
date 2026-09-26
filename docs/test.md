# Test strategy

## Unit (offline, CI)

`python -m pytest tests/ -v` needs neither FluidSynth nor a SoundFont.

- Note-name parsing, including sharps and flats across octaves.
- Bar-length validation rejects bars that do not sum to the time signature.
- Skeleton extraction and comparison: identical melodies pass, octave shifts pass, a changed strong-beat pitch fails unless it is in the allow-list.
- MIDI writing: every example builds, writes a readable MIDI file, has the expected tracks, and its drum track uses a single velocity (except the optional final accent).
- Every example passes its own skeleton check.

## Integration (local, opt-in)

Rendering is exercised manually because it needs FluidSynth, ffmpeg and a SoundFont:

```bash
python scripts/render_example.py songbie --soundfont /path/to/neothfont.sf2
```

Success means an MP3 of the expected length (within about 3 s of `bars × 4 × 60 / bpm`) appears under `out/`.

## Human acceptance

The only real test of an arrangement is listening. The agent delivers audio, via the listening page when the user is on another device, and asks two questions: is the source recognisable, and does it sound like ZUN?
