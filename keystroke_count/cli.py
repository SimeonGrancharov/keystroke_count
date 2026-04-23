import argparse
import sys
from datetime import date, timedelta

from keystroke_count.tracker import KeystrokeTracker, get_all_data, get_data


def cmd_start(args) -> None:
    tracker = KeystrokeTracker()
    tracker.start(quiet=args.quiet, foreground=args.foreground, debug=args.debug)


def cmd_stop(_args) -> None:
    KeystrokeTracker.stop()


def cmd_status(_args) -> None:
    running = KeystrokeTracker.is_running()
    print(f"Tracker is {'running' if running else 'not running'}.")


def cmd_today(_args) -> None:
    data = get_data()
    today = date.today().isoformat()
    day_data = data.get(today)
    if not day_data:
        print("No keystrokes recorded today.")
        return
    print(f"Today ({today}): {day_data['total']:,} keystrokes")


def cmd_stats(args) -> None:
    data = get_all_data()
    if not data:
        print("No data recorded yet.")
        return

    days = args.days
    if days:
        cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
        filtered = {d: v for d, v in data.items() if d >= cutoff}
    else:
        filtered = data

    if not filtered:
        print(f"No data in the last {days} days.")
        return

    total_all = sum(v["total"] for v in filtered.values())
    print(f"{'Date':<14} {'Keystrokes':>12}")
    print("-" * 28)

    for day_key in sorted(filtered.keys()):
        print(f"{day_key:<14} {filtered[day_key]['total']:>12,}")

    print("-" * 28)
    print(f"{'Total':<14} {total_all:>12,}")
    print(f"{'Daily avg':<14} {total_all // len(filtered):>12,}")

    if args.keys:
        merged_keys: dict[str, int] = {}
        for day_data in filtered.values():
            for key, count in day_data.get("keys", {}).items():
                merged_keys[key] = merged_keys.get(key, 0) + count

        top_keys = sorted(merged_keys.items(), key=lambda x: x[1], reverse=True)[:20]
        print(f"\n{'Key':<20} {'Count':>10}")
        print("-" * 32)
        for key, count in top_keys:
            print(f"{key:<20} {count:>10,}")

    if args.apps:
        merged_apps: dict[str, int] = {}
        for day_data in filtered.values():
            for app, count in day_data.get("apps", {}).items():
                merged_apps[app] = merged_apps.get(app, 0) + count

        top_apps = sorted(merged_apps.items(), key=lambda x: x[1], reverse=True)[:20]
        print(f"\n{'App':<24} {'Count':>10}")
        print("-" * 36)
        for app, count in top_apps:
            print(f"{app:<24} {count:>10,}")


def cmd_show(_args) -> None:
    data = get_all_data()
    today_key = date.today().isoformat()
    today_data = data.get(today_key)

    running = KeystrokeTracker.is_running()
    print(f"Tracker: {'running' if running else 'not running'}")
    print()

    # Today
    today_total = today_data["total"] if today_data else 0
    print(f"  Today: {today_total:,} keystrokes")

    # Last 7 days
    last_7 = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).isoformat()
        last_7.append(data.get(day, {}).get("total", 0))

    if any(last_7):
        week_total = sum(last_7)
        print(f"  7-day: {week_total:,} keystrokes (avg {week_total // 7:,}/day)")

        # Sparkline bar chart for the week
        max_count = max(last_7) if max(last_7) > 0 else 1
        bar_width = 20
        print()
        day_labels = [(date.today() - timedelta(days=6 - i)).strftime("%a") for i in range(7)]
        for i, (label, count) in enumerate(zip(day_labels, last_7)):
            bar_length = round(count / max_count * bar_width)
            bar = "#" * bar_length
            marker = " <" if i == 6 else ""
            print(f"  {label}  {bar:<{bar_width}} {count:>8,}{marker}")

    # Top 5 keys today
    if today_data and today_data.get("keys"):
        top_keys = sorted(today_data["keys"].items(), key=lambda x: x[1], reverse=True)[:5]
        print()
        print("  Top keys today:")
        for key, count in top_keys:
            pct = count / today_data["total"] * 100
            print(f"    {key:<14} {count:>8,}  ({pct:.1f}%)")

    # Top 5 apps today
    if today_data and today_data.get("apps"):
        top_apps = sorted(today_data["apps"].items(), key=lambda x: x[1], reverse=True)[:5]
        print()
        print("  Top apps today:")
        for app, count in top_apps:
            pct = count / today_data["total"] * 100
            print(f"    {app:<20} {count:>8,}  ({pct:.1f}%)")

    # All-time
    if len(data) > 1:
        all_total = sum(v["total"] for v in data.values())
        print()
        print(f"  All-time: {all_total:,} keystrokes across {len(data)} days")

        top_day_key, top_day_data = max(data.items(), key=lambda item: item[1]["total"])
        print(f"  Top day: {top_day_key} ({top_day_data['total']:,} keystrokes)")


def cmd_heatmap(args) -> None:
    data = get_all_data()
    if not data:
        print("No data recorded yet.")
        return

    days = args.days
    if days:
        cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
        filtered = {d: v for d, v in data.items() if d >= cutoff}
    else:
        filtered = data

    if not filtered:
        print(f"No data in the last {days} days.")
        return

    key_counts: dict[str, int] = {}
    for day_data in filtered.values():
        for key, count in day_data.get("keys", {}).items():
            key_counts[key] = key_counts.get(key, 0) + count

    total = sum(v["total"] for v in filtered.values())

    from keystroke_count.heatmap import render
    render(key_counts, total, len(filtered))


def cmd_apps(args) -> None:
    data = get_all_data()
    if not data:
        print("No data recorded yet.")
        return

    days = args.days
    if days:
        cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
        filtered = {d: v for d, v in data.items() if d >= cutoff}
    else:
        filtered = data

    if not filtered:
        print(f"No data in the last {days} days.")
        return

    app_counts: dict[str, int] = {}
    for day_data in filtered.values():
        for app, count in day_data.get("apps", {}).items():
            app_counts[app] = app_counts.get(app, 0) + count

    if not app_counts:
        print("No app data recorded yet.")
        return

    total = sum(v["total"] for v in filtered.values())

    from keystroke_count.apps import render
    render(app_counts, total, len(filtered))


def cmd_reset(_args) -> None:
    from keystroke_count.tracker import ARCHIVE_FILE, DATA_FILE

    if not DATA_FILE.exists() and not ARCHIVE_FILE.exists():
        print("No data to reset.")
        return

    confirm = input("Are you sure you want to delete all keystroke data? [y/N] ")
    if confirm.lower() == "y":
        DATA_FILE.unlink(missing_ok=True)
        ARCHIVE_FILE.unlink(missing_ok=True)
        print("Data reset.")
    else:
        print("Cancelled.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="keystroke-count",
        description="Track and view your keystroke statistics.",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start tracking keystrokes")
    start_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    start_parser.add_argument("-f", "--foreground", action="store_true", help="Run in foreground instead of daemonizing")
    start_parser.add_argument("-d", "--debug", action="store_true", help="Run in foreground with debug logging")
    subparsers.add_parser("stop", help="Stop the tracker")
    subparsers.add_parser("status", help="Check if the tracker is running")
    subparsers.add_parser("today", help="Show today's keystroke count")

    stats_parser = subparsers.add_parser("stats", help="Show keystroke statistics")
    stats_parser.add_argument("-d", "--days", type=int, default=None, help="Number of days to show (default: all)")
    stats_parser.add_argument("-k", "--keys", action="store_true", help="Show per-key breakdown")
    stats_parser.add_argument("-a", "--apps", action="store_true", help="Show per-app breakdown")

    subparsers.add_parser("show", help="Show a dashboard of keystroke data")

    heatmap_parser = subparsers.add_parser("heatmap", help="Show keyboard heatmap")
    heatmap_parser.add_argument("-d", "--days", type=int, default=None, help="Number of days to show (default: all)")

    apps_parser = subparsers.add_parser("apps", help="Show top 5 apps bar chart")
    apps_parser.add_argument("-d", "--days", type=int, default=None, help="Number of days to show (default: all)")

    subparsers.add_parser("reset", help="Delete all recorded data")

    args = parser.parse_args()

    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "today": cmd_today,
        "stats": cmd_stats,
        "show": cmd_show,
        "heatmap": cmd_heatmap,
        "apps": cmd_apps,
        "reset": cmd_reset,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
