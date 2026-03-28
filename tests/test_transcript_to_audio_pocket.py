from pathlib import Path

import pytest
import torch
from typer.testing import CliRunner

import transcript_to_audio_pocket
from pocket_tts.data.audio import audio_read

runner = CliRunner()


class FakeModel:
    def __init__(self):
        self.sample_rate = 24000
        self.voice_inputs = []
        self.generated = []

    def get_state_for_audio_prompt(self, voice_input, truncate=False):
        self.voice_inputs.append((voice_input, truncate))
        return {"voice_input": voice_input}

    def generate_audio_stream(
        self,
        model_state,
        text_to_generate,
        max_tokens,
        frames_after_eos,
    ):
        self.generated.append((model_state, text_to_generate, max_tokens, frames_after_eos))
        yield torch.zeros(2400)
        yield torch.ones(2400) * 0.1


class FakeNoVoiceCloneModel(FakeModel):
    def get_state_for_audio_prompt(self, voice_input, truncate=False):
        raise ValueError(transcript_to_audio_pocket.VOICE_CLONING_UNSUPPORTED)


@pytest.fixture
def fake_model(monkeypatch):
    model = FakeModel()

    def fake_load_model(*args, **kwargs):
        return model

    monkeypatch.setattr(transcript_to_audio_pocket.TTSModel, "load_model", fake_load_model)
    return model


@pytest.fixture
def fake_no_voice_clone_model(monkeypatch):
    model = FakeNoVoiceCloneModel()

    def fake_load_model(*args, **kwargs):
        return model

    monkeypatch.setattr(transcript_to_audio_pocket.TTSModel, "load_model", fake_load_model)
    return model


def test_transcript_cli_uses_voice_prompt_and_exports_state(tmp_path, monkeypatch, fake_model):
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text("First line.\nSecond line.", encoding="utf-8")
    output_path = tmp_path / "output.wav"
    export_path = tmp_path / "voice_state.safetensors"

    exported = {}

    def fake_export_model_state(model_state, dest):
        exported["model_state"] = model_state
        exported["dest"] = dest
        Path(dest).write_bytes(b"fake")

    monkeypatch.setattr(transcript_to_audio_pocket, "export_model_state", fake_export_model_state)

    result = runner.invoke(
        transcript_to_audio_pocket.app,
        [
            str(transcript_path),
            str(output_path),
            "--voice",
            "voice.wav",
            "--export-voice-state",
            str(export_path),
        ],
    )

    assert result.exit_code == 0
    assert fake_model.voice_inputs == [("voice.wav", True)]
    assert exported["model_state"] == {"voice_input": "voice.wav"}
    assert exported["dest"] == export_path
    assert output_path.exists()

    audio, sample_rate = audio_read(output_path)
    assert audio.shape[1] > 0
    assert sample_rate == 24000
    assert fake_model.generated[0][1] == "First line.\nSecond line."


def test_transcript_cli_prefers_voice_state_file(tmp_path, monkeypatch, fake_model):
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text("Transcript text.", encoding="utf-8")
    output_path = tmp_path / "output.wav"
    voice_state_path = tmp_path / "voice_state.safetensors"
    voice_state_path.write_bytes(b"fake")

    export_called = {"value": False}

    def fake_export_model_state(*args, **kwargs):
        export_called["value"] = True

    monkeypatch.setattr(transcript_to_audio_pocket, "export_model_state", fake_export_model_state)

    result = runner.invoke(
        transcript_to_audio_pocket.app,
        [
            str(transcript_path),
            str(output_path),
            "--voice-state",
            str(voice_state_path),
            "--voice",
            "voice.wav",
        ],
    )

    assert result.exit_code == 0
    assert fake_model.voice_inputs == [(str(voice_state_path), True)]
    assert export_called["value"] is False
    assert output_path.exists()


def test_transcript_cli_rejects_empty_transcript(tmp_path):
    transcript_path = tmp_path / "empty.txt"
    transcript_path.write_text("   \n", encoding="utf-8")
    output_path = tmp_path / "output.wav"

    result = runner.invoke(
        transcript_to_audio_pocket.app,
        [
            str(transcript_path),
            str(output_path),
            "--voice",
            "voice.wav",
        ],
    )

    assert result.exit_code != 0
    assert "Transcript file is empty" in result.stderr


def test_transcript_cli_reports_voice_cloning_blocker(tmp_path, fake_no_voice_clone_model):
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text("Transcript text.", encoding="utf-8")
    output_path = tmp_path / "output.wav"

    result = runner.invoke(
        transcript_to_audio_pocket.app,
        [
            str(transcript_path),
            str(output_path),
            "--voice",
            "voice.wav",
        ],
    )

    assert result.exit_code != 0
    assert "Custom voice cloning is unavailable" in result.stderr
    assert "uvx hf" in result.stderr
    assert "auth login" in result.stderr
