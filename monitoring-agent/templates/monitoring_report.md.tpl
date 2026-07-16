# Monitoring Report — {{ observed_at }}

Project count: {{ project_count }}

{{#projects}}
## {{ project }}

### Datadog
{{ datadog.summary }}

### Stability SDK
{{ stability_sdk.summary }}

### Sentry
{{ sentry.summary }}

### tracking_patrol
{{ tracking_patrol.summary }}

{{/projects}}

## Evidence

Each signal links to its redacted evidence JSON file. Unavailable or degraded signals must retain their real error reason.
