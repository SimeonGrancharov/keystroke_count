# keystroke-count

A CLI keystroke counter for macOS. Tracks keystrokes globally across all apps, with per-app and per-key breakdowns.

## Installation

Requires Python 3.10+.

```bash
pip install .
```

## Permissions

The tracker needs two macOS permissions to capture keystrokes and detect the active app. Grant both to your terminal app (e.g. Ghostty, iTerm2, Terminal) **and** the Python binary:

1. **Input Monitoring** — System Settings > Privacy & Security > Input Monitoring
2. **Accessibility** — System Settings > Privacy & Security > Accessibility

To find your Python binary path:

```bash
which python3
```

Use `Cmd+Shift+G` in the file picker to paste the path when adding it.

## Usage

```bash
# Start tracking (background daemon)
keystroke-count start

# Start in foreground
keystroke-count start -f

# Start in foreground with debug logging
keystroke-count start -d

# Stop tracking
keystroke-count stop

# Check if tracker is running
keystroke-count status

# Show today's count
keystroke-count today

# Show a dashboard with weekly chart, top keys, and top apps
keystroke-count show

# Show statistics (all time)
keystroke-count stats

# Show last 7 days with per-key breakdown
keystroke-count stats -d 7 -k

# Show last 7 days with per-app breakdown
keystroke-count stats -d 7 -a

# Show keyboard heatmap (all time)
keystroke-count heatmap

# Show keyboard heatmap for last 7 days
keystroke-count heatmap -d 7

# Show top 5 apps bar chart (all time)
keystroke-count apps

# Show top 5 apps bar chart for last 7 days
keystroke-count apps -d 7

# Delete all recorded data
keystroke-count reset
```

## Data storage

Data is stored in `~/.keystroke_count/data.json` (current week) and `~/.keystroke_count/archive.json` (past weeks). Old week data is automatically rotated to the archive.
