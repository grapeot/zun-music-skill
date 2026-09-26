# zun-music-skill

An agent skill and a small Python toolkit for arranging public-domain melodies in the style of ZUN, the composer of the Touhou Project games, and rendering them to MIDI and MP3.

A coding agent can already write MIDI. What it lacks is taste in this particular style. Left alone, it either copies the source tune verbatim, so the result is recognisable but not ZUN, or it rewrites the tune so heavily that the source disappears. It also tends to render with a generic General MIDI bank that hides half the sound. This repository encodes what a human listener confirmed over several rounds of A/B listening:

- **Keep the tune's skeleton.** The pitches on strong beats stay as written; ZUN idioms go between them: 3-3-2 syncopation, anticipations, 16th-note turns and runs, and a trumpet lead with scoop and vibrato.
- **Harmony.** The ZUN progression (♭VI–♭VII–i, or IV–V–vi in a major key) with harmonic-minor cadences.
- **Drums that sound programmed.** Constant velocity, 16th-note hats, syncopated 16th-note kicks, a crash on every beat in the climax, 32nd-note snare bursts.
- **A Touhou-oriented SoundFont.** Trumpet doubled by piano, strings, piano arpeggios.

A built-in check verifies that an arrangement still carries the source melody's strong-beat skeleton, so "recognisable" is tested rather than hoped for.

## Requirements

- Python 3.9+
- [FluidSynth](https://www.fluidsynth.org/) and [ffmpeg](https://ffmpeg.org/) on PATH (only for rendering audio)
- A SoundFont (`.sf2`). The recommended bank is **NeoTHFont**, a community bank aimed at the Roland SC-88Pro / SD-90 sound, listed on [musical-artifacts.com](https://musical-artifacts.com/artifacts/6614). In it, program 56 is "Romantic Tp", the trumpet Touhou fans call the ZUNpet. Any General MIDI bank, such as [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS), works for smoke tests but sounds much less like ZUN.

SoundFonts are not included. The provenance of samples in fan-made banks is often unclear, so check the terms of whichever bank you use before publishing anything rendered with it.

## Installation

```bash
git clone https://github.com/grapeot/zun-music-skill
cd zun-music-skill
uv venv && source .venv/bin/activate      # or: python -m venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"                # or: pip install -e ".[dev]"
python -m pytest tests/ -v                # offline, no SoundFont needed
```

## Quick start

Render the bundled example, the climax phrase of 《送别》 ("Farewell"), whose melody is J. P. Ordway's 1868 "Dreaming of Home and Mother":

```bash
export ZUN_MUSIC_SOUNDFONT=/path/to/neothfont.sf2   # or pass --soundfont
python scripts/render_example.py songbie
# -> out/songbie.mid, out/songbie.mp3, out/songbie.txt
```

Listen from any device on the same network:

```bash
python scripts/serve.py out --port 8766
# prints http://<your LAN address>:8766/
```

The page lists every MP3 in the folder with its one-line description and a MIDI download link, and picks up new renders on refresh.

## Writing a new arrangement

Copy `examples/songbie.py` to `examples/<tune>.py`. Then:

1. Put the untouched transcription in `SOURCE`, as bars of `(note name, beats)`.
2. Write the arranged `MELODY` and the `CHORDS`, as bars of `(root, quality, beats)`.
3. List any deliberate strong-beat departures in `skeleton_allow`.
4. State the melody's provenance and why it is public domain in the module docstring.

Then run:

```bash
python -m pytest tests/ -v                   # structural + skeleton checks for every example
python scripts/render_example.py <tune> --midi-only   # fast structural + skeleton check
python scripts/render_example.py <tune> --name v2_drums --note "drums only: constant velocity"
```

The toolkit supports 4/4 only; convert other meters as part of the arrangement.

## Using it with AI agents

The root skill is `skills/zun_music.md`. It gives the agent the goal and acceptance criteria, the source-selection rules including a public-domain check, the arrangement method, and the pitfalls observed in real listening sessions.

To install it, give this repository's URL to your coding agent (Claude Code, Codex, Cursor, OpenCode, …) and ask it to install the skill. The agent should clone the repository and install it as above. It should then start from your workspace's `AGENTS.md` or `CLAUDE.md`, follow any routing file it points to, and add `skills/zun_music.md` to the workspace's skill discovery chain. If the workspace has a `skills/INDEX.md` or `rules/skills/INDEX.md`, the entry goes there; otherwise a short pointer goes in `AGENTS.md` or `CLAUDE.md`. Only the root skill needs to be registered.

## Disclaimer

This is an independent fan project. It is not affiliated with ZUN, Team Shanghai Alice, or Roland. Touhou Project is the work of Team Shanghai Alice. The repository contains no Touhou music and no samples; it generates new arrangements of public-domain melodies.

## License

MIT
