# Test strategy

## Unit (offline, CI)

`python -m pytest tests/ -v` needs neither FluidSynth nor a SoundFont.

- Note-name parsing, including sharps and flats across octaves.
- Bar-length validation rejects bars that do not sum to the time signature.
- Skeleton extraction and comparison: identical melodies pass, octave shifts pass, a changed strong-beat pitch fails unless it is in the allow-list.
- MIDI writing: every example builds, writes a readable MIDI file, has the expected tracks, and its drum track uses a single velocity.
- Every example passes its own skeleton check.
- Video: band levels have the right shape, range and frequency placement; frames have the right size and count; titles are trimmed. An end-to-end encode test runs only where ffmpeg has libx265 and checks for `hevc/hvc1` + `aac`.
- Server: Range parsing (open, suffix, clamped, unsatisfiable, multi-range ignored), a live 206 response with the right bytes, and 404 for path traversal attempts.

## Integration (local, opt-in)

Rendering is exercised manually because it needs FluidSynth, ffmpeg and a SoundFont:

```bash
python scripts/render_example.py songbie --soundfont /path/to/neothfont.sf2
```

Success means an MP3 appears under `out/` whose length is the MIDI length printed by the script plus at most about 3 s of reverb tail.

## Human acceptance

The only real test of an arrangement is listening. The agent delivers audio, via the listening page when the user is on another device, and asks two questions: is the source recognisable, and does it sound like ZUN?
