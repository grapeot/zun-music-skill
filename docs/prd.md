# PRD — zun-music-skill

## Problem

People who like ZUN's Touhou soundtrack sound want to hear a familiar tune "as if ZUN had written it". A coding agent can write MIDI, but left alone it produces generic results: it either copies the source verbatim (recognisable but not ZUN) or rewrites it so heavily (minor key + ornaments + modulation) that the source disappears. Rendering with a default General MIDI SoundFont also hides most of the character, because a large part of the ZUN sound is the Roland SC-88Pro / SD-90 era timbre.

## Users

- A person with a coding agent (Claude Code, Codex, Cursor, OpenCode, …) who asks for "a ZUN-style arrangement of <tune>".
- The agent itself, which needs a reusable toolkit plus a skill document that encodes what actually makes an arrangement sound like ZUN.

## Requirements

1. Pick a source melody that is public domain and suits the style; refuse or substitute copyrighted sources.
2. Transcribe the source faithfully and keep its strong-beat skeleton in the arrangement so it stays recognisable.
3. Apply ZUN idioms on top: ZUN progression (♭VI–♭VII–i / IV–V–vi), 3-3-2 syncopation, anticipations, 16th-note turns and runs, trumpet scoop + vibrato, mechanical sequencer drums, driving eighth-note bass, piano arpeggios, strings pad.
4. Render to audio with FluidSynth using a Touhou-oriented SoundFont.
5. Let the user compare versions quickly, including from a phone on the same network.

## Success criteria

- Automated: every arrangement passes the bar-length check and the skeleton check (strong-beat pitches match the transcription, allowing the documented exceptions), and the drum track has constant velocity.
- Human: a listener recognises the source tune within the first phrase and also hears it as "ZUN-like". Only the user can judge this; the agent must deliver audio and ask.

## Non-goals

- Reproducing any specific Touhou track or sampling ZUN's recordings.
- A DAW or notation editor. Output is MIDI + rendered audio.
- Distributing SoundFonts.
