# Report Formatting Rules

The monitoring report (`report.md`) is a **signal-level overview**, not a detailed analysis dump. Follow these hard rules to ensure consistency across models.

## Structure

```
# Monitoring Report — {observed_at}
  Time range / Project count metadata line

## {project}              ← one H2 per project
### Datadog               ← one H3 per signal, in this fixed order
### Stability SDK
### Sentry
### tracking_patrol

## Evidence               ← evidence table at the end
```

## Per-signal section format

Every signal section MUST contain exactly:

1. **Status badge** — first line: `**Status: {OK|DEGRADED|UNAVAILABLE}**` (uppercase)
2. **One-sentence summary** — plain text describing what happened
3. **Metrics table** — a Markdown table with the signal's key numbers (see template for each signal's required columns)
4. For Stability SDK only: a numbered list of **Top P0 issues** (max 5 items, one line each)

## What NOT to put in report.md

| Forbidden | Where it belongs |
|-----------|-----------------|
| Full error-by-error breakdown tables | `{project}/fe-stability-analysis.json` |
| Spike alert listings (all 19+ rows) | `overview.json` or project analysis JSON |
| Governance item lists | project analysis JSON |
| Repair suggestions / 修复建议 | project analysis JSON |
| Hourly breakdown data | project analysis JSON |
| Category-by-category sub-sections | project analysis JSON |

The monitoring report references evidence files; the reader uses evidence JSONs for drill-down. Do not duplicate analysis-level detail into the report.

## Stability SDK summary constraints

- Report the **totals** (curr, base, change%), **P0 count**, and **spike alert count** in the metrics table.
- List at most **5 top P0 issues** as one-liners (error name + change% or "new").
- Do NOT expand each error category into its own subsection.
- Do NOT include individual error tables, governance items, or repair suggestions.
- Mark provisional data with a blockquote note.

## Datadog summary constraints

- If monitors are found, include a monitor table (name / state / threshold).
- Report the exact total error-log count returned by the Logs Aggregate API.
- Include at most five errors ordered by count descending.
- Do NOT dump raw log entries or full monitor definitions.

## Sentry summary constraints

- Report current count, baseline count, and delta (absolute + percentage) in a table.
- One sentence max for the summary narrative.

## tracking_patrol summary constraints

- If available: one sentence with conclusion and link to the run.
- If unavailable: state why (missing config, missing token, etc.).

## Length target

The full `report.md` for a single project should be **60–100 lines**. Multi-project reports add ~40 lines per additional project. Reports exceeding 150 lines for a single project violate these rules.

## HTML report (`report.html`)

After writing `report.md` and `report.json`, always generate the standalone HTML report by calling:

```python
from report_html import generate_html_report

html = generate_html_report(run_dir)
(run_dir / "report.html").write_text(html, encoding="utf-8")
```

Or from the command line:

```bash
python3 monitoring-orchestrator/report_html.py artifacts/monitoring/<run_id>
```

The HTML report mirrors the structure of `report.md` but adds visual enhancements: SVG line charts (hourly error distribution), SVG bar charts (error category comparison), styled P0 issue tables, and color-coded stat cards. It is self-contained with no external dependencies.
