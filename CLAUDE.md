# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hns** is a speech-to-text CLI tool that transcribes voice from microphone to clipboard. It's 100% local using faster-whisper and built with Python. The tool is designed for integration with coding agents and other CLI tools.

## Development Environment

- **Language**: Python 3.10+
- **Package Manager**: `uv` (ultra fast Python package installer)
- **Linter/Formatter**: ruff (with specific rules for code style)
- **Build System**: hatchling

## Building and Running

### Installation for Development
```bash
uv sync --dev  # Install all dependencies including dev tools
```

### Running the CLI
```bash
make run  # Run with small Whisper model (default for dev)
# or
uv run --no-sync --project . python -m hns.cli
```

### Common Commands
```bash
make list-models           # Show available Whisper models
make test-help            # Check CLI help output
make format-and-lint      # Format code and fix linting issues (required before commit)
make bump-patch           # Bump patch version and update lock file
make bump-minor           # Bump minor version and update lock file
make publish-test         # Publish to TestPyPI (requires PYPI_TEST_TOKEN env var)
make publish              # Publish to PyPI (requires PYPI_TOKEN env var)
```

## Code Architecture

### Core Classes

**AudioRecorder** (`hns/cli.py:32-137`)
- Handles microphone input and WAV file recording
- Uses `sounddevice` for audio capture with threading-based UI updates
- Implements live timer display during recording
- Caches last recording to platform-specific cache directory (Windows/macOS/Linux)
- Methods: `record()`, `_validate_audio_device()`, `_prepare_wave_file()`, `_close_wave_file()`

**WhisperTranscriber** (`hns/cli.py:139-275`)
- Wraps faster-whisper for speech-to-text
- Lazy imports `faster_whisper` on first use (for faster startup)
- Supports 19 different Whisper models (from tiny.en to turbo)
- Configurable via environment variables: `HNS_WHISPER_MODEL` and `HNS_LANG`
- Threading-based progress display during transcription
- Uses VAD (Voice Activity Detection) to filter silence
- Methods: `transcribe()`, `_load_model()`, `_get_model_name()`, `list_models()`

**CLI Entry Point** (`hns/cli.py:282-326`)
- Click-based command-line interface
- Options: `--sample-rate`, `--channels`, `--list-models`, `--language`, `--last`
- Orchestrates AudioRecorder → WhisperTranscriber → Clipboard copy workflow
- Uses Rich Console for colored output on stderr (progress), stdout (transcription)

### Output Design
- **stdout**: Final transcribed text only (supports piping/composability)
- **stderr**: All progress messages and status updates (via Rich Console)
- **Clipboard**: Transcription automatically copied (with non-blocking error handling)

## Key Dependencies

- **click**: CLI framework with options parsing
- **faster-whisper**: Speech-to-text model inference (CPU only, int8 quantization)
- **numpy**: Audio data manipulation
- **pyperclip**: Cross-platform clipboard access
- **sounddevice**: Audio input handling
- **rich**: Terminal output formatting and colors
- **requests**: HTTP utilities (for future use)

## Linting and Formatting

Code uses **ruff** with the following rules:
- Line length: 120 characters
- Python target version: 3.10
- Selected rules: E4, E7, E9, F, I (imports), W, TID, PTH (pathlib), Q (quotes)

Always run before committing:
```bash
make format-and-lint
```

This is enforced by CI on all PRs (`.github/workflows/lint.yml`).

## CI/CD Pipeline

**Linting Workflow** (`.github/workflows/lint.yml`)
- Runs on all PRs (opened, synchronize, reopened events)
- Checks Python 3.10 compatibility
- Enforces clean `make format-and-lint` output
- Blocks merging if formatting issues exist

## Important Implementation Patterns

1. **Threading for UI Updates**: Both AudioRecorder and WhisperTranscriber use daemon threads with threading.Event for clean cancellation
2. **Environment Variables**: Model selection and language preference are environment-driven, not just CLI options
3. **Error Handling**: Graceful fallbacks (e.g., clipboard copy failure doesn't block transcription output)
4. **Progress Display**: Uses carriage returns (`\r`) for in-place updating of status lines
5. **Audio Caching**: Last recording is cached for use with `--last` flag, supports offline transcription

## Configuration

Environment variables for customization:
- `HNS_WHISPER_MODEL`: Set Whisper model (default: "base")
- `HNS_LANG`: Force language detection (e.g., "en", "es", "fr")

## Testing Notes

The project doesn't have automated tests yet. Manual testing focuses on:
- Audio device detection on different platforms
- Whisper model download and caching
- Clipboard functionality on Windows/macOS/Linux
- Progress display output during recording and transcription
