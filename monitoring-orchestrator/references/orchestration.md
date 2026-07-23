# Orchestration Whitelist

Only these downstream capabilities are allowed in Phase 1:

| Signal | Capability | Required data |
|---|---|---|
| Datadog | [`capabilities/datadog.md`](capabilities/datadog.md) | error rate, 4xx/5xx, P95 within the resolved `time_range`; use `datadog.service` or fall back to `app_name` |
| Stability SDK | [`capabilities/stability-sdk.md`](capabilities/stability-sdk.md) | one shared analysis for all enabled projects; consume the matching run's overview and project JSON files |
| Sentry | [`capabilities/sentry.md`](capabilities/sentry.md) | errors in the resolved `time_range` and delta against its equal-duration baseline |
| tracking_patrol | [`capabilities/tracking-patrol.md`](capabilities/tracking-patrol.md) | latest patrol pass/fail summary |

Out of scope: Defensive SEO, change classification, deploy hooks, Jira ticket creation, and multi-window post-deploy scheduling.
