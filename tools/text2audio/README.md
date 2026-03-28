# Text2Audio AI Integration

This folder mirrors the working local `text2audio` plugin and Codex skill so the setup can be versioned inside the repo.

## Included Files

- `.codex-plugin/plugin.json`: local plugin manifest
- `scripts/text2audio.sh`: runner that calls `transcript_to_audio_pocket.py`
- `skills/text2audio/SKILL.md`: Codex skill instructions
- `skills/text2audio/agents/openai.yaml`: Codex UI metadata
- `marketplace.example.json`: example marketplace entry for home-local plugin installation

## Runner Usage

Transcript file:

```bash
./tools/text2audio/scripts/text2audio.sh \
  --transcript-file /path/to/transcript.txt \
  --output /path/to/output.wav
```

Inline text:

```bash
./tools/text2audio/scripts/text2audio.sh \
  --text "Read this paragraph aloud." \
  --output /path/to/output.wav
```

The runner defaults to:

- repo: the current repo when executed from this checkout, otherwise `POCKET_TTS_REPO` or `/Users/peteryang/DEV/pocket-tts`
- voice state: `${TEXT2AUDIO_VOICE_STATE:-$POCKET_TTS_REPO/PYang_Voice.safetensors}`

## Install Into Codex

Copy or symlink the skill into `~/.codex/skills`:

```bash
mkdir -p ~/.codex/skills/text2audio
cp /Users/peteryang/DEV/pocket-tts/tools/text2audio/skills/text2audio/SKILL.md ~/.codex/skills/text2audio/SKILL.md
mkdir -p ~/.codex/skills/text2audio/agents
cp /Users/peteryang/DEV/pocket-tts/tools/text2audio/skills/text2audio/agents/openai.yaml ~/.codex/skills/text2audio/agents/openai.yaml
```

Then restart or reload Codex so it rescans installed skills.

Typical trigger styles:

- `/text2audio`
- `$text2audio`
- natural language such as `convert this transcript to audio`

Whether `/text2audio` appears in slash autocomplete depends on the Codex client UI.

## Install As A Local Codex Plugin

Copy or symlink the plugin directory:

```bash
mkdir -p ~/plugins
cp -R /Users/peteryang/DEV/pocket-tts/tools/text2audio ~/plugins/text2audio
chmod +x ~/plugins/text2audio/scripts/text2audio.sh
```

Create or update `~/.agents/plugins/marketplace.json` using `marketplace.example.json` as the model.

## Use From Claude Code

Claude Code does not automatically consume Codex skills or plugin manifests.

Use the same runner script directly:

```bash
/Users/peteryang/DEV/pocket-tts/tools/text2audio/scripts/text2audio.sh \
  --transcript-file /path/to/transcript.txt \
  --output /path/to/output.wav
```

If you want a Claude-side shortcut, wrap the same runner in a Claude custom command.
