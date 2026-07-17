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

Datadog, Stability SDK, and Sentry share the resolved `time_range`. Sentry compares that current window with the immediately preceding, equal-duration baseline. `delta` is current minus baseline; percentage delta is omitted when baseline is zero.

Stability SDK receives the equivalent calendar-day intent. Its data-stability window remains governed by `fe-stability-analysis`.
