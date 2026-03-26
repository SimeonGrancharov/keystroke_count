
RESET = "\033[0m"

# Heat gradient: cold (dark/blue) → hot (red)
# Each entry: (background_ansi, foreground_ansi)
HEAT = [
    ("\033[48;5;233m", "\033[38;5;242m"),              # 0: near-black, dim
    ("\033[48;5;235m", "\033[38;5;250m"),              # 1: dark gray
    ("\033[48;5;17m",  "\033[38;5;75m"),               # 2: dark blue
    ("\033[48;5;24m",  "\033[38;5;153m"),              # 3: blue
    ("\033[48;5;29m",  "\033[38;5;158m"),              # 4: teal
    ("\033[48;5;142m", "\033[38;5;232m"),              # 5: olive/yellow
    ("\033[48;5;166m", "\033[38;5;232m"),              # 6: orange
    ("\033[48;5;124m", "\033[1m\033[38;5;255m"),       # 7: red, bold white
]

# Keyboard layout: (row_indent, [(label, [data_keys], inner_width), ...])
ROWS = [
    (0, [
        ("`",     ["`", "~"], 4),
        ("1",     ["1", "!"], 4),
        ("2",     ["2", "@"], 4),
        ("3",     ["3", "#"], 4),
        ("4",     ["4", "$"], 4),
        ("5",     ["5", "%"], 4),
        ("6",     ["6", "^"], 4),
        ("7",     ["7", "&"], 4),
        ("8",     ["8", "*"], 4),
        ("9",     ["9", "("], 4),
        ("0",     ["0", ")"], 4),
        ("-",     ["-", "_"], 4),
        ("=",     ["=", "+"], 4),
        ("BKSP",  ["backspace"], 7),
    ]),
    (1, [
        ("TAB",   ["tab"], 6),
        ("Q",     ["q", "Q"], 4),
        ("W",     ["w", "W"], 4),
        ("E",     ["e", "E"], 4),
        ("R",     ["r", "R"], 4),
        ("T",     ["t", "T"], 4),
        ("Y",     ["y", "Y"], 4),
        ("U",     ["u", "U"], 4),
        ("I",     ["i", "I"], 4),
        ("O",     ["o", "O"], 4),
        ("P",     ["p", "P"], 4),
        ("[",     ["[", "{"], 4),
        ("]",     ["]", "}"], 4),
        ("\\",    ["\\", "|"], 4),
    ]),
    (2, [
        ("CAPS",  ["caps_lock"], 7),
        ("A",     ["a", "A"], 4),
        ("S",     ["s", "S"], 4),
        ("D",     ["d", "D"], 4),
        ("F",     ["f", "F"], 4),
        ("G",     ["g", "G"], 4),
        ("H",     ["h", "H"], 4),
        ("J",     ["j", "J"], 4),
        ("K",     ["k", "K"], 4),
        ("L",     ["l", "L"], 4),
        (";",     [";", ":"], 4),
        ("'",     ["'", "\""], 4),
        ("RET",   ["enter"], 7),
    ]),
    (3, [
        ("SHIFT", ["shift"], 9),
        ("Z",     ["z", "Z"], 4),
        ("X",     ["x", "X"], 4),
        ("C",     ["c", "C"], 4),
        ("V",     ["v", "V"], 4),
        ("B",     ["b", "B"], 4),
        ("N",     ["n", "N"], 4),
        ("M",     ["m", "M"], 4),
        (",",     [",", "<"], 4),
        (".",     [".", ">"], 4),
        ("/",     ["/", "?"], 4),
        ("SHIFT", ["shift"], 9),
    ]),
    (0, [
        ("ctrl",  ["ctrl"], 6),
        ("alt",   ["alt"], 5),
        ("cmd",   ["cmd"], 6),
        ("SPACE", ["space"], 25),
        ("cmd",   ["cmd", "cmd_r"], 6),
        ("alt",   ["alt"], 5),
        ("ctrl",  ["ctrl"], 6),
    ]),
]

EXTRAS = [
    ("ESC", ["esc"]),
    ("DEL", ["delete"]),
    ("UP",  ["up"]),
    ("DN",  ["down"]),
    ("LT",  ["left"]),
    ("RT",  ["right"]),
]


def _thresholds(all_counts):
    """Compute percentile-based thresholds for heat levels 1-7."""
    non_zero = sorted(c for c in all_counts if c > 0)
    if not non_zero:
        return [0] * 7
    n = len(non_zero)
    breakpoints = [0.10, 0.25, 0.40, 0.55, 0.70, 0.85, 0.95]
    return [non_zero[min(int(p * n), n - 1)] for p in breakpoints]


def _level(count, thresholds):
    if count == 0:
        return 0
    for i, threshold in enumerate(thresholds):
        if count <= threshold:
            return i + 1
    return 7


def _cell(text, width, heat):
    bg, fg = HEAT[heat]
    return f"{bg}{fg}{text.center(width)}{RESET}"


def _fmt(count, width):
    if count == 0:
        return " " * width
    s = str(count)
    if len(s) <= width:
        return s.center(width)
    s = f"{count // 1000}k"
    if len(s) > width:
        s = f"{count // 1_000_000}m"
    return s.center(width)[:width]


def render(key_counts, total, num_days):
    # Gather all counts for heat scaling
    all_counts = []
    for _, keys in ROWS:
        for _, data_keys, _ in keys:
            all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))
    for _, data_keys in EXTRAS:
        all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))

    thresholds = _thresholds(all_counts)

    period = f"{num_days} day{'s' if num_days != 1 else ''}"
    print(f"\n  Keyboard Heatmap  --  {period}, {total:,} keystrokes\n")

    for indent, keys in ROWS:
        pad = " " * (indent + 2)
        widths = [w for _, _, w in keys]

        counts = []
        heats = []
        for _, data_keys, _ in keys:
            c = sum(key_counts.get(k, 0) for k in data_keys)
            counts.append(c)
            heats.append(_level(c, thresholds))

        # Top border
        print(pad + "\u250c" + "\u252c".join("\u2500" * w for w in widths) + "\u2510")

        # Label line
        label_cells = [_cell(label, w, heats[i]) for i, (label, _, w) in enumerate(keys)]
        print(pad + "\u2502" + "\u2502".join(label_cells) + "\u2502")

        # Count line
        count_cells = [_cell(_fmt(counts[i], w), w, heats[i]) for i, (_, _, w) in enumerate(keys)]
        print(pad + "\u2502" + "\u2502".join(count_cells) + "\u2502")

        # Bottom border
        print(pad + "\u2514" + "\u2534".join("\u2500" * w for w in widths) + "\u2518")

    # Extra keys (ESC, arrows, DEL)
    parts = []
    for label, data_keys in EXTRAS:
        c = sum(key_counts.get(k, 0) for k in data_keys)
        h = _level(c, thresholds)
        bg, fg = HEAT[h]
        parts.append(f"{bg}{fg} {label} {c:,} {RESET}")

    print()
    print("  " + "  ".join(parts))

    # Legend
    print()
    legend = "  "
    for i in range(8):
        bg, _ = HEAT[i]
        legend += f"{bg}      {RESET}"
    print(legend)
    print(f"  {'cold':<24}{'hot':>24}")
    print()
