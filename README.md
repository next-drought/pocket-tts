# Pocket TTS Fork

This fork is set up for transcript-to-audio generation with a reusable custom voice state.

The key upgrade in this repo is:

- `transcript_to_audio_pocket.py`: generate one final WAV from a transcript file
- `PYang_Voice.safetensors`: exported Pocket TTS voice state for fast reuse
- `tests/test_transcript_to_audio_pocket.py`: focused coverage for the wrapper

## What This Repo Is For

Use this repo when you want to:

- generate audio from a long transcript file
- use Pocket TTS instead of manual chunk concatenation logic
- reuse a pre-exported custom voice state
- keep the workflow CPU-friendly and simple

## Files Added In This Fork

- `transcript_to_audio_pocket.py`
- `PYang_Voice.safetensors`
- `tests/test_transcript_to_audio_pocket.py`

## Environment

This project uses `uv`.

Install dependencies:

```bash
uv sync
```

If you need the optional audio dependency:

```bash
uv sync --extra audio
```

## Hugging Face Access

Custom voice cloning requires access to the gated `kyutai/pocket-tts` model.

If you need to log in:

```bash
uvx hf auth login --force
```

To verify direct gated access:

```bash
uvx hf download kyutai/pocket-tts tts_b6369a24.safetensors
```

If this fails, you either:

- have not accepted access for `https://huggingface.co/kyutai/pocket-tts`
- or are logged in with the wrong Hugging Face account

## Export A Custom Voice State

If you have a prompt WAV and gated access is working:

```bash
uv run pocket-tts export-voice ./PYang_Voice.wav ./PYang_Voice.safetensors
```

Successful output means the audio prompt was encoded and the `.safetensors` file can now be reused directly.

## Generate Transcript Audio

### Recommended: use the exported voice state

```bash
uv run python transcript_to_audio_pocket.py \
  ./03292026_transcript.txt \
  ./out_pyang.wav \
  --voice-state ./PYang_Voice.safetensors
```

This is the main upgraded workflow in this repo.

### Use a raw voice prompt WAV

```bash
uv run python transcript_to_audio_pocket.py \
  ./03292026_transcript.txt \
  ./out_pyang.wav \
  --voice ./PYang_Voice.wav
```

This is slower because the audio prompt has to be encoded each run.

### Use a preset voice

```bash
uv run python transcript_to_audio_pocket.py \
  ./03292026_transcript.txt \
  ./out_charles.wav \
  --voice charles
```

Preset voices work even when custom voice cloning access is unavailable.

## Use From AI Tools

This repo can also be used from AI coding tools through the local runner and skill/plugin setup created on the machine.

### Local runner

The reusable runner lives at:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh
```

It defaults to:

- Pocket TTS repo: `/Users/peteryang/DEV/pocket-tts`
- voice state: `/Users/peteryang/DEV/pocket-tts/PYang_Voice.safetensors`

Runner examples:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --transcript-file /Users/peteryang/DEV/pocket-tts/03292026_transcript.txt \
  --output /Users/peteryang/DEV/pocket-tts/out_ai.wav
```

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --text "Hello world from Pocket TTS." \
  --output /Users/peteryang/DEV/pocket-tts/hello_ai.wav
```

### Codex

A local plugin and installed Codex skill were created for this workflow.

Paths:

- plugin manifest: `/Users/peteryang/plugins/text2audio/.codex-plugin/plugin.json`
- plugin runner: `/Users/peteryang/plugins/text2audio/scripts/text2audio.sh`
- Codex skill: `/Users/peteryang/.codex/skills/text2audio/SKILL.md`
- Codex skill metadata: `/Users/peteryang/.codex/skills/text2audio/agents/openai.yaml`
- local marketplace entry: `/Users/peteryang/.agents/plugins/marketplace.json`

After restarting or reloading the Codex client, the skill can be triggered in one of these ways:

- type `/text2audio`
- invoke `$text2audio`
- ask naturally, for example: "convert this transcript to audio"

Important:

- whether `/text2audio` appears in slash-command autocomplete depends on the Codex client UI
- the skill is installed correctly, but some clients only rescan skills on restart

### Claude Code

Claude Code does not automatically reuse Codex skills or plugin manifests.

The practical way to use the same capability in Claude Code is to call the same local runner script directly:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --transcript-file /path/to/transcript.txt \
  --output /path/to/output.wav
```

or:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --text "Read this paragraph aloud." \
  --output /path/to/output.wav
```

If you want a Claude-side shortcut later, build it as a Claude custom command that wraps this same runner.

## Script Options

Basic form:

```bash
uv run python transcript_to_audio_pocket.py TRANSCRIPT_PATH OUTPUT_WAV [options]
```

Useful options:

- `--voice <name-or-path>`: preset voice, local audio file, URL, or `hf://` path
- `--voice-state <path>`: use an exported `.safetensors` voice state
- `--export-voice-state <path>`: export a `.safetensors` file after encoding a WAV prompt
- `--truncate-voice-prompt / --no-truncate-voice-prompt`
- `--temperature <float>`
- `--lsd-decode-steps <int>`
- `--eos-threshold <float>`
- `--frames-after-eos <int>`
- `--max-tokens <int>`
- `--quantize`
- `-q / --quiet`

Example:

```bash
uv run python transcript_to_audio_pocket.py \
  ./03292026_transcript.txt \
  ./out.wav \
  --voice ./PYang_Voice.wav \
  --export-voice-state ./PYang_Voice.safetensors \
  --temperature 0.7 \
  --max-tokens 50
```

## Testing

Run the focused wrapper tests:

```bash
uv run pytest tests/test_transcript_to_audio_pocket.py -v
```

## Current Status

What is confirmed in this fork:

- transcript file -> final WAV works
- preset voice generation works
- custom voice export to `.safetensors` works
- reusable custom voice-state loading works

What still needs subjective evaluation per transcript:

- voice similarity vs Chatterbox
- pacing and prosody
- long-sermon quality
- whether Pocket TTS should fully replace the existing Chatterbox pipeline

## Notes

- `PYang_Voice.safetensors` is tracked in this fork for convenience.
- `03292026_transcript.txt` is not committed by default.
- This README describes the forked workflow, not the original upstream project documentation.
