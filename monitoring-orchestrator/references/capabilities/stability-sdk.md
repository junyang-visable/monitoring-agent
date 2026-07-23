# Stability SDK Capability

## Invocation

Invoke `fe-stability-analysis` once per monitoring run for all enabled Stability projects. Pass:

- sorted standard `app_names`
- the resolved time intent
- `stability_sdk.time_granularity`
- `partition_timezone`
- `stability_window_hours`
- `output_mode=analysis_only`
- `output_dir=artifacts/monitoring/<run_id>/`

For `time_granularity=hour`, the SDK queries completed `ds/hh` partitions in the configured partition timezone.

## Output consumption

Consume the shared `overview.json` and each `{app_name}/fe-stability-analysis.json` from the matching run directory. Attach each project result to the corresponding monitoring project. Do not generate a separate Stability Markdown report.

The SDK's cache behavior is governed by the `fe-stability-analysis` cache policy. The monitoring run directory remains isolated by the shared UTC `run_id`.

