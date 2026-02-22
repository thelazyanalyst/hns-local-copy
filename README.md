<p align="center">
  <a href=""><img src="img/hns-github-card.png" alt="hns" width="60%"></a>
</p>
<p align="center">
    <em>Speech-to-text CLI. 100% local. Built for developers.</em>
</p>
<p align="center">
<a href="https://pypi.org/project/hns" target="_blank">
    <img src="https://img.shields.io/pypi/v/hns?color=%33FF33" alt="Package version">
</a>
<a href="https://github.com/primaprashant/hns/releases" target="_blank">
    <img src="https://img.shields.io/github/release/primaprashant/hns?color=%33FF33" alt="Package version">
</a>
<a href="https://pypi.org/project/hns" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/hns.svg?color=%33FF33" alt="Supported Python Version">
</a>
<a href="https://github.com/primaprashant/hns/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/primaprashant/hns.svg?color=%33FF33" alt="License">
</a>
</p>

---

> **This is a fork of the excellent [primaprashant/hns](https://github.com/primaprashant/hns) project.** It extends the original with automatic local file saving — every recording is stored as a named WAV + JSON pair in its own dated folder, making it easy to build a personal voice knowledge base, review past transcriptions, and feed multiple recordings into AI agents or pipelines for multi-prompt knowledge storage and retrieval.

---

hns is a speech-to-text CLI tool to transcribe your voice from your microphone directly to clipboard. Integrate hns with Claude Code, Ollama, LLM, and more CLI tools for powerful workflows.

`hns` transcribes your voice 100% locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). The whisper model is downloaded automatically on first run and after that, `hns` can be used completely offline. After transcription, the text is displayed in the terminal (written to stdout) as well as automatically copied to your clipboard, ready to be pasted anywhere with `Ctrl+V` or `Cmd+V`.

### What this fork adds

- **Automatic local saving** — every recording is saved to its own `YYYY_MM_DD_words/` folder with a `.wav` audio file and `.json` transcript
- **JSON metadata** — each transcript includes model, language, timestamps, and duration, ready for downstream processing
- **Multi-voice knowledge storage** — build up a library of recordings over time and feed them into AI agents, RAG pipelines, or search tools
- **Persistent configuration** — set your model, language, and save directory once with `hns config` instead of repeating flags
- **GPU/CUDA support** — auto-detects your GPU and uses it for faster transcription (with `--device` override)

With `hns`, you can:
- [Drive AI coding agents like Claude Code, Codex CLI, and Cursor CLI with your voice](https://hns-cli.dev/docs/drive-coding-agents/)
- [Dictate and get polished text for emails, Slack messages, and documents](https://hns-cli.dev/docs/voice-to-polished-text/)
- [Speak freely in a stream-of-consciousness style and get polished, coherent journal entry or note](https://hns-cli.dev/docs/effortless-daily-journaling/)

...and much more! Just integrate `hns` with your favorite CLI tools.

## Quick Start

1. Install with `uv tool install hns` and then run `hns` in your terminal.
3. When you see `🎤 Recording...`, speak the following sentence clearly into your microphone: **"In the beginning the Universe was created. This has made a lot of people very angry and been widely regarded as a bad move"**.
4. Press `Enter` when you're done. The transcribed text will be printed to your terminal and copied directly to your clipboard, ready to be pasted anywhere with `Ctrl+V` or `Cmd+V`.

## Highlights

- **Instant Clipboard**: Transcribed text is automatically copied to your clipboard for immediate pasting
- **Composability (The Unix Way)**: Transcription is written to stdout and progress/status messages to stderr. Easy to integrate with other CLI tools
- **100% Local & Private**: Audio is processed entirely on your local machine. No data leaves your device
- **Works Offline**: After the initial model download, no internet connection is required
- **Multi-Language Support**: Transcribe in any language supported by Whisper
- **Persistent Configuration**: Set your preferred models, languages, and save locations once with `hns config`
- **Automatic Recording Storage**: Each recording is saved with a date/time-named WAV file and JSON metadata for easy retrieval and organization
- **Configurable**: Choose models, languages, and save directories via CLI, environment variables, or config file
- **Open Source** - MIT licensed, fully transparent

## Docs

- **[Overview](https://hns-cli.dev/docs/)**
- **Get Started**
  - [Quick Start](https://hns-cli.dev/docs/quick-start/): Get `hns` up and running in less than 30 seconds.
  - [Installation](https://hns-cli.dev/docs/installation/): Different ways to install `hns`, configure it, and upgrade to the latest version.
  - [Configuration](https://hns-cli.dev/docs/configuration/): Configure `hns` to match your hardware and transcription needs. Set up Whisper models and language preferences for optimal performance.
  - [CLI Reference](https://hns-cli.dev/docs/cli-reference/): Detailed reference for all available command-line options for `hns`.
- **Use Cases**
  - [Overview](https://hns-cli.dev/docs/use-cases/): Unlock powerful workflows by integrating `hns` with various CLI tools.
  - [Drive AI Coding Agents With Your Voice](https://hns-cli.dev/docs/drive-coding-agents/): Provide detailed, context-rich prompts to coding agents like Claude Code, Codex CLI, and Cursor CLI with your voice for faster development cycles.
  - [Turn Your Voice Into Polished Text](https://hns-cli.dev/docs/voice-to-polished-text/): Integrate `hns` with LLMs to transforms your raw dictation into polished text for emails, Slack messages, and documents, streamlining your daily communication.
  - [Effortless Daily Journaling With Your Voice](https://hns-cli.dev/docs/effortless-daily-journaling/): Speak freely in a stream-of-consciousness style and get polished, coherent journal entries or notes by integrating `hns` with LLMs.

## Usage

![use-cases-command-examples](img/hero-command-examples-dark.png)

## CLI Reference

```
Usage: hns [OPTIONS] COMMAND [ARGS]...

  Record audio from microphone, transcribe it, and copy to clipboard.

Options:
  --sample-rate INTEGER  Sample rate for audio recording  [default: 16000]
  --channels INTEGER     Number of audio channels  [default: 1]
  --list-models          List available Whisper models and exit
  --model TEXT           Whisper model to use. Can also use HNS_WHISPER_MODEL env var
  --language TEXT        Force language detection (e.g., en, es, fr). Can also use HNS_LANG env var
  --last                 Transcribe the last recorded audio file
  --help                 Show this message and exit.

Commands:
  config  Manage hns configuration.

Examples:
  hns                              Record and transcribe using default settings
  hns --model small                Use the small Whisper model
  hns --language en                Force English transcription
  hns --last                       Re-transcribe the last recorded audio
  hns --model medium --language fr Record and transcribe in French
  hns config --show                Show current configuration
  hns config --model small         Set default model to 'small'
  hns config --save-dir ~/notes    Save recordings to ~/notes
  hns --list-models                List all available Whisper models
```

### `hns config` subcommand

```
Usage: hns config [OPTIONS]

  Manage hns configuration.

Options:
  --model TEXT     Set the default Whisper model
  --language TEXT  Set the default language code
  --save-dir TEXT  Set the directory for saving recordings
  --show           Show current configuration
  --help           Show this message and exit.
```

## Configuration

hns supports persistent configuration so you set your preferences once and they apply to every future recording.

### View Current Configuration
```bash
hns config --show
```

Shows your effective configuration, active environment variables, config file contents, and the priority order for how settings are resolved.

### Set Configuration
```bash
# Set default Whisper model
hns config --model small

# Set default language
hns config --language en

# Set directory for saving recordings
hns config --save-dir ~/my-recordings

# Combine multiple settings at once
hns config --model base --language en --save-dir ~/hns-recordings
```

### Configuration File
Settings are stored in `~/.config/hns/config.toml`:
```toml
model = "small"
language = "en"
save_dir = "/home/user/my-recordings"
```

You can edit this file directly. Valid keys are `model`, `language`, and `save_dir`.

### Available Models

| Model | Size | Notes |
|-------|------|-------|
| `tiny.en` / `tiny` | ~75MB | Fastest, least accurate |
| `base.en` / `base` | ~145MB | Default — good balance |
| `small.en` / `small` | ~465MB | Better accuracy |
| `medium.en` / `medium` | ~1.5GB | High accuracy |
| `large-v3` / `turbo` | ~3GB | Best accuracy, slowest |
| `distil-large-v3` | ~1.5GB | Distilled, fast + accurate |

Run `hns --list-models` to see the full list.

### Priority Order
Settings are resolved in this order (highest to lowest priority):
1. **Command-line options** (`--model`, `--language`, etc.)
2. **Environment variables** (`HNS_WHISPER_MODEL`, `HNS_LANG`)
3. **Config file** (`~/.config/hns/config.toml`)
4. **Built-in defaults** (model: `base`, language: auto-detect)

### Environment Variables
```bash
export HNS_WHISPER_MODEL=small   # Set default model
export HNS_LANG=en               # Force language (ISO 639-1 code)
```

## Recording Storage

Each recording is automatically saved in its own subfolder named `YYYY_MM_DD_words/`, containing both the audio and a JSON metadata file:

```
~/recordings/
└── 2026_02_22_hello_world_this_is_a/
    ├── 2026_02_22_hello_world_this_is_a.wav
    └── 2026_02_22_hello_world_this_is_a.json
```

The JSON metadata contains:
```json
{
  "text": "Hello world, this is a test.",
  "model": "base",
  "language": "en",
  "recorded_at": "2026-02-22T10:30:00",
  "audio_duration_seconds": 3.2,
  "transcription_time_seconds": 1.1,
  "wav_file": "2026_02_22_hello_world_this_is_a.wav"
}
```

### Default Save Locations
- **Linux**: `~/.local/share/hns/recordings/`
- **macOS**: `~/Library/Application Support/hns/recordings/`
- **Windows**: `~/AppData/Roaming/hns/Recordings/`

Change the save directory anytime with:
```bash
hns config --save-dir ~/path/to/your/recordings
```

## Demo

Watch with sound on!

https://github.com/user-attachments/assets/2aa3752e-bd16-4536-81bd-0679c3be3616
