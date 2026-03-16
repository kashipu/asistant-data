"""
Shared Markdown formatting utilities for report generation.
Used by report_builder.py, generate_report.py, generate_deep_report.py,
and the /api/reports/export/markdown endpoint.
"""


def N(n, decimals: int = 0) -> str:
    """Number with thousand separators."""
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.{decimals}f}"
    return f"{int(n):,}"


def pct(value, total) -> str:
    """Percentage string from value/total."""
    if not total:
        return "0.0%"
    return f"{value / total * 100:.1f}%"


def md_table(rows: list, headers: list) -> str:
    """Build a Markdown table from rows (list of lists) and headers."""
    if not rows:
        return "_Sin datos disponibles._\n"
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    header = "| " + " | ".join(str(h) for h in headers) + " |"
    lines = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


def trunc(text: str, max_len: int = 100) -> str:
    """Truncate text to max_len, replacing newlines with spaces."""
    text = str(text).replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text


def dict_to_table(d: dict, key_header: str, val_header: str, top_n: int = None) -> str:
    """Convert {name: count} dict to a Markdown table with a % column."""
    if not d:
        return "_Sin datos._\n"
    items = sorted(d.items(), key=lambda x: x[1], reverse=True)
    if top_n:
        items = items[:top_n]
    total = sum(d.values())
    rows = [[k, N(v), f"{v / total * 100:.1f}%"] for k, v in items]
    return md_table(rows, [key_header, val_header, "%"])


def hourly_to_shifts(hourly: dict) -> dict:
    """Aggregate hourly message counts into 4 time shifts."""
    shifts = {
        "Madrugada (00–05)": 0,
        "Mañana (06–11)": 0,
        "Tarde (12–17)": 0,
        "Noche (18–23)": 0,
    }
    for h, cnt in hourly.items():
        h = int(h)
        if h < 6:
            shifts["Madrugada (00–05)"] += cnt
        elif h < 12:
            shifts["Mañana (06–11)"] += cnt
        elif h < 18:
            shifts["Tarde (12–17)"] += cnt
        else:
            shifts["Noche (18–23)"] += cnt
    return shifts


def split_criteria_counts(failures_df) -> dict:
    """
    Count failure criteria properly by splitting comma-separated values.
    Returns {criteria_name: count}.
    """
    from collections import Counter
    counts = Counter()
    for criteria_str in failures_df['criteria'].dropna():
        for crit in str(criteria_str).split(','):
            c = crit.strip()
            if c:
                counts[c] += 1
    return dict(counts)
