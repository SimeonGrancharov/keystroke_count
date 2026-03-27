import json
import os
import signal
import sys
import time
from datetime import date
from pathlib import Path

from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListExcludeDesktopElements, kCGWindowListOptionOnScreenOnly
from pynput import keyboard

_cached_app: str = "Unknown"
_cached_at: float = 0.0
_CACHE_TTL: float = 2.0


def _active_app() -> str:
    global _cached_app, _cached_at
    now = time.monotonic()
    if now - _cached_at < _CACHE_TTL:
        return _cached_app
    try:
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID,
        )
        for window in windows:
            if window.get("kCGWindowLayer", -1) == 0:
                _cached_app = window.get("kCGWindowOwnerName", "Unknown")
                _cached_at = now
                return _cached_app
    except Exception:
        pass
    _cached_app = "Unknown"
    _cached_at = now
    return _cached_app


DATA_DIR = Path.home() / ".keystroke_count"
DATA_FILE = DATA_DIR / "data.json"
ARCHIVE_FILE = DATA_DIR / "archive.json"
PID_FILE = DATA_DIR / "daemon.pid"


def _same_week(d1: date, d2: date) -> bool:
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]


def get_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}


def save_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_archive() -> dict:
    if ARCHIVE_FILE.exists():
        with open(ARCHIVE_FILE) as f:
            return json.load(f)
    return {}


def save_archive(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def rotate_weekly() -> None:
    """Move previous-week entries from data.json into archive.json."""
    if not DATA_FILE.exists():
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    if not data:
        return

    today = date.today()
    current_week = {}
    old_entries = {}

    for day_key, day_data in data.items():
        if _same_week(date.fromisoformat(day_key), today):
            current_week[day_key] = day_data
        else:
            old_entries[day_key] = day_data

    if not old_entries:
        return

    archive = get_archive()
    archive.update(old_entries)
    save_archive(archive)
    save_data(current_week)


def get_all_data() -> dict:
    """Get merged current + archive data."""
    rotate_weekly()
    return {**get_archive(), **get_data()}


def key_to_label(key) -> str:
    try:
        return key.char if key.char else "unknown"
    except AttributeError:
        return str(key).replace("Key.", "")


class KeystrokeTracker:
    def __init__(self, debug: bool = False) -> None:
        self.data = get_data()
        self.debug = debug
        self.flush_counter = 0
        self.flush_every = 50

    def _maybe_rotate(self) -> None:
        """Archive old week data from in-memory state."""
        today = date.today()
        old_keys = [
            day_key for day_key in self.data
            if not _same_week(date.fromisoformat(day_key), today)
        ]
        if not old_keys:
            return

        archive = get_archive()
        for key in old_keys:
            archive[key] = self.data.pop(key)
        save_archive(archive)

    def on_press(self, key) -> None:
        today = date.today().isoformat()
        label = key_to_label(key)

        if today not in self.data:
            self._maybe_rotate()
            self.data[today] = {"total": 0, "keys": {}, "apps": {}}

        day = self.data[today]
        if "apps" not in day:
            day["apps"] = {}

        app = _active_app()
        if self.debug:
            print(f"[DEBUG] Key: {label} | App: {app}", flush=True)
        day["total"] += 1
        day["keys"][label] = day["keys"].get(label, 0) + 1
        day["apps"][app] = day["apps"].get(app, 0) + 1

        self.flush_counter += 1
        if self.flush_counter >= self.flush_every:
            save_data(self.data)
            self.flush_counter = 0

    def start(self, quiet: bool = False, foreground: bool = False, debug: bool = False) -> None:
        if debug:
            self.debug = True
            foreground = True
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

        if not foreground:
            import subprocess
            proc = subprocess.Popen(
                [sys.executable, "-m", "keystroke_count.cli", "start", "-f", "-q"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
            print(f"Tracker started (pid {proc.pid}).")
            return

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
