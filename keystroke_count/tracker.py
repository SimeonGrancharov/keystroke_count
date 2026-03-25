import json
import os
import signal
import sys
from datetime import date
from pathlib import Path

from pynput import keyboard

DATA_DIR = Path.home() / ".keystroke_count"
DATA_FILE = DATA_DIR / "data.json"
PID_FILE = DATA_DIR / "daemon.pid"


def get_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}


def save_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def key_to_label(key) -> str:
    try:
        return key.char if key.char else "unknown"
    except AttributeError:
        return str(key).replace("Key.", "")


class KeystrokeTracker:
    def __init__(self) -> None:
        self.data = get_data()
        self.flush_counter = 0
        self.flush_every = 50

    def on_press(self, key) -> None:
        today = date.today().isoformat()
        label = key_to_label(key)

        if today not in self.data:
            self.data[today] = {"total": 0, "keys": {}}

        self.data[today]["total"] += 1
        self.data[today]["keys"][label] = self.data[today]["keys"].get(label, 0) + 1

        self.flush_counter += 1
        if self.flush_counter >= self.flush_every:
            save_data(self.data)
            self.flush_counter = 0

    def start(self, quiet: bool = False) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        if PID_FILE.exists():
            old_pid = int(PID_FILE.read_text().strip())
            try:
                os.kill(old_pid, 0)
                if not quiet:
                    print(f"Tracker is already running (pid {old_pid}).")
                sys.exit(0)
            except OSError:
                PID_FILE.unlink()

        PID_FILE.write_text(str(os.getpid()))

        def cleanup(*_args) -> None:
            save_data(self.data)
            PID_FILE.unlink(missing_ok=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        if not quiet:
            print(f"Tracking keystrokes (pid {os.getpid()}). Press Ctrl+C to stop.")
            print("Note: macOS requires Accessibility permissions for this app.")

        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

    @staticmethod
    def stop() -> None:
        if not PID_FILE.exists():
            print("No tracker is running.")
            return

        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped tracker (pid {pid}).")
        except OSError:
            print(f"Process {pid} not found. Cleaning up stale pid file.")
            PID_FILE.unlink(missing_ok=True)

    @staticmethod
    def is_running() -> bool:
        if not PID_FILE.exists():
            return False
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            PID_FILE.unlink(missing_ok=True)
            return False
