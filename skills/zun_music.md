# ZUN-Style Arrangement Skill

## Metadata

- **Type**: Workflow + BestPractice
- **Use when**: the user wants a familiar tune re-imagined "as if ZUN wrote it" (Touhou Project style), or wants to learn what makes ZUN's music sound like ZUN by hearing controlled variations.
- **Trigger words**: `ZUN style`, `Touhou style`, `東方風アレンジ`, `東方風`, `ZUN风`, `神主风`, `ZUN-ify`, `ZUNpet`
- **Output**: `out/<version>.mid`, `out/<version>.mp3`, `out/<version>.txt` (one-line description), plus a new or updated arrangement module in `examples/`
- **Created**: 2026-09-25

## Goal

Produce a short arrangement, typically one complete phrase of 8 bars, about 15 s, in which a listener both recognises the source tune within the first phrase and hears it as ZUN-style. Deliver it as audio the user can play immediately.

## Boundaries

- Source melodies must be public domain in the user's likely jurisdiction. Check the composer's death year: China protects works for life + 50 years; Japan for life + 70 years if the author died in 1968 or later (life + 50 before that); the EU for life + 70 years; in the US, anything published before 1931 is public domain as of 2026. A famous children's song is not automatically public domain. If the requested tune is protected, say so and propose a public-domain substitute with a similar feel before writing any notes.
- Do not reproduce or quote actual Touhou tracks. The goal is the style, not ZUN's melodies.
- Do not commit, redistribute or bundle SoundFonts or rendered audio.
- Work inside a clone of this repository: new arrangements go in its `examples/`, and renders go in its `out/`.
- 4/4 only. `check()` rejects other meters, so convert triple-meter sources such as Greensleeves to 4/4 as part of the arrangement.
- The human is the only judge of "sounds like ZUN". Never report an arrangement as good without the user having listened to it.

## Acceptance criteria

Automated. `python scripts/render_example.py <tune> --midi-only` runs `check()` (criteria 1–2) and exits non-zero on failure; `python -m pytest tests/ -v` runs criteria 1–3 for every example:

1. Every melody, source and chord bar sums to the meter; the final bar may be short.
2. The skeleton check passes. At each strong beat (beats 1 and 3 in 4/4), the arrangement's pitch class equals the untouched source transcription's. Every deliberate departure is listed in `skeleton_allow`, capped at one per four bars; normally it is only the final cadence.
3. The drum track uses one velocity.
4. `scripts/render_example.py <tune>` produces an MP3 whose length is the printed MIDI length plus at most about 3 s of reverb tail. Check it with `ffprobe`.

Human:

5. The user confirms that the source tune is recognisable and that the result sounds like ZUN. If either answer is no, iterate.

## Resources

- Toolkit in `src/zun_music/`. `theory.py` handles note names, chord qualities and the skeleton check. `arrange.py` holds the `Arrangement` dataclass and the idiom generators (trumpet lead doubled an octave up on piano, trumpet scoop and vibrato, root/octave eighth-note bass, 16th-note piano arpeggios, block strings, mechanical drums). `render.py` wraps FluidSynth and ffmpeg. `video.py` turns an MP3 into a small EQ-meter MP4 (640×360, H.265/hvc1 + AAC) for sharing. `serve.py` provides the listening page, which embeds the video if there is one and offers download links for every file.
- `examples/songbie.py` is a complete arrangement that a human accepted after seven rounds. Copy its shape: a `SOURCE` transcription, the arranged `MELODY`, `CHORDS`, and an `ARRANGEMENT` whose module docstring states the melody's provenance.
- External tools: `fluidsynth` and `ffmpeg` on PATH.
- A SoundFont, passed with `--soundfont` or `ZUN_MUSIC_SOUNDFONT`. The recommended bank is NeoTHFont (musical-artifacts.com artifact 6614, hosted on MediaFire), in which program 56 is "Romantic Tp", the so-called ZUNpet. General MIDI banks such as GeneralUser GS are fine for smoke tests but hide most of the style.

If no suitable SoundFont is available, still deliver the MIDI, render with whatever General MIDI bank exists, and tell the user plainly that the timbre is the missing piece.

## Method

These are recommendations, not a fixed sequence, except where noted.

**Choose the source for fit, not just fame.** Good candidates meet three conditions. They are in a minor key or a minor-flavoured pentatonic mode, so the ZUN progression ♭VI–♭VII–i applies directly. Their melody has some rhythmic drive and not too many long held notes, because ZUN melodies almost never rest, and a slow lyrical tune means most of the work is filling long notes. And they are recognisable within 8 bars. Examples that meet these conditions include 荒城の月 (Taki, 1901, B minor), Greensleeves, and the Swan Lake theme. A tune that is already video-game music, such as Korobeiniki (the Tetris theme), removes the contrast that makes the experiment interesting. Major-key tunes still work: reharmonise toward the relative minor with IV–V–vi and a borrowed V7→vi cadence, as `songbie.py` does.

**Transcribe from a score, not from memory.** Find the numbered notation or staff notation, keep the scan next to your working files, and store the untouched transcription as `SOURCE`. A complete phrase matters more than hitting an exact duration: an 8-bar phrase at 140–150 BPM is about 15 s.

**Keep the skeleton and put the ZUN idioms between the skeleton notes.** The balance that worked:

- Use 3-3-2 syncopation (dotted eighth, dotted eighth, eighth) on phrases that were plain quarter notes.
- Anticipate long notes by half a beat.
- End held notes with 16th-note turns, for example C–D–C–B–C.
- Connect phrases with ascending 16th-note runs instead of rests.
- Give long trumpet notes a scoop at the attack and vibrato that fades in over the second half. `expressive_lead=True` does this.
- Add minor colour at cadences: a harmonic-minor V7 under the melody, the ♭9 tension of the melody's 4th degree held over that V7, and optionally land the last note on the minor tonic. That last choice is the typical `skeleton_allow` entry.

**Harmony.** Use the ZUN progression ♭VI–♭VII–i (in a major key, IV–V–vi) as the backbone, and use the major V (harmonic minor) for cadences. Sudden key changes are idiomatic in longer pieces, but inside a single 8-bar phrase they cost more recognisability than they add.

**Drums must sound programmed, not played.** Use constant velocity, continuous 16th-note hi-hats, syncopated 16th-note kick patterns, and, in the climax, eighth-note kicks with a crash on every beat. Transitions use 32nd-note snare bursts and descending tom runs with kicks under them. `add_mechanical_drums` implements this. Do not "improve" it with accents or ghost notes.

**Timbre is half the style.** Use trumpet (GM 56) plus piano doubling the melody an octave up, strings on block chords, 16th-note piano arpeggios, a fingered bass (GM 33), and reverb around CC91 = 55. Switching from GeneralUser GS to NeoTHFont was the single largest improvement in the reference session.

**Iterate by changing one dimension per version.** When the user gives feedback, render a version that changes only that dimension (drums only, SoundFont only, melody only) next to the previous one, so the user can tell which change produced which effect. Name versions `vN_<what changed>` with `--name`, and describe the change in one line with `--note`.

**Deliver where the user can listen and take it away.** Render with `--video` (or run `python scripts/make_videos.py out` afterwards), then serve the output folder with `python scripts/serve.py out --port <free port>` as a managed background task. The page has MP3, MP4 and MIDI download links, so the user can keep or forward any version. Verify the page by fetching it and checking that the expected version names appear; a `200` status alone is not enough. Then give the user the LAN URL.

## Known pitfalls

These all happened during the reference session.

| Pitfall | What happened | What to do |
|---|---|---|
| Assuming a famous song is public domain | A well-known 1955 Chinese children's song was proposed; its composer died in 1998, so it is protected until 2048 | Check the composer's death year and jurisdiction before transcribing |
| Over-transforming the melody | Changing to the parallel minor, adding dense ornaments and modulating mid-phrase produced something the listener called "completely unrelated to the original" | Keep the strong-beat skeleton; the skeleton check enforces this |
| Under-transforming the melody | With the melody verbatim and only harmony, drums and timbre changed, the listener said it was "too close" and lacked ZUN character | Add the melodic idioms listed above between the skeleton notes |
| Humanised drums | A standard rock beat with accents and dynamics was "obviously not ZUN" | Use constant-velocity sequencer drums |
| Blaming the writing when it is the SoundFont | A General MIDI bank made even good writing sound generic | Render with a Touhou-oriented bank before judging an arrangement |
| SoundFont download returns HTML | musical-artifacts.com sits behind a Cloudflare challenge; both `curl` and automated Chrome received a "Just a moment..." page saved as `.sf2` | `resolve_soundfont` checks the RIFF/sfbk header. Fetch the MediaFire mirror page and extract its `download…` link, or ask the user to download it in a normal browser |
| Video will not play on the phone | Python's stock `http.server` ignores Range requests, and iOS Safari refuses to play a `<video>` without 206 responses | `serve.py` implements Range; if you swap in another server, check that `curl -H 'Range: bytes=0-15'` returns 206 |
| Listening server silently gone | A server started with `nohup … &` died when its shell exited, and another process then took the port, so the URL served a different app | Run the server as a tracked background task, pick a free port, and verify the page content |

## Output specification

For each version in `out/`:

- `<name>.mid`: type-1 MIDI with tracks `Lead`, `Lead Double`, `Bass`, `Strings`, `Piano` and `Drums` (channel 10), plus `Piano Fill` when the arrangement has fills.
- `<name>.mp3`: the rendered audio, trimmed and loudness-normalised to -16 LUFS.
- `<name>.txt`: one line describing what changed relative to the previous version.
- `<name>.mp4` (optional, `--video`): the EQ-meter video with the same audio.

Each new arrangement is an `examples/<tune>.py` module exposing `ARRANGEMENT`. Its docstring states the provenance and why the melody is public domain, and the tests check for that.
