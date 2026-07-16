# Deploy Guide

## Steps

1. Package the skill and configuration.
2. Inject credentials through the runtime secret store.
3. Invoke from the supported agent or cron runtime.

## Commands

- build → not defined.
- deploy → not defined.

```mermaid
flowchart LR
  Source[Skill and Config] --> Package[Package]
  Package --> Runtime[Agent or Cron]
  Runtime --> External[External Services]
  External --> Artifacts[Reports and Evidence]
```

