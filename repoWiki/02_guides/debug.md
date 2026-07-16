# Debug Guide

- missing credentials → mark the affected signal unavailable; do not synthesize values.
- external timeout → isolate the signal and record timeout evidence.
- malformed response → record normalization error and continue aggregation.
- logs → planned under `artifacts/monitoring/<timestamp>/<project>/<signal>.json`.

