RESET = "\033[0m"
BAR_COLOR = "\033[38;5;75m"
LABEL_COLOR = "\033[1m\033[38;5;255m"
DIM = "\033[38;5;240m"


def render(app_counts: dict[str, int], total: int, num_days: int) -> None:
    top = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    if not top:
        print("No app data to display.")
        return

    max_val = top[0][1]
    max_label = max(len(name) for name, _ in top)
    bar_width = 40

    period = f"{num_days} day{'s' if num_days != 1 else ''}"
    print(f"\n  Top Apps  --  {period}, {total:,} keystrokes\n")

    for name, count in top:
        pct = count / total * 100
        filled = int(round(count / max_val * bar_width))
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"  {LABEL_COLOR}{name:<{max_label}}{RESET}  {BAR_COLOR}{bar}{RESET}  {count:>10,}  {DIM}({pct:.1f}%){RESET}")

    print()
