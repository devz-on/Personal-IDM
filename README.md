# Personal IDM (Internet Download Manager)

A powerful, high-speed download manager built with Python, available as both a command-line tool and a modern GUI application. It features multi-segmented downloading to maximize throughput.

## Features

- 🚀 **High Speed**: Splits files into multiple segments to download in parallel, maximizing bandwidth usage.
- 🖥️ **Graphic User Interface**: Clean, modern GUI built with PySide6 (Qt).
- 💻 **CLI Support**: Simple command-line interface for scripting and quick downloads.
- 🛑 **Speed Limiter**: Built-in bandwidth throttling support.
- 📋 **Queue Management**: Add multiple downloads to the list (GUI).
- 🔒 **SSL/TLS**: Secure download support.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/devz-on/Personal-IDM.git
   cd Personal-IDM
   ```

2. Install dependencies:
   ```bash
   pip install aiohttp PySide6
   ```

## Usage

### GUI Mode
Launch the graphical interface:
```bash
python -m ui.main_window
```
*(Or run `python main.py` without arguments if configured, but currently `main.py` is CLI focused).*

> **Note**: To launch the GUI directly, run the `ui/main_window.py` script:
> ```bash
> python -m ui.main_window
> ```

### CLI Mode
Download a file directly from the terminal:
```bash
python main.py <URL> <OUTPUT_FILE>
```

**Example**:
```bash
python main.py https://example.com/largefile.zip D:/Downloads/file.zip
```

## Project Structure

- `core/`: Core logic (Downloader, SpeedLimiter, etc.)
- `ui/`: User Interface code (PySide6)
- `main.py`: Command-line entry point
- `storage/`: Data persistence (planned)

## Requirements

- Python 3.8+
- `aiohttp`
- `PySide6`

## License

MIT License
