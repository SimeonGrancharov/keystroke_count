RESET = "\033[0m"
VALUE_COLOR = "\033[1m\033[38;5;255m"
LABEL_COLOR = "\033[38;5;75m"
DIM = "\033[38;5;240m"


def format_duration(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _humanize(count: float) -> str:
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return f"{int(count):,}"


def render(mouse_data: dict, num_days: int, daily: list[tuple[str, dict]] | None = None) -> None:
    period = f"{num_days} day{'s' if num_days != 1 else ''}"
    print(f"\n  Mouse Activity  --  {period}\n")

    rows = [
        ("Active time", format_duration(mouse_data.get("active_seconds", 0.0))),
        ("Moves", f"{mouse_data.get('moves', 0):,}"),
        ("Clicks", f"{mouse_data.get('clicks', 0):,}"),
        ("Scrolls", f"{mouse_data.get('scrolls', 0):,}"),
        ("Distance", f"{_humanize(mouse_data.get('distance', 0.0))} px"),
    ]

    label_width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"  {LABEL_COLOR}{label:<{label_width}}{RESET}   {VALUE_COLOR}{value}{RESET}")

    if daily:
        print()
        print(f"  {LABEL_COLOR}Daily active time{RESET}")
        print()

        from datetime import date

        max_seconds = max((d.get("active_seconds", 0.0) for _, d in daily), default=0.0)
        bar_width = 20
        today_key = date.today().isoformat()
        for day_key, day_mouse in daily:
            seconds = day_mouse.get("active_seconds", 0.0)
            bar_length = round(seconds / max_seconds * bar_width) if max_seconds else 0
            bar = "#" * bar_length
            label = date.fromisoformat(day_key).strftime("%a %m-%d")
            marker = f" {DIM}<{RESET}" if day_key == today_key else ""
            value = format_duration(seconds)
            print(f"  {LABEL_COLOR}{label}{RESET}  {bar:<{bar_width}} {VALUE_COLOR}{value:>8}{RESET}{marker}")

    print()
