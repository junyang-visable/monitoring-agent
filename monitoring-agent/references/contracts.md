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

Sentry uses two adjacent windows: current `now-24h..now` and baseline `now-48h..now-24h`. `delta` is current minus baseline. Percentage delta is omitted when baseline is zero.

Stability SDK always invokes `fe-stability-analysis` for the rolling window `now-24h..now`; it does not use a calendar-day boundary.
