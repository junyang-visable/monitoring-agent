# Module Map

```mermaid
graph TD
  Config[Configuration] --> Core[Monitoring Core]
  Core --> Adapters[Capability Adapters]
  Core --> Reports[Report Artifacts]
```

- configuration → planned config files.
- monitoring core → planned orchestration entry.
- capability adapters → planned external integrations.
- report artifacts → planned output files.

