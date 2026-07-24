# Stability SDK Capability

## Invocation

This capability is controlled and configured only by the root-level global `stability_sdk.enabled == true` block. Project-level `stability_sdk` blocks are invalid and must be ignored.

When the global switch is false, skip this capability entirely: must not invoke `fe-stability-analysis`, must not write Stability evidence or analysis artifacts, and must not treat the skipped signal as unavailable.

When the global switch is true, validate the root-level configuration and build `stability_projects` from all enabled projects. Invoke `fe-stability-analysis` once per monitoring run for the entire non-empty list. If the list is empty, record a configuration error without invoking the skill. Pass:

- sorted standard `app_names`
- the resolved time intent
- global `stability_sdk.time_granularity`
- global `stability_sdk.partition_timezone`
- global `stability_sdk.stability_window_hours`
- global `stability_sdk.output_mode` (must be `analysis_only`)
- `output_dir=artifacts/monitoring/<run_id>/`

For `time_granularity=hour`, the SDK queries completed `ds/hh` partitions in the configured partition timezone.

## Output consumption

Consume the shared `overview.json` and each `{app_name}/fe-stability-analysis.json` from the matching run directory. Attach each project result to the corresponding monitoring project. Do not generate a separate Stability Markdown report.

The SDK's cache behavior is governed by the `fe-stability-analysis` cache policy. The monitoring run directory remains isolated by the shared UTC `run_id`.
