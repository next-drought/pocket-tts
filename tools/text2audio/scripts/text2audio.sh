#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  text2audio.sh --transcript-file PATH --output PATH [extra Pocket TTS args]
  text2audio.sh --text "..." --output PATH [extra Pocket TTS args]

Options:
  --transcript-file PATH   Input transcript file.
  --text TEXT              Inline text to convert into audio.
  --output PATH            Output WAV path. If omitted, a timestamped WAV is written to the current directory.
  --voice-state PATH       Override the default exported voice state.
  --repo PATH              Override the Pocket TTS repo path.
  --help                   Show this help.

Any remaining arguments are passed through to transcript_to_audio_pocket.py.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_FROM_SCRIPT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

POCKET_TTS_REPO="${POCKET_TTS_REPO:-}"
if [[ -z "${POCKET_TTS_REPO}" ]]; then
  if [[ -f "${REPO_FROM_SCRIPT}/transcript_to_audio_pocket.py" ]]; then
    POCKET_TTS_REPO="${REPO_FROM_SCRIPT}"
  else
    POCKET_TTS_REPO="/Users/peteryang/DEV/pocket-tts"
  fi
fi

VOICE_STATE="${TEXT2AUDIO_VOICE_STATE:-${POCKET_TTS_REPO}/PYang_Voice.safetensors}"
TRANSCRIPT_FILE=""
TEXT_INPUT=""
OUTPUT_PATH=""
EXTRA_ARGS=()
TEMP_TRANSCRIPT=""

while (($#)); do
  case "$1" in
    --transcript-file)
      TRANSCRIPT_FILE="$2"
      shift 2
      ;;
    --text)
      TEXT_INPUT="$2"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --voice-state)
      VOICE_STATE="$2"
      shift 2
      ;;
    --repo)
      POCKET_TTS_REPO="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -n "$TRANSCRIPT_FILE" && -n "$TEXT_INPUT" ]]; then
  echo "Use either --transcript-file or --text, not both." >&2
  exit 1
fi

if [[ -z "$TRANSCRIPT_FILE" && -z "$TEXT_INPUT" ]]; then
  echo "You must provide --transcript-file or --text." >&2
  usage >&2
  exit 1
fi

if [[ ! -d "$POCKET_TTS_REPO" ]]; then
  echo "Pocket TTS repo not found: $POCKET_TTS_REPO" >&2
  exit 1
fi

if [[ ! -f "$VOICE_STATE" ]]; then
  echo "Voice state not found: $VOICE_STATE" >&2
  exit 1
fi

if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$PWD/text2audio-$(date +%Y%m%d-%H%M%S).wav"
fi

if [[ -n "$TEXT_INPUT" ]]; then
  TEMP_TRANSCRIPT="$(mktemp "${TMPDIR:-/tmp}/text2audio.XXXXXX.txt")"
  printf '%s\n' "$TEXT_INPUT" > "$TEMP_TRANSCRIPT"
  TRANSCRIPT_FILE="$TEMP_TRANSCRIPT"
fi

cleanup() {
  if [[ -n "$TEMP_TRANSCRIPT" && -f "$TEMP_TRANSCRIPT" ]]; then
    rm -f "$TEMP_TRANSCRIPT"
  fi
}
trap cleanup EXIT

if [[ ! -f "$TRANSCRIPT_FILE" ]]; then
  echo "Transcript file not found: $TRANSCRIPT_FILE" >&2
  exit 1
fi

CMD=(
  uv run python
  "$POCKET_TTS_REPO/transcript_to_audio_pocket.py"
  "$TRANSCRIPT_FILE"
  "$OUTPUT_PATH"
  --voice-state
  "$VOICE_STATE"
)
if ((${#EXTRA_ARGS[@]})); then
  CMD+=("${EXTRA_ARGS[@]}")
fi

(
  cd "$POCKET_TTS_REPO"
  "${CMD[@]}"
)

echo "Wrote audio to: $OUTPUT_PATH"
