# AGENTS.md — agent operating rules for this repository

## Exact commands

```bash
# setup (Python 3.9+; 3.12 recommended)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# offline unit tests (no SoundFont, no network)
python -m pytest tests/ -v

# rendering needs FluidSynth + ffmpeg on PATH and a SoundFont
# (path via --soundfont or ZUN_MUSIC_SOUNDFONT)
```

## Layout

- `src/zun_music/` — reusable package
- `scripts/` — user-facing entry points
- `examples/` — complete worked arrangements (public-domain melodies only)
- `skills/` — agent skill documents; `skills/zun_music.md` is the single root skill
- `docs/` — `prd.md`, `rfc.md`, `test.md`, `working.md`

## Invariants

- Only public-domain source melodies in `examples/` and tests. Record the composer, year and why it is public domain next to every transcription.
- Never commit SoundFonts, rendered audio, or anything under `out/`. SoundFonts are downloaded by the user; the README says where from.
- Never commit personal data: no real names beyond the GitHub handle, no email addresses, LAN IPs, home-directory paths, or machine names. Use `example.com` / `192.0.2.x` placeholders if an example needs them.
- Default branch is `master`. All changes land through a PR; branch protection is on.
- Update `docs/working.md` (Changelog + Lessons Learned) whenever behaviour or a musical lesson changes.
- Commit only when the user asks; keep commits small and single-purpose.
