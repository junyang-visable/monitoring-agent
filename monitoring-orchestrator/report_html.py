"""Generate a standalone HTML monitoring report from a completed run's artifacts.

Reads report.json and per-project fe-stability-analysis.json evidence files,
then outputs a self-contained report.html with inline CSS and SVG charts.

Usage:
    python report_html.py <run_dir>
    python monitoring-orchestrator/report_html.py artifacts/monitoring/20260724T063134Z

The output is written to <run_dir>/report.html.
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# SVG chart renderers
# ---------------------------------------------------------------------------

def _svg_line_chart(
    categories: list[str],
    series_list: list[dict[str, Any]],
    *,
    width: int = 760,
    height: int = 220,
    title: str = "",
    caption: str = "",
) -> str:
    """Render a multi-series line chart as inline SVG."""
    pad_l, pad_r, pad_t, pad_b = 56, 20, 30, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = len(categories)
    if n < 2:
        return ""

    all_vals = [v for s in series_list for v in s["data"]]
    y_min = 0
    y_max = max(all_vals) * 1.1 if all_vals else 1

    colors = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24"]

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height + 24}" '
                 f'style="display:block;margin:8px 0">')

    if title:
        lines.append(f'<text x="{width // 2}" y="16" text-anchor="middle" '
                     f'fill="#e2e8f0" font-size="13" font-weight="600">{escape(title)}</text>')

    # Grid lines
    for i in range(5):
        gy = pad_t + plot_h - (i / 4) * plot_h
        val = y_min + (i / 4) * (y_max - y_min)
        lines.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l + plot_w}" y2="{gy:.1f}" '
                     f'stroke="#334155" stroke-width="1"/>')
        lines.append(f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" '
                     f'fill="#94a3b8" font-size="10">{_fmt_k(val)}</text>')

    # X-axis labels (show every Nth)
    step = max(1, n // 12)
    for i in range(0, n, step):
        x = pad_l + (i / (n - 1)) * plot_w
        lines.append(f'<text x="{x:.1f}" y="{pad_t + plot_h + 16}" text-anchor="middle" '
                     f'fill="#94a3b8" font-size="10">{escape(categories[i])}</text>')

    # Series
    for si, series in enumerate(series_list):
        color = colors[si % len(colors)]
        points: list[str] = []
        for i, val in enumerate(series["data"]):
            x = pad_l + (i / (n - 1)) * plot_w
            y = pad_t + plot_h - ((val - y_min) / (y_max - y_min)) * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" '
                     f'stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')

    # Legend
    lx = pad_l
    for si, series in enumerate(series_list):
        color = colors[si % len(colors)]
        lines.append(f'<rect x="{lx}" y="{height + 8}" width="12" height="3" fill="{color}" rx="1"/>')
        lines.append(f'<text x="{lx + 16}" y="{height + 12}" fill="#cbd5e1" font-size="10">'
                     f'{escape(series["name"])}</text>')
        lx += len(series["name"]) * 6 + 32

    if caption:
        lines.append(f'<text x="{width - pad_r}" y="{height + 12}" text-anchor="end" '
                     f'fill="#64748b" font-size="9">{escape(caption)}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def _svg_bar_chart(
    categories: list[str],
    series_list: list[dict[str, Any]],
    *,
    width: int = 760,
    height: int = 200,
    title: str = "",
) -> str:
    """Render a grouped bar chart as inline SVG."""
    pad_l, pad_r, pad_t, pad_b = 56, 20, 30, 50
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = len(categories)
    if n < 1:
        return ""

    ns = len(series_list)
    all_vals = [v for s in series_list for v in s["data"]]
    y_max = max(all_vals) * 1.15 if all_vals else 1

    colors = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24"]
    bar_group_w = plot_w / n * 0.75
    bar_w = bar_group_w / ns
    gap = plot_w / n * 0.25

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height + 20}" '
                 f'style="display:block;margin:8px 0">')

    if title:
        lines.append(f'<text x="{width // 2}" y="16" text-anchor="middle" '
                     f'fill="#e2e8f0" font-size="13" font-weight="600">{escape(title)}</text>')

    # Grid
    for i in range(5):
        gy = pad_t + plot_h - (i / 4) * plot_h
        val = (i / 4) * y_max
        lines.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l + plot_w}" y2="{gy:.1f}" '
                     f'stroke="#334155" stroke-width="1"/>')
        lines.append(f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" '
                     f'fill="#94a3b8" font-size="10">{_fmt_k(val)}</text>')

    # Bars
    for ci in range(n):
        group_x = pad_l + ci * (plot_w / n) + gap / 2
        for si, series in enumerate(series_list):
            val = series["data"][ci] if ci < len(series["data"]) else 0
            bh = (val / y_max) * plot_h if y_max else 0
            bx = group_x + si * bar_w
            by = pad_t + plot_h - bh
            color = colors[si % len(colors)]
            lines.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w * 0.85:.1f}" '
                         f'height="{bh:.1f}" fill="{color}" rx="2"/>')

    # X labels
    for ci in range(n):
        x = pad_l + ci * (plot_w / n) + (plot_w / n) / 2
        lines.append(f'<text x="{x:.1f}" y="{pad_t + plot_h + 14}" text-anchor="middle" '
                     f'fill="#94a3b8" font-size="9" transform="rotate(-25 {x:.1f} {pad_t + plot_h + 14})">'
                     f'{escape(categories[ci])}</text>')

    # Legend
    lx = pad_l
    for si, series in enumerate(series_list):
        color = colors[si % len(colors)]
        ly = height + 8
        lines.append(f'<rect x="{lx}" y="{ly}" width="12" height="3" fill="{color}" rx="1"/>')
        lines.append(f'<text x="{lx + 16}" y="{ly + 4}" fill="#cbd5e1" font-size="10">'
                     f'{escape(series["name"])}</text>')
        lx += len(series["name"]) * 6 + 32

    lines.append("</svg>")
    return "\n".join(lines)


def _fmt_k(val: float) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.0f}k"
    return f"{val:.0f}"


def _fmt_num(val: int | float) -> str:
    return f"{val:,.0f}"


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #0f172a; color: #e2e8f0; padding: 32px; line-height: 1.6;
  max-width: 880px; margin: 0 auto;
}
h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; color: #f1f5f9; }
h2 { font-size: 16px; font-weight: 600; margin: 24px 0 12px; color: #f1f5f9;
     border-bottom: 1px solid #1e293b; padding-bottom: 6px; }
h3 { font-size: 13px; font-weight: 600; margin: 16px 0 8px; color: #cbd5e1; }
.meta { font-size: 12px; color: #64748b; margin-bottom: 20px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
         gap: 12px; margin: 12px 0; }
.stat { background: #1e293b; border-radius: 8px; padding: 12px 16px; }
.stat-value { font-size: 20px; font-weight: 700; color: #f1f5f9; }
.stat-value.good { color: #34d399; }
.stat-value.bad { color: #f87171; }
.stat-label { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.callout { border-left: 3px solid #fbbf24; background: #1e293b; padding: 10px 14px;
           border-radius: 4px; margin: 12px 0; font-size: 13px; }
.callout.danger { border-left-color: #f87171; }
.callout-title { font-weight: 600; margin-bottom: 2px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 8px 0; }
th { text-align: left; padding: 6px 10px; background: #1e293b; color: #94a3b8;
     font-weight: 600; border-bottom: 1px solid #334155; }
td { padding: 6px 10px; border-bottom: 1px solid #1e293b; }
tr:hover td { background: #1e293b; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.new-badge { background: #dc2626; color: #fff; font-size: 10px; padding: 1px 5px;
             border-radius: 3px; font-weight: 600; margin-left: 4px; }
.spike-badge { background: #d97706; color: #fff; font-size: 10px; padding: 1px 5px;
               border-radius: 3px; font-weight: 600; margin-left: 4px; }
.divider { border-top: 1px solid #1e293b; margin: 24px 0; }
.footer { font-size: 11px; color: #475569; margin-top: 24px; }
.section-signal { display: inline-block; background: #1e293b; padding: 2px 8px;
                  border-radius: 4px; font-size: 11px; color: #94a3b8; margin-right: 6px; }
.ok { color: #34d399; }
.alert { color: #f87171; }
"""


def _render_stat(value: str, label: str, tone: str = "") -> str:
    cls = f"stat-value {tone}" if tone else "stat-value"
    return f'<div class="stat"><div class="{cls}">{escape(value)}</div><div class="stat-label">{escape(label)}</div></div>'


def _render_callout(title: str, body: str, danger: bool = False) -> str:
    cls = "callout danger" if danger else "callout"
    return f'<div class="{cls}"><div class="callout-title">{escape(title)}</div>{escape(body)}</div>'


def _render_p0_table(issues: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for issue in issues:
        change = issue.get("change_display", "")
        badges = ""
        if issue.get("is_new"):
            badges += '<span class="new-badge">NEW</span>'
        elif issue.get("is_spike"):
            badges += '<span class="spike-badge">SPIKE</span>'
        rows.append(
            f"<tr><td>{escape(issue['category'])}</td>"
            f"<td>{escape(issue['display'])}{badges}</td>"
            f'<td class="num">{_fmt_num(issue["curr_count"])}</td>'
            f'<td class="num">{escape(change)}</td>'
            f'<td class="num">{_fmt_num(issue.get("impact_score", 0))}</td></tr>'
        )
    return (
        "<table><thead><tr><th>Category</th><th>Error</th>"
        '<th class="num">Count</th><th class="num">Change</th>'
        '<th class="num">Impact</th></tr></thead><tbody>'
        + "\n".join(rows)
        + "</tbody></table>"
    )


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def _extract_p0_issues(stability_data: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for _category, info in stability_data.get("issues", {}).items():
        for detail in info.get("details", []):
            if detail.get("priority") == "P0":
                pct = detail.get("change_pct")
                if detail.get("is_new"):
                    change_display = "NEW"
                elif pct is not None:
                    change_display = f"+{pct}%" if pct > 0 else f"{pct}%"
                else:
                    change_display = "—"
                issues.append({**detail, "change_display": change_display})
    issues.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
    return issues


def _extract_hourly(stability_data: dict[str, Any]) -> tuple[list[str], list[int], list[int]]:
    hourly = stability_data.get("hourly_breakdown", {})
    base_hours = hourly.get("base", [])
    curr_hours = hourly.get("curr", [])
    categories = [f"{h['hh']}:00" for h in curr_hours]
    curr_data = [h["count"] for h in curr_hours]
    base_data = [h["count"] for h in base_hours]
    return categories, curr_data, base_data


def _extract_metrics_chart(stability_data: dict[str, Any]) -> tuple[list[str], list[int], list[int]]:
    metrics = stability_data.get("metrics", [])
    cats: list[str] = []
    curr_vals: list[int] = []
    base_vals: list[int] = []
    for m in metrics:
        short_key = m["key"].split(":")[-1] if ":" in m["key"] else m["key"]
        cats.append(short_key)
        curr_vals.append(m["curr_total"])
        base_vals.append(m["base_total"])
    return cats, curr_vals, base_vals


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate_html_report(run_dir: Path) -> str:
    report_path = run_dir / "report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"report.json not found in {run_dir}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    time_range = report.get("time_range", {})
    run_id = report.get("run_id", run_dir.name)
    observed_at = report.get("observed_at", "")

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en"><head><meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append(f"<title>Monitoring Report — {time_range.get('label', run_id)}</title>")
    parts.append(f"<style>{_CSS}</style></head><body>")

    # Header
    parts.append(f"<h1>Monitoring Report — {escape(time_range.get('label', 'N/A'))}</h1>")
    parts.append(
        f'<div class="meta">Time range: {escape(time_range.get("start", ""))} → '
        f'{escape(time_range.get("end", ""))} | Run: {escape(run_id)} | '
        f'Observed: {escape(observed_at)}</div>'
    )

    # Summary stats
    projects = report.get("projects", [])
    parts.append('<div class="stats">')
    for proj in projects:
        name = proj["project"]
        stability = proj.get("signals", {}).get("stability_sdk", {})
        metrics = stability.get("metrics", {})
        curr = metrics.get("curr_total")
        pct = metrics.get("change_pct")
        if curr is not None:
            tone = "good" if pct is not None and pct <= 0 else "bad" if pct is not None and pct > 10 else ""
            parts.append(_render_stat(_fmt_num(curr), f"{name} errors", tone))
            if pct is not None:
                sign = "+" if pct > 0 else ""
                tone2 = "good" if pct <= 0 else "bad"
                parts.append(_render_stat(f"{sign}{pct}%", f"vs baseline", tone2))
    parts.append("</div>")

    # Per-project sections
    for proj in projects:
        name = proj["project"]
        signals = proj.get("signals", {})
        parts.append(f"<h2>{escape(name)}</h2>")

        # Signal badges
        parts.append("<div>")
        for sig_name in ["datadog", "stability_sdk", "sentry", "tracking_patrol"]:
            sig = signals.get(sig_name, {})
            status = sig.get("status", "disabled")
            cls = "ok" if status == "ok" else "alert" if status in ("degraded", "unavailable") else ""
            parts.append(f'<span class="section-signal">{escape(sig_name)}: '
                         f'<span class="{cls}">{escape(status.upper())}</span></span>')
        parts.append("</div>")

        # Stat grid
        parts.append('<div class="stats">')
        stability = signals.get("stability_sdk", {})
        stab_metrics = stability.get("metrics", {})
        if stab_metrics.get("curr_total") is not None:
            parts.append(_render_stat(_fmt_num(stab_metrics["curr_total"]), "Stability errors"))
        dd = signals.get("datadog", {})
        dd_metrics = dd.get("metrics", {})
        if dd_metrics.get("error_log_count") is not None:
            parts.append(_render_stat(_fmt_num(dd_metrics["error_log_count"]), "Datadog error logs"))
        sentry = signals.get("sentry", {})
        sentry_metrics = sentry.get("metrics", {})
        if sentry_metrics.get("current") is not None:
            delta_pct = sentry_metrics.get("delta_percent")
            label = f"Sentry errors ({delta_pct:+.1f}%)" if delta_pct else "Sentry errors"
            tone = "good" if delta_pct and delta_pct < 0 else "bad" if delta_pct and delta_pct > 10 else ""
            parts.append(_render_stat(_fmt_num(sentry_metrics["current"]), label, tone))
        patrol = signals.get("tracking_patrol", {})
        if patrol.get("status") == "ok":
            parts.append(_render_stat("PASS", "Tracking Patrol", "good"))
        parts.append("</div>")

        # Stability SDK details (charts + P0 table)
        stability_file = run_dir / name / "fe-stability-analysis.json"
        if stability_file.exists():
            stab_data = json.loads(stability_file.read_text(encoding="utf-8"))
            totals = stab_data.get("totals", {})

            # Hourly chart
            hours, curr_hourly, base_hourly = _extract_hourly(stab_data)
            if hours:
                base_label = stab_data.get("meta", {}).get("base_start_fmt", "baseline")
                curr_label = stab_data.get("meta", {}).get("curr_start_fmt", "current")
                parts.append(_svg_line_chart(
                    hours,
                    [
                        {"name": f"{curr_label} (current)", "data": curr_hourly},
                        {"name": f"{base_label} (baseline)", "data": base_hourly},
                    ],
                    title=f"Hourly error distribution — {name}",
                    caption=f"Partition timezone: {stab_data.get('meta', {}).get('partition_timezone', 'UTC')}",
                ))

            # Category chart
            cats, curr_cat, base_cat = _extract_metrics_chart(stab_data)
            if cats:
                parts.append(_svg_bar_chart(
                    cats,
                    [
                        {"name": f"{curr_label} (current)", "data": curr_cat},
                        {"name": f"{base_label} (baseline)", "data": base_cat},
                    ],
                    title=f"Error categories — {name}",
                ))

            # Severe spike callout
            severe = [m for m in stab_data.get("metrics", [])
                      if m.get("change_pct") is not None and m["change_pct"] > 100]
            for m in severe:
                parts.append(_render_callout(
                    f'{m["key"]} spike: +{m["change_pct"]:.0f}%',
                    f'{_fmt_num(m["base_total"])} → {_fmt_num(m["curr_total"])}',
                    danger=True,
                ))

            # Worsening trend callout
            trend = totals.get("trend", "")
            if "恶化" in trend:
                pct = totals.get("change_pct", 0)
                parts.append(_render_callout(
                    f"Error volume worsening (+{pct}%)",
                    f'{_fmt_num(totals.get("base_total", 0))} → {_fmt_num(totals.get("curr_total", 0))}',
                    danger=True,
                ))

            # P0 table
            p0_issues = _extract_p0_issues(stab_data)
            if p0_issues:
                parts.append(f"<h3>P0 Issues ({len(p0_issues)} total, sorted by impact)</h3>")
                parts.append(_render_p0_table(p0_issues[:15]))

        # Datadog details
        if dd_metrics.get("top_errors"):
            parts.append("<h3>Datadog — Top Errors</h3>")
            parts.append("<table><thead><tr><th>#</th><th>Error</th>"
                         '<th class="num">Count</th></tr></thead><tbody>')
            for err in dd_metrics["top_errors"]:
                parts.append(f'<tr><td>{err["rank"]}</td><td>{escape(err["error"])}</td>'
                             f'<td class="num">{_fmt_num(err["count"])}</td></tr>')
            parts.append("</tbody></table>")

        # Datadog monitors
        if dd_metrics.get("monitors"):
            parts.append("<h3>Datadog — Monitors</h3>")
            parts.append("<table><thead><tr><th>Monitor</th><th>State</th>"
                         "<th>Threshold</th></tr></thead><tbody>")
            for mon in dd_metrics["monitors"]:
                state_cls = "alert" if mon["state"] == "Alert" else ""
                thresh = ", ".join(f'{k}: {v}' for k, v in mon.get("threshold", {}).items())
                parts.append(f'<tr><td>{escape(mon["name"])}</td>'
                             f'<td class="{state_cls}">{escape(mon["state"])}</td>'
                             f"<td>{escape(thresh)}</td></tr>")
            parts.append("</tbody></table>")

        # Sentry details
        if sentry_metrics.get("current") is not None:
            parts.append("<h3>Sentry — Error Delta</h3>")
            parts.append("<table><thead><tr><th>Window</th>"
                         '<th class="num">Errors</th></tr></thead><tbody>')
            parts.append(f'<tr><td>Current</td><td class="num">{_fmt_num(sentry_metrics["current"])}</td></tr>')
            parts.append(f'<tr><td>Baseline</td><td class="num">{_fmt_num(sentry_metrics["baseline"])}</td></tr>')
            delta = sentry_metrics.get("delta", 0)
            delta_pct = sentry_metrics.get("delta_percent", 0)
            parts.append(f'<tr><td><strong>Delta</strong></td>'
                         f'<td class="num"><strong>{delta:+,} ({delta_pct:+.1f}%)</strong></td></tr>')
            parts.append("</tbody></table>")

        parts.append('<div class="divider"></div>')

    # Footer
    parts.append(f'<div class="footer">Run ID: {escape(run_id)} | Generated by monitoring-orchestrator report_html.py'
                 f' | Stability data may be provisional</div>')
    parts.append("</body></html>")

    return "\n".join(parts)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python report_html.py <run_dir>", file=sys.stderr)
        print("  e.g. python report_html.py artifacts/monitoring/20260724T063134Z", file=sys.stderr)
        sys.exit(1)

    run_dir = Path(sys.argv[1]).resolve()
    if not run_dir.is_dir():
        print(f"Error: {run_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    html = generate_html_report(run_dir)
    output = run_dir / "report.html"
    output.write_text(html, encoding="utf-8")
    print(f"HTML report written to {output}")


if __name__ == "__main__":
    main()
