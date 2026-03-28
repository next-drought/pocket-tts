---
name: text2audio
description: Use when the user wants to turn a transcript file or pasted text into a WAV file with the local Pocket TTS fork and the default exported voice state at /Users/peteryang/DEV/pocket-tts/PYang_Voice.safetensors. Trigger for requests like "/text2audio", "convert this transcript to audio", "read this text aloud", or "generate a WAV from this sermon transcript".
---

# Text2Audio

Use the local plugin runner:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh
```

Defaults:

- Pocket TTS repo: `/Users/peteryang/DEV/pocket-tts`
- Voice state: `/Users/peteryang/DEV/pocket-tts/PYang_Voice.safetensors`

Common commands:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --transcript-file /path/to/transcript.txt \
  --output /path/to/output.wav
```

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --text "Read this paragraph aloud." \
  --output /path/to/output.wav
```

Extra arguments after the required input/output flags are passed through to `transcript_to_audio_pocket.py`.

Examples:

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --transcript-file /path/to/transcript.txt \
  --output /path/to/output.wav \
  --max-tokens 50
```

```bash
/Users/peteryang/plugins/text2audio/scripts/text2audio.sh \
  --text "Hello world" \
  --output ./hello.wav \
  --temperature 0.7
```

If the user only provides text in chat, write it to a temporary file or use `--text` directly through the runner.
