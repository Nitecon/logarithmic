# Logarithmic

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.10.0-green)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

A cross-platform desktop log file watcher with multi-window GUI. Built with Python and PySide6 (Qt).

## Quick Links

- **[PRD / Task Specification](Docs/task.md)** - Complete product requirements
- **[Coding Guidelines](Docs/CodingGuidelines.md)** - Python development standards

## What Does This Do?

Logarithmic is a desktop application that watches log files in real-time and displays their content in separate windows. It handles:

- **Real-time log tailing** - See new log lines as they're written
- **Multi-window design** - Each log file opens in its own window
- **File state management** - Handles file creation, deletion, and rotation
- **Pause/Resume** - Pause log updates while keeping the tail active
- **Session management** - Track multiple log files simultaneously

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd logarithmic
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install development dependencies** (optional)
   ```bash
   pip install -e ".[dev]"
   ```

## Running the Application

```bash
python -m logarithmic
```

Or from the source directory:

```bash
python src/logarithmic/__main__.py
```

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=src/logarithmic --cov-report=term-missing
```

## Usage

1. **Add a log file**: Enter the path to a log file in the input box and click "Add Log" or press Enter
2. **Open a viewer**: Double-click a log file in the list to open its viewer window
3. **Pause/Resume**: Click the "Pause" button in a viewer window to pause updates
4. **Clear**: Click the "Clear" button to clear the viewer content
5. **Reset Windows**: Click "Reset Windows" to cascade all viewer windows
6. **Reset Session**: Click "Reset Session" to close all viewers and clear the tracked logs list

## Architecture

The application follows a clean architecture with separation of concerns:

- **`main_window.py`**: Main control window (add logs, manage session)
- **`log_viewer_window.py`**: Individual log viewer windows
- **`file_watcher.py`**: File watching and tailing logic using watchdog
- **`exceptions.py`**: Custom exception types

### File State Management

The file watcher implements a three-state system:

1. **Non-Existent**: Watch parent directory for file creation
2. **Exists**: Tail the file and watch for deletion/move
3. **Deleted/Moved**: Close handles and return to state 1

This ensures robust handling of log rotation and file system changes.

## Project Structure

```
logarithmic/
├── Docs/
│   ├── CodingGuidelines.md
│   └── task.md
├── src/
│   └── logarithmic/
│       ├── __init__.py
│       ├── __main__.py
│       ├── exceptions.py
│       ├── file_watcher.py
│       ├── log_viewer_window.py
│       └── main_window.py
├── tests/
│   └── (test files)
├── .gitignore
├── pyproject.toml
├── requirements.in
├── requirements.txt
└── README.md
```

## Contributing

All contributions must follow the standards defined in [Docs/CodingGuidelines.md](Docs/CodingGuidelines.md).

Key requirements:
- Use `ruff` for linting and formatting
- Use `mypy` for type checking
- Include type hints for all functions
- Write tests for new functionality
- Follow Google-style docstrings

## Fonts

Logarithmic uses three custom fonts to provide a modern, readable interface:

### Michroma
- **Usage**: Window titles and headers
- **License**: SIL Open Font License 1.1
- **Copyright**: Copyright 2011 The Michroma Project Authors
- **Source**: https://github.com/googlefonts/Michroma-font
- **License File**: `fonts/Michroma/OFL.txt`

### Oxanium
- **Usage**: UI elements (buttons, labels, status bar)
- **License**: SIL Open Font License 1.1
- **Copyright**: Copyright 2016 The Oxanium Project Authors
- **Source**: https://github.com/sevmeyer/oxanium
- **License File**: `fonts/Oxanium/OFL.txt`

### Red Hat Mono
- **Usage**: Log content display (monospace)
- **License**: SIL Open Font License 1.1
- **Copyright**: Copyright 2021 The Red Hat Project Authors
- **Source**: https://github.com/RedHatOfficial/RedHatFont
- **License File**: `fonts/Red_Hat_Mono/OFL.txt`

All fonts are licensed under the SIL Open Font License 1.1, which permits:
- Free use in commercial and non-commercial applications
- Redistribution and modification
- Bundling with software

Full license text is available in each font's directory under `fonts/`.

## License

Apache 2.0 - See LICENSE file for details
