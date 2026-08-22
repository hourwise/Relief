# NaPTAN N4A — source snapshot and revision contract

`transport_source_snapshots` identifies one exact upstream byte snapshot. Its idempotency key is:

```text
<source_namespace>:sha256:<lowercase sha256>
```

The record includes product, URL, byte size, checksum, retrieval time, source publication/revision metadata where supplied, licence, attribution, parser version, schema version, row counts, and lifecycle state. The checksum is validated as 64 hexadecimal characters and `(source_namespace, checksum)` is unique.

The source snapshot is append-only evidence. A future refresh registers a new snapshot even when the publisher identities overlap. StopArea and StopPoint identities are unique only within the exact snapshot, which prevents a changed publisher record from overwriting historical values. Cross-snapshot comparison uses the publisher identity and reports unchanged, changed, added, removed, and reappeared records.

`import_runs` is not reused: it is tied to the existing Toilet Map workflow and would misstate national transport graph capture. A future governed importer may link a transport snapshot to a separate execution record if operational audit later requires it; N4A does not invent that coupling.

Required attribution for the frozen N3 source remains: `Contains public sector information licensed under the Open Government Licence v3.0.`
