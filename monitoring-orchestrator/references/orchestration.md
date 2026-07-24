# Orchestration Whitelist

Only these downstream capabilities are allowed in Phase 1:

| Signal | Capability | Required data |
|---|---|---|
| Datadog | [`capabilities/datadog.md`](capabilities/datadog.md) | total error count, top five errors by count, monitors, and configured metrics within the resolved `time_range`; use `datadog.service` or fall back to `app_name` |
| Stability SDK | [`capabilities/stability-sdk.md`](capabilities/stability-sdk.md) | one shared analysis for all enabled projects; consume the matching run's overview and project JSON files |
| Sentry | [`capabilities/sentry.md`](capabilities/sentry.md) | errors in the resolved `time_range` and delta against its equal-duration baseline |
| tracking_patrol | [`capabilities/tracking-patrol.md`](capabilities/tracking-patrol.md) | latest patrol pass/fail summary |

## Signal enablement

First resolve every project's effective `enabled` value. Then build the Datadog, Sentry, and tracking patrol project lists independently: these signals may run only when the project is enabled and the signal's project-level `enabled` value is exactly `true`.

Before invoking one of those platform adapters, use `resolve_project_signal_config(config, project_name, signal)` from `adapters/config.py`. It recursively merges the root platform block with the project's signal block, with project values taking precedence. Root blocks contain shared connection and authentication settings; project blocks contain `enabled`, resource identifiers, and exceptional overrides.

Stability SDK uses one root-level configuration block, gated by global `stability_sdk.enabled == true`. When false, skip the path entirely and must not invoke `fe-stability-analysis`. When true, batch every enabled project into one shared call using the same global `output_mode`, intent-driven `time_granularity`, `partition_timezone`, and stability-window settings. `auto` selects hour only for explicit hour intents; all natural-day intents use day. Project-level `stability_sdk` blocks are not supported.

Out of scope: Defensive SEO, change classification, deploy hooks, Jira ticket creation, and multi-window post-deploy scheduling.
