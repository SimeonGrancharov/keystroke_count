from keystroke_count.mouse import DIM, LABEL_COLOR, RESET, VALUE_COLOR, format_duration


def render(keyboard_data: dict, num_days: int, daily: list[tuple[str, dict]] | None = None) -> None:
    period = f"{num_days} day{'s' if num_days != 1 else ''}"
    print(f"\n  Keyboard Activity  --  {period}\n")

    active_seconds = keyboard_data.get("active_seconds", 0.0)
    total_keystrokes = keyboard_data.get("total", 0)
    rows = [
        ("Active time", format_duration(active_seconds)),
        ("Keystrokes", f"{total_keystrokes:,}"),
    ]
    if active_seconds > 0 and total_keystrokes:
        rows.append(("Pace", f"{total_keystrokes / (active_seconds / 60):.0f} keys/min active"))

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
        for day_key, day_keyboard in daily:
            seconds = day_keyboard.get("active_seconds", 0.0)
            bar_length = round(seconds / max_seconds * bar_width) if max_seconds else 0
            bar = "#" * bar_length
            label = date.fromisoformat(day_key).strftime("%a %m-%d")
            marker = f" {DIM}<{RESET}" if day_key == today_key else ""
            value = format_duration(seconds)
            print(f"  {LABEL_COLOR}{label}{RESET}  {bar:<{bar_width}} {VALUE_COLOR}{value:>8}{RESET}{marker}")

    print()
