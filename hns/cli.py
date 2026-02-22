import json
import os
import re
import shutil
import sys
import threading
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import click
import numpy as np
import pyperclip
import sounddevice as sd
from rich.console import Console

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

console = Console(stderr=True)
stdout_console = Console()


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS format."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def get_default_save_dir() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Roaming" / "hns" / "Recordings"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "hns" / "recordings"
    else:
        return Path.home() / ".local" / "share" / "hns" / "recordings"


def load_config() -> dict:
    config_path = Path.home() / ".config" / "hns" / "config.toml"
    if not config_path.exists():
        return {}
    try:
        with config_path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        console.print(f"⚠️ [bold yellow]Could not parse config file {config_path}: {e}[/bold yellow]")
        return {}


def save_recording(
    wav_source: Path,
    text: str,
    model_name: str,
    language: Optional[str],
    audio_duration: Optional[float],
    transcription_time: Optional[float],
    save_dir: Path,
    recorded_at: datetime,
) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    timestamp = recorded_at.strftime("%Y%m%d%H%M")
    words = re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
    slug = "_".join(words[:5]) if words else "no_speech"
    stem = f"{timestamp}_{slug}"

    wav_dest = save_dir / f"{stem}.wav"
    json_dest = save_dir / f"{stem}.json"

    try:
        shutil.copy2(wav_source, wav_dest)
    except Exception as e:
        console.print(f"⚠️ [bold yellow]Failed to save WAV recording: {e}[/bold yellow]")

    try:
        metadata = {
            "text": text,
            "model": model_name,
            "language": language,
            "recorded_at": recorded_at.isoformat(),
            "audio_duration_seconds": audio_duration,
            "transcription_time_seconds": transcription_time,
            "wav_file": f"{stem}.wav",
        }
        json_dest.write_text(json.dumps(metadata, indent=2))
    except Exception as e:
        console.print(f"⚠️ [bold yellow]Failed to save transcript JSON: {e}[/bold yellow]")


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_file_path = self._get_audio_file_path()
        self.wave_file = None
        self.recording_frames = 0

    def _audio_callback(self, indata, frames, time, status):
        if status:
            console.print(f"⚠️ [bold yellow]Audio warning: {status}[/bold yellow]")
        if self.wave_file:
            audio_int16 = (indata * 32767).astype(np.int16)
            self.wave_file.writeframes(audio_int16.tobytes())
            self.recording_frames += frames

    def record(self) -> Path:
        self._validate_audio_device()
        self._prepare_wave_file()

        try:
            stream = sd.InputStream(
                samplerate=self.sample_rate, channels=self.channels, callback=self._audio_callback, dtype=np.float32
            )
        except Exception as e:
            self._close_wave_file()
            raise RuntimeError(f"Failed to initialize audio stream: {e}")

        # Setup timer for live recording display
        start_time = time.time()
        recording_stopped = threading.Event()

        try:
            with stream:

                def update_timer():
                    """Update the display with elapsed time."""
                    while not recording_stopped.is_set():
                        elapsed = time.time() - start_time
                        time_str = format_duration(elapsed)
                        # Overwrite the same line
                        console.print(
                            f"🎤 [bold blue]Recording ...... {time_str} Press Enter to stop[/bold blue]", end="\r"
                        )
                        time.sleep(1)

                # Start timer thread
                timer_thread = threading.Thread(target=update_timer)
                timer_thread.daemon = True
                timer_thread.start()

                # Wait for user input
                input()

                # Stop timer and wait for thread to finish
                recording_stopped.set()
                timer_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish

                # Clear the recording line completely
                console.print(" " * 50, end="\r")  # Clear line with spaces

        except KeyboardInterrupt:
            recording_stopped.set()
            console.print("\n⏹️ [bold yellow]Recording cancelled[/bold yellow]")
            self._close_wave_file()
            sys.exit(0)
        finally:
            recording_stopped.set()
            self._close_wave_file()

        if self.recording_frames == 0:
            raise ValueError("No audio recorded")

        return self.audio_file_path

    def _validate_audio_device(self):
        try:
            default_input = sd.query_devices(kind="input")
            if default_input is None:
                raise RuntimeError("No audio input device found")
        except Exception as e:
            raise RuntimeError(f"Failed to access audio devices: {e}")

    def _get_audio_file_path(self) -> Path:
        if sys.platform == "win32":
            cache_dir = Path.home() / "AppData" / "Local" / "hns" / "Cache"
        elif sys.platform == "darwin":
            cache_dir = Path.home() / "Library" / "Caches" / "hns"
        else:
            cache_dir = Path.home() / ".cache" / "hns"

        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "last_recording.wav"

    def _prepare_wave_file(self):
        self.recording_frames = 0
        self.wave_file = wave.open(str(self.audio_file_path), "wb")
        self.wave_file.setnchannels(self.channels)
        self.wave_file.setsampwidth(2)  # 16-bit audio
        self.wave_file.setframerate(self.sample_rate)

    def _close_wave_file(self):
        if self.wave_file:
            self.wave_file.close()
            self.wave_file = None


class WhisperTranscriber:
    VALID_MODELS = [
        "tiny.en",
        "tiny",
        "base.en",
        "base",
        "small.en",
        "small",
        "medium.en",
        "medium",
        "large-v1",
        "large-v2",
        "large-v3",
        "large",
        "distil-large-v2",
        "distil-medium.en",
        "distil-small.en",
        "distil-large-v3",
        "distil-large-v3.5",
        "large-v3-turbo",
        "turbo",
    ]

    def __init__(self, model_name: Optional[str] = None, language: Optional[str] = None):
        self.model_name = self._get_model_name(model_name)
        self.language = language or os.environ.get("HNS_LANG")
        self.model = self._load_model()

    def _get_audio_duration(self, audio_file_path: Union[Path, str]) -> Optional[float]:
        """Get duration of audio file in seconds."""
        try:
            with wave.open(str(audio_file_path), "rb") as audio_file:
                frames = audio_file.getnframes()
                sample_rate = audio_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception:
            return None

    def _get_model_name(self, model_name: Optional[str]) -> str:
        model = model_name or os.environ.get("HNS_WHISPER_MODEL", "base")

        if model not in self.VALID_MODELS:
            console.print(f"⚠️ [bold yellow]Invalid model '{model}', using 'base' instead[/bold yellow]")
            console.print(f"    [dim]Available models: {', '.join(self.VALID_MODELS)}[/dim]")
            return "base"

        return model

    def _load_model(self):
        from faster_whisper import WhisperModel

        try:
            return WhisperModel(self.model_name, device="cpu", compute_type="int8")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def transcribe(self, audio_source: Union[Path, str], show_progress: bool = True) -> str:
        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": {"min_silence_duration_ms": 500, "speech_pad_ms": 400, "threshold": 0.5},
        }

        if self.language:
            transcribe_kwargs["language"] = self.language

        try:
            start_time = time.time()

            if show_progress:
                import queue
                import threading

                progress_queue = queue.Queue()
                transcription_complete = threading.Event()

                def transcribe_worker():
                    """Worker function to perform transcription in background."""
                    try:
                        segments, _ = self.model.transcribe(str(audio_source), **transcribe_kwargs)
                        transcription_parts = []
                        for segment in segments:
                            text = segment.text.strip()
                            if text:
                                transcription_parts.append(text)
                        progress_queue.put(("result", transcription_parts))
                    except Exception as e:
                        progress_queue.put(("error", e))
                    finally:
                        transcription_complete.set()

                # Start transcription in background
                worker_thread = threading.Thread(target=transcribe_worker)
                worker_thread.daemon = True
                worker_thread.start()

                # Simple progress display with elapsed timer
                while not transcription_complete.is_set():
                    elapsed = time.time() - start_time
                    time_str = format_duration(elapsed)
                    console.print(f"🔄 [bold blue]Transcribing ... {time_str}[/bold blue]", end="\r")
                    time.sleep(1)

                # Print a new line
                console.print("")

                result_type, result_data = progress_queue.get()
                if result_type == "error":
                    raise result_data
                transcription_parts = result_data
            else:
                segments, _ = self.model.transcribe(str(audio_source), **transcribe_kwargs)
                transcription_parts = []
                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        transcription_parts.append(text)

            full_transcription = " ".join(transcription_parts)
            if not full_transcription:
                raise ValueError("No speech detected in audio")

            elapsed_total = time.time() - start_time
            return full_transcription, elapsed_total if show_progress else None
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    @classmethod
    def list_models(cls):
        console.print("ℹ️ [bold cyan]Available Whisper models:[/bold cyan]")
        for model in cls.VALID_MODELS:
            console.print(f"  • [dim]{model}[/dim]")
        console.print("\nℹ️ [bold cyan]Environment variables:[/bold cyan]")
        console.print("  [dim]export HNS_WHISPER_MODEL=<model-name>[/dim]")
        console.print("  [dim]export HNS_LANG=<language-code>  # e.g., en, es, fr[/dim]")


def copy_to_clipboard(text: str):
    pyperclip.copy(text)
    console.print("✅ [bold green]Copied to clipboard![/bold green]")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--sample-rate", default=16000, help="Sample rate for audio recording")
@click.option("--channels", default=1, help="Number of audio channels")
@click.option("--list-models", is_flag=True, help="List available Whisper models and exit")
@click.option("--model", help="Whisper model to use. Can also use HNS_WHISPER_MODEL env var")
@click.option("--language", help="Force language detection (e.g., en, es, fr). Can also use HNS_LANG env var")
@click.option("--last", is_flag=True, help="Transcribe the last recorded audio file")
def main(
    ctx: click.Context,
    sample_rate: int,
    channels: int,
    list_models: bool,
    model: Optional[str],
    language: Optional[str],
    last: bool,
):
    """Record audio from microphone, transcribe it, and copy to clipboard."""

    if ctx.invoked_subcommand is not None:
        return

    if list_models:
        WhisperTranscriber.list_models()
        return

    try:
        cfg = load_config()
        resolved_model = model or os.environ.get("HNS_WHISPER_MODEL") or cfg.get("model") or "base"
        resolved_language = language or os.environ.get("HNS_LANG") or cfg.get("language") or None
        raw_save_dir = cfg.get("save_dir")
        save_dir = Path(raw_save_dir).expanduser() if raw_save_dir else get_default_save_dir()

        recorded_at = datetime.now()

        if last:
            recorder = AudioRecorder(sample_rate, channels)
            audio_file_path = recorder._get_audio_file_path()
            if not audio_file_path.exists():
                console.print(
                    "❌ [bold red]No previous recording found. Record audio first by running 'hns' without --last flag.[/bold red]"
                )
                sys.exit(1)
        else:
            recorder = AudioRecorder(sample_rate, channels)
            audio_file_path = recorder.record()

        transcriber = WhisperTranscriber(model_name=resolved_model, language=resolved_language)
        audio_duration = transcriber._get_audio_duration(audio_file_path)
        transcription, transcription_time = transcriber.transcribe(audio_file_path, show_progress=True)

        try:
            copy_to_clipboard(transcription)
        except Exception as e:
            console.print(f"⚠️ [bold yellow]Failed to copy to clipboard: {e}[/bold yellow]")

        try:
            save_recording(
                audio_file_path,
                transcription,
                resolved_model,
                resolved_language,
                audio_duration,
                transcription_time,
                save_dir,
                recorded_at,
            )
        except Exception as e:
            console.print(f"⚠️ [bold yellow]Failed to save recording: {e}[/bold yellow]")

        stdout_console.print(transcription)

    except (RuntimeError, ValueError) as e:
        console.print(f"❌ [bold red]{e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


def _show_config():
    cfg = load_config()
    env_model = os.environ.get("HNS_WHISPER_MODEL")
    env_lang = os.environ.get("HNS_LANG")

    config_file = Path.home() / ".config" / "hns" / "config.toml"
    console.print("[bold cyan]Current Configuration[/bold cyan]")

    if config_file.exists():
        console.print(f"  Config file: {config_file}")
    else:
        console.print(f"  Config file: {config_file} [dim](not yet created)[/dim]")

    console.print("\n[bold cyan]Settings (in priority order):[/bold cyan]")
    console.print("  1. Command-line options (--model, --language, etc.)")
    console.print("  2. Environment variables (HNS_WHISPER_MODEL, HNS_LANG)")
    console.print(f"  3. Config file ({config_file})")
    console.print("  4. Built-in defaults (model: base, language: auto-detect)")

    resolved_model = os.environ.get("HNS_WHISPER_MODEL") or cfg.get("model") or "base"
    resolved_language = os.environ.get("HNS_LANG") or cfg.get("language") or None
    raw_save_dir = cfg.get("save_dir")
    resolved_save_dir = Path(raw_save_dir).expanduser() if raw_save_dir else get_default_save_dir()

    console.print("\n[bold cyan]Effective configuration:[/bold cyan]")
    console.print(f"  Model: {resolved_model}")
    console.print(f"  Language: {resolved_language or '(auto-detect)'}")
    console.print(f"  Save directory: {resolved_save_dir}")

    if env_model or env_lang:
        console.print("\n[bold cyan]Active environment variables:[/bold cyan]")
        if env_model:
            console.print(f"  HNS_WHISPER_MODEL={env_model}")
        if env_lang:
            console.print(f"  HNS_LANG={env_lang}")

    if config_file.exists():
        console.print("\n[bold cyan]Config file contents:[/bold cyan]")
        console.print(config_file.read_text())


def _write_config(model: Optional[str], language: Optional[str], save_dir: Optional[str]):
    config_file = Path.home() / ".config" / "hns" / "config.toml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    cfg = load_config()
    if model is not None:
        cfg["model"] = model
    if language is not None:
        cfg["language"] = language
    if save_dir is not None:
        cfg["save_dir"] = save_dir

    toml_lines = []
    if "model" in cfg:
        toml_lines.append(f'model = "{cfg["model"]}"')
    if "language" in cfg:
        lang_val = f'"{cfg["language"]}"' if cfg["language"] else "null"
        toml_lines.append(f"language = {lang_val}")
    if "save_dir" in cfg:
        toml_lines.append(f'save_dir = "{cfg["save_dir"]}"')

    config_file.write_text("\n".join(toml_lines) + "\n" if toml_lines else "")
    console.print(f"✅ [bold green]Config saved to {config_file}[/bold green]")
    _show_config()


@main.command("config")
@click.option("--model", help="Set the default Whisper model")
@click.option("--language", help="Set the default language code")
@click.option("--save-dir", help="Set the directory for saving recordings")
@click.option("--show", is_flag=True, help="Show current configuration")
def config_cmd(model: Optional[str], language: Optional[str], save_dir: Optional[str], show: bool):
    """Manage hns configuration."""
    if show or (not model and not language and not save_dir):
        _show_config()
    else:
        _write_config(model, language, save_dir)


if __name__ == "__main__":
    main()
