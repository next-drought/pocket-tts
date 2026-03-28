import logging
from pathlib import Path

import typer

from pocket_tts.data.audio import stream_audio_chunks
from pocket_tts.default_parameters import (
    DEFAULT_EOS_THRESHOLD,
    DEFAULT_LSD_DECODE_STEPS,
    DEFAULT_NOISE_CLAMP,
    DEFAULT_TEMPERATURE,
    DEFAULT_VARIANT,
    MAX_TOKEN_PER_CHUNK,
)
from pocket_tts.models.tts_model import TTSModel, VOICE_CLONING_UNSUPPORTED, export_model_state
from pocket_tts.utils.logging_utils import enable_logging

app = typer.Typer(
    help=(
        "Generate a single WAV from a transcript file using Pocket TTS and an audio prompt "
        "or exported voice state."
    ),
    pretty_exceptions_show_locals=False,
)

DEFAULT_VOICE_PATH = Path(__file__).with_name("PYang_Voice.wav")


def _read_transcript(transcript_path: Path) -> str:
    if not transcript_path.exists():
        raise typer.BadParameter(f"Transcript file not found: {transcript_path}")

    text = transcript_path.read_text(encoding="utf-8")
    if not text.strip():
        raise typer.BadParameter(f"Transcript file is empty: {transcript_path}")

    return text


def _ensure_parent_dir(path: Path) -> None:
    if path.parent != Path():
        path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_voice_input(voice: str | None, voice_state: Path | None) -> str:
    if voice_state is not None:
        if not voice_state.exists():
            raise typer.BadParameter(f"Voice state file not found: {voice_state}")
        return str(voice_state)

    if voice:
        return voice

    if DEFAULT_VOICE_PATH.exists():
        return str(DEFAULT_VOICE_PATH)

    raise typer.BadParameter(
        "No voice input available. Pass --voice or --voice-state, or place PYang_Voice.wav "
        "next to this script."
    )


def _load_voice_state(
    model: TTSModel,
    voice: str | None,
    voice_state: Path | None,
    export_voice_state_path: Path | None,
    truncate_voice_prompt: bool,
):
    resolved_voice_input = _resolve_voice_input(voice=voice, voice_state=voice_state)
    try:
        model_state = model.get_state_for_audio_prompt(
            resolved_voice_input, truncate=truncate_voice_prompt
        )
    except ValueError as exc:
        if str(exc) != VOICE_CLONING_UNSUPPORTED:
            raise

        if resolved_voice_input.endswith(".safetensors"):
            raise typer.BadParameter(
                "The provided voice state requires voice-cloning-capable weights, but this "
                "environment only has the preset-voice model. Accept the Hugging Face terms "
                "for kyutai/pocket-tts and log in with `uvx hf auth login`, or switch to a "
                "preset voice such as `--voice alba`."
            ) from exc

        raise typer.BadParameter(
            "Custom voice cloning is unavailable in this environment. Accept the Hugging Face "
            "terms for kyutai/pocket-tts and log in with `uvx hf auth login`, then rerun with "
            "your WAV prompt. Otherwise use a preset voice such as `--voice alba`."
        ) from exc

    if export_voice_state_path is not None and not resolved_voice_input.endswith(".safetensors"):
        _ensure_parent_dir(export_voice_state_path)
        export_model_state(model_state, export_voice_state_path)

    return model_state


@app.command()
def main(
    transcript_path: Path = typer.Argument(help="Path to the input transcript text file."),
    output_path: Path = typer.Argument(help="Path to the output WAV file."),
    voice: str | None = typer.Option(
        default=str(DEFAULT_VOICE_PATH) if DEFAULT_VOICE_PATH.exists() else None,
        help="Voice prompt input. Accepts a local audio file, URL, hf:// path, or preset voice.",
    ),
    voice_state: Path | None = typer.Option(
        None,
        help="Path to an exported .safetensors voice state. If set, this is used instead of --voice.",
    ),
    export_voice_state_path: Path | None = typer.Option(
        None,
        "--export-voice-state",
        help="Optional .safetensors file to write after encoding an audio prompt.",
    ),
    truncate_voice_prompt: bool = typer.Option(
        True,
        "--truncate-voice-prompt/--no-truncate-voice-prompt",
        help="Trim audio prompts to 30 seconds before encoding.",
    ),
    config: str = typer.Option(
        DEFAULT_VARIANT, help="Model signature or path to a local config .yaml file."
    ),
    lsd_decode_steps: int = typer.Option(
        DEFAULT_LSD_DECODE_STEPS, help="Number of generation steps."
    ),
    temperature: float = typer.Option(DEFAULT_TEMPERATURE, help="Sampling temperature."),
    noise_clamp: float | None = typer.Option(DEFAULT_NOISE_CLAMP, help="Noise clamp value."),
    eos_threshold: float = typer.Option(DEFAULT_EOS_THRESHOLD, help="EOS threshold."),
    frames_after_eos: int | None = typer.Option(
        None, help="Number of frames to keep generating after EOS."
    ),
    max_tokens: int = typer.Option(
        MAX_TOKEN_PER_CHUNK, help="Maximum tokenizer-aware chunk size for long transcripts."
    ),
    quantize: bool = typer.Option(False, help="Apply int8 quantization to reduce memory usage."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable logging output."),
):
    """Generate transcript audio with reusable voice-state support."""
    _ensure_parent_dir(output_path)
    text = _read_transcript(transcript_path)

    log_level = logging.ERROR if quiet else logging.INFO
    with enable_logging("pocket_tts", log_level):
        model = TTSModel.load_model(
            config, temperature, lsd_decode_steps, noise_clamp, eos_threshold, quantize=quantize
        )
        model_state = _load_voice_state(
            model=model,
            voice=voice,
            voice_state=voice_state,
            export_voice_state_path=export_voice_state_path,
            truncate_voice_prompt=truncate_voice_prompt,
        )
        audio_chunks = model.generate_audio_stream(
            model_state=model_state,
            text_to_generate=text,
            max_tokens=max_tokens,
            frames_after_eos=frames_after_eos,
        )
        stream_audio_chunks(output_path, audio_chunks, model.sample_rate)


if __name__ == "__main__":
    app()
