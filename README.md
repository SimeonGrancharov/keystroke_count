# keystroke-count

A CLI keystroke counter for macOS.

## Installation

Requires Python 3.10+.

```bash
pip install .
```

**Note:** macOS requires Accessibility permissions for the terminal app you run this from (System Settings > Privacy & Security > Accessibility).

## Usage

```bash
# Start tracking
keystroke-count start

# Start in quiet mode (for background/autostart use)
keystroke-count start -q

# Stop tracking
keystroke-count stop

# Check if tracker is running
keystroke-count status

# Show today's count
keystroke-count today

# Show a dashboard with weekly chart and top keys
keystroke-count show

# Show statistics (all time)
keystroke-count stats

# Show last 7 days with per-key breakdown
keystroke-count stats -d 7 -k

# Delete all recorded data
keystroke-count reset
```

Data is stored in `~/.keystroke_count/data.json`.
