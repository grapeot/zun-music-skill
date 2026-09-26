# Working notes

## Changelog

### 2026-09-25

- Scaffolded the repository: docs, packaging, CI, empty package, smoke test.
- Added `theory.py`: note parsing, chord qualities, bar-length validation, strong-beat skeleton check.
- Added `song.py`: multi-track MIDI writer with controller events.
- Added `arrange.py`: `Arrangement`, `check()`, and the lead, backing and mechanical-drum generators.
- Added `render.py` (FluidSynth + ffmpeg, verbatim subprocess errors, SoundFont header check) and `serve.py` (LAN listening page).
- Ported the accepted prototype arrangement of 《送别》 to `examples/songbie.py`; its MIDI matches the prototype note for note except the intro bass pickup, which is now a generic walk-up to the first chord root.
- Added `scripts/render_example.py` and `scripts/serve.py`.
- Wrote `skills/zun_music.md` and the full README.
- Review fixes: `check()` reports a source/melody bar-count mismatch instead of crashing, rejects non-4/4 meters, and caps `skeleton_allow` at one per four bars; 7th chords now sound their 7th in strings and piano; bass eighths are clipped at segment boundaries; the final bar sustains for its written length; piano fills moved to their own `Piano Fill` channel so they no longer cut the held lead-double note; render trims only trailing silence and always removes the temp WAV; the server reports a busy port instead of a traceback; `render_example.py` gained `--note` and a clean error on failed checks.
- Validation: 32 unit tests passed offline; rendered `songbie` with NeoTHFont; privacy scan clean.

## Lessons Learned

- The musical lessons (skeleton vs. idioms, mechanical drums, SoundFont first) live in `skills/zun_music.md` under "Known pitfalls", because the agent reads that file; do not duplicate them here.
- `render.resolve_soundfont` checks the RIFF/sfbk header on purpose: a Cloudflare challenge page saved as `.sf2` otherwise makes FluidSynth fail with an unhelpful message.
- ffmpeg `silenceremove` with `stop_periods=-1` strips every internal silence, not just the tail; trailing-only trimming needs the `areverse` sandwich.
- The intro bass pickup is transposed up an octave when the first chord root falls below C2, to keep it out of the mud; it then resolves down to the bass voicing.
