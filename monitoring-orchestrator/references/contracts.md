# Normalized Signal Contract

Every path returns this envelope:

```yaml
signal: datadog | stability_sdk | sentry | tracking_patrol
project: string
status: ok | degraded | unavailable
observed_at: ISO-8601 timestamp
duration_ms: integer
summary: string
metrics: object
errors: []
evidence: string
```

Rules:

- `ok` means the real call completed and returned usable data.
- `degraded` means the real call completed partially or returned incomplete data.
- `unavailable` means the call could not be made or returned no usable data.
- `metrics` contains only values returned by the service.
- `errors` contains type, message, and source; secrets must be redacted.
- `evidence` points to the redacted per-signal log.

## Run report contract

Write one normalized run report in both Markdown and JSON:

```yaml
run_id: string # UTC directory timestamp: YYYYMMDDTHHMMSSZ
observed_at: ISO-8601 timestamp
time_range:
  label: string
  start: ISO-8601 timestamp
  end: ISO-8601 timestamp
projects: []
```

Write these files under `artifacts/monitoring/<run_id>/`:

```text
report.md
report.json
```

Keep `time_range` in the report body rather than duplicating it in the filename.

### report.md scope boundary

`report.md` is a **signal-level overview** (~60–100 lines per project). It must NOT contain:

- Full error-by-error breakdown tables
- Spike alert listings
- Governance item lists or repair suggestions
- Hourly breakdown data or category-level sub-sections

Those details live in the evidence JSON files. The report references evidence paths so readers can drill down.

Follow the exact structure and constraints defined in `SKILL.md § Report formatting rules`.

The shared Stability SDK analysis is stored in the same Monitoring run directory. Use the same `run_id`:

```text
artifacts/monitoring/<run_id>/overview.json
artifacts/monitoring/<run_id>/<app_name>/fe-stability-analysis.json
```

Datadog, Stability SDK, and Sentry share one run-level time intent; projects cannot override it. Datadog and Sentry retain exact rolling UTC bounds. Sentry compares that current window with the immediately preceding, equal-duration baseline. `delta` is current minus baseline; percentage delta is omitted when baseline is zero.

Stability SDK uses day granularity for natural-day intents such as `yesterday`. It uses hour granularity only for explicit hour intents such as `last_2h` and `last_24h`, and independently rounds its bounds down to completed hours. Its data-stability window remains governed by `fe-stability-analysis`.
