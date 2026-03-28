
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

# F-key row: groups separated by gaps
F_ROW = [
    [("ESC", ["esc"], 4)],
    [("F1", ["f1"], 4), ("F2", ["f2"], 4), ("F3", ["f3"], 4), ("F4", ["f4"], 4)],
    [("F5", ["f5"], 4), ("F6", ["f6"], 4), ("F7", ["f7"], 4), ("F8", ["f8"], 4)],
    [("F9", ["f9"], 4), ("F10", ["f10"], 4), ("F11", ["f11"], 4), ("F12", ["f12"], 4)],
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
        ("SPACE", ["space"], 15),
        ("cmd",   ["cmd", "cmd_r"], 6),
        ("alt",   ["alt"], 5),
        ("ctrl",  ["ctrl"], 6),
    ]),
]

ARROWS = {
    "up":    ("▲",  ["up"]),
    "down":  ("▼",  ["down"]),
    "left":  ("◀",  ["left"]),
    "right": ("▶",  ["right"]),
}

EXTRAS = [
    ("DEL", ["delete"]),
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


def _render_key_group(keys, key_counts, thresholds):
    """Render a group of keys as a bordered block, return list of lines."""
    widths = [w for _, _, w in keys]
    counts = []
    heats = []
    for _, data_keys, _ in keys:
        c = sum(key_counts.get(k, 0) for k in data_keys)
        counts.append(c)
        heats.append(_level(c, thresholds))

    top = "\u250c" + "\u252c".join("\u2500" * w for w in widths) + "\u2510"
    label_cells = [_cell(label, w, heats[i]) for i, (label, _, w) in enumerate(keys)]
    labels = "\u2502" + "\u2502".join(label_cells) + "\u2502"
    count_cells = [_cell(_fmt(counts[i], w), w, heats[i]) for i, (_, _, w) in enumerate(keys)]
    cnt = "\u2502" + "\u2502".join(count_cells) + "\u2502"
    bot = "\u2514" + "\u2534".join("\u2500" * w for w in widths) + "\u2518"
    return [top, labels, cnt, bot]


def render(key_counts, total, num_days):
    # Gather all counts for heat scaling
    all_counts = []
    for group in F_ROW:
        for _, data_keys, _ in group:
            all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))
    for _, keys in ROWS:
        for _, data_keys, _ in keys:
            all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))
    for _, data_keys in EXTRAS:
        all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))
    for _, data_keys in ARROWS.values():
        all_counts.append(sum(key_counts.get(k, 0) for k in data_keys))

    thresholds = _thresholds(all_counts)

    period = f"{num_days} day{'s' if num_days != 1 else ''}"
    print(f"\n  Keyboard Heatmap  --  {period}, {total:,} keystrokes\n")

    # F-key row (groups separated by gaps)
    group_lines = [_render_key_group(g, key_counts, thresholds) for g in F_ROW]
    gap = "  "
    for line_idx in range(4):
        print("  " + gap.join(gl[line_idx] for gl in group_lines))

    def _row_lines(indent, keys):
        pad = " " * (indent + 2)
        widths = [w for _, _, w in keys]
        counts = []
        heats = []
        for _, data_keys, _ in keys:
            c = sum(key_counts.get(k, 0) for k in data_keys)
            counts.append(c)
            heats.append(_level(c, thresholds))
        label_cells = [_cell(label, w, heats[i]) for i, (label, _, w) in enumerate(keys)]
        count_cells = [_cell(_fmt(counts[i], w), w, heats[i]) for i, (_, _, w) in enumerate(keys)]
        return [
            pad + "\u250c" + "\u252c".join("\u2500" * w for w in widths) + "\u2510",
            pad + "\u2502" + "\u2502".join(label_cells) + "\u2502",
            pad + "\u2502" + "\u2502".join(count_cells) + "\u2502",
            pad + "\u2514" + "\u2534".join("\u2500" * w for w in widths) + "\u2518",
        ]

    for indent, keys in ROWS[:-1]:
        for line in _row_lines(indent, keys):
            print(line)

    # Last row + arrow keys side by side
    last_indent, last_keys = ROWS[-1]
    row_lines = _row_lines(last_indent, last_keys)

    # Extra keys (DEL) inline badge
    extra_parts = []
    for label, data_keys in EXTRAS:
        c = sum(key_counts.get(k, 0) for k in data_keys)
        h = _level(c, thresholds)
        bg, fg = HEAT[h]
        extra_parts.append(f"{bg}{fg} {label} {c:,} {RESET}")
    del_str = "  " + "  ".join(extra_parts)

    w = 4
    arrow_data = {}
    for direction, (label, data_keys) in ARROWS.items():
        c = sum(key_counts.get(k, 0) for k in data_keys)
        h = _level(c, thresholds)
        arrow_data[direction] = (label, c, h)

    lt_label, lt_count, lt_heat = arrow_data["left"]
    rt_label, rt_count, rt_heat = arrow_data["right"]
    up_label, up_count, up_heat = arrow_data["up"]
    dn_label, dn_count, dn_heat = arrow_data["down"]

    b = "\u2502"
    gap = "  "
    arrow_lines = [
        "\u250c" + "\u2500" * w + "\u252c" + "\u2500" * w + "\u252c" + "\u2500" * w + "\u2510",
        b + _cell(lt_label, w, lt_heat) + b + _cell(up_label, w, up_heat) + b + _cell(rt_label, w, rt_heat) + b,
        b + _cell(_fmt(lt_count, w), w, lt_heat) + "\u251c" + "\u2500" * w + "\u2524" + _cell(_fmt(rt_count, w), w, rt_heat) + b,
        b + _cell("", w, lt_heat) + b + _cell(dn_label, w, dn_heat) + b + _cell("", w, rt_heat) + b,
        "\u2514" + "\u2500" * w + "\u2534" + "\u2500" * w + "\u2534" + "\u2500" * w + "\u2518",
    ]

    # Visible width of the last row (strip ANSI for padding)
    import re
    row_visible_width = len(re.sub(r"\033\[[^m]*m", "", row_lines[0]))

    for i in range(max(len(row_lines), len(arrow_lines))):
        left = row_lines[i] if i < len(row_lines) else " " * row_visible_width
        right = arrow_lines[i] if i < len(arrow_lines) else ""
        suffix = del_str if i == 0 else ""
        print(left + gap + right + suffix)

    # Legend
    print()
    legend = "  "
    for i in range(8):
        bg, _ = HEAT[i]
        legend += f"{bg}      {RESET}"
    print(legend)
    print(f"  {'cold':<24}{'hot':>24}")
    print()
