# Universal AI

A tiny always-on-top overlay that gives you instant, straight-to-the-point answers without leaving what you're doing. Watching a movie and don't know a word? Reading an article and want a quick definition? Hit a shortcut, ask, read the answer, and get back to it. No tab switching, no Googling.

> **You:** What is Manchester?
> **Universal AI:** Manchester is a city in northwest England known for football, its industrial history, and its music scene.

## Features

- **Instant overlay**: a small frameless card that floats on top of any window
- **Short answers**: replies are limited to 1-2 sentences, with the direct answer first
- **Streaming**: text appears as it's generated, so you don't wait for the full reply
- **Non-blocking UI**: requests run in a background thread, so the overlay never freezes
- **Keyboard first**: `Enter` to ask, `Esc` to hide, a system shortcut to toggle
- **Runs in the background**: the app stays alive when the overlay is hidden

## Project structure

```
universal_ai/
├── ai.py          # Groq client, system prompt, streaming
├── overlay.py     # PySide6 overlay UI and toggle server
├── .env           # your API key (never commit this)
└── README.md
```

## Requirements

- Python 3.10+ (3.12 or 3.13 recommended for PySide6)
- A free [Groq API key](https://console.groq.com/keys)

## Installation

```bash
git clone <your-repo-url> universal_ai
cd universal_ai

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install PySide6 groq python-dotenv
```

Create a `.env` file in the project folder:

```
GROQ_API_KEY=your_key_here
```

Add `.env` and `.venv/` to your `.gitignore` so your key is never committed.

## Running

```bash
python overlay.py
```

Leave it running in a terminal. On Linux under Wayland, start it with XWayland so "always on top" and positioning work:

```bash
QT_QPA_PLATFORM=xcb python overlay.py
```

## Setting up the shortcut

The app listens for a `--toggle` signal. Bind that command to a key in your operating system and the overlay opens from any app.

**Ubuntu / GNOME**

1. Open **Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts → Add**.
2. **Name:** `universal_ai`
3. **Command:** the full path to your venv's Python, then the script, then `--toggle`:

   ```
   /home/<you>/universal_ai/.venv/bin/python /home/<you>/universal_ai/overlay.py --toggle
   ```

4. **Shortcut:** press your key combination, for example `Ctrl+Alt+Space`.

The **Command** field must contain the command above, not the key combination. If `Ctrl+Space` doesn't fire, your input method (IBus) probably owns it, so pick a different combination.

**Other systems**: use any tool that can run a command on a hotkey (Windows: AutoHotkey or a desktop shortcut with a hotkey; macOS: Shortcuts app or Automator) and point it at the same `--toggle` command.

To test the command by itself, run it in a second terminal while the app is running. The overlay should appear and the exit code should be `0`:

```bash
python overlay.py --toggle; echo $?
```

## Usage

| Action | Key |
| --- | --- |
| Show / hide overlay | Your system shortcut |
| Ask a question | `Enter` |
| Hide overlay | `Esc` |

## Configuration

Both settings live in `ai.py`.

**Model.** Groq changes its model catalog often, so a model can disappear. List what your key can use:

```bash
python -c "from ai import client; print(sorted(m.id for m in client.models.list().data))"
```

For a snappy overlay, prefer a non-reasoning model such as `llama-3.3-70b-versatile`. Reasoning models (like `openai/gpt-oss-20b`) think before answering, so they respond more slowly and need a larger `max_tokens`.

**Personality and length.** Edit `SYSTEM_PROMPT` to change how answers look. For example, you can shorten replies further, answer in the user's language, or explain slang and references. One string controls the behavior of every answer.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Shortcut does nothing | Check the shortcut's **Command** field has the full `--toggle` command. Try a different key combo. Make sure `overlay.py` is running. |
| `--toggle` prints exit code `1` | The app isn't running, or isn't listening. Start it first, then run `--toggle` again. |
| Overlay not on top, or wrong position (Linux) | Run with `QT_QPA_PLATFORM=xcb`. |
| Overlay hidden over a video or game | Use borderless or windowed fullscreen. Exclusive fullscreen can cover any overlay. |
| Stuck on "Thinking..." | You're probably using a reasoning model with too small a `max_tokens`. Switch to a non-reasoning model. |
| `404 model_not_found` | That model isn't available to your key. List models (see Configuration) and pick another. |
| `QLayout: Attempting to add QLayout` | `OverlayWindow` must extend `QWidget`, not `QMainWindow`. |
| `Signal source has been deleted` | Create the signal bridge once in `__init__` and connect it there, instead of creating a new `QThread` per question. |

## Roadmap

- System tray icon with a Quit option
- Ask about highlighted or clipboard text with the hotkey
- Context mode (for example the movie or book title) for better answers to ambiguous words
- Optional conversation memory for follow-up questions
- Packaging as a single installable app

