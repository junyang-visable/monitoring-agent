# Orchestration Whitelist

Only these downstream capabilities are allowed in Phase 1:

| Signal | Capability | Required data |
|---|---|---|
| Datadog | `user-datadog` MCP | error rate, 4xx/5xx, P95 |
| Stability SDK | `fe-stability-analysis` | Stability SDK report fragment for rolling `now-24h..now` |
| Sentry | Sentry REST API | last 24h errors and delta |
| tracking_patrol | GitHub Actions API | latest patrol pass/fail summary |

Out of scope: Defensive SEO, change classification, deploy hooks, Jira ticket creation, and multi-window post-deploy scheduling.
