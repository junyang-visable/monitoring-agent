# Orchestration Whitelist

Only these downstream capabilities are allowed in Phase 1:

| Signal | Capability | Required data |
|---|---|---|
| Datadog | `user-datadog` MCP | error rate, 4xx/5xx, P95 within the resolved `time_range`; use `datadog.service` or fall back to `app_name` |
| Stability SDK | `fe-stability-analysis` (`app_names`, `output_mode=analysis_only`, `output_dir=artifacts/fe-stability-analysis/<run_id>/`) | one batch query plan for enabled projects; consume the overview plus dedicated project JSON files in the matching run directory; no separate Stability Markdown report |
| Sentry | Sentry REST API | errors in the resolved `time_range` and delta against its equal-duration baseline |
| tracking_patrol | GitHub Actions API | latest patrol pass/fail summary |

Out of scope: Defensive SEO, change classification, deploy hooks, Jira ticket creation, and multi-window post-deploy scheduling.
