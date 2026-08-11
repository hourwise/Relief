# Toilet Map Apply 1A — post-apply verification specification

This is a future verification contract. It contains no live result and is not
evidence that Apply 1A has run.

Immediately after a successful database transaction, the privileged operator
must run the checks below using the same run UUID and pinned manifest.

## Required assertions

1. The audit run is `status = completed` and
   `transaction_outcome = committed`.
2. `requested_operation_count = 48`, `ready_count = 48`,
   `applied_count = 48`, `stale_count = 0`, and `failed_count = 0`.
3. Each of the 48 exact facility IDs still exists and each target field equals
   its approved `proposed_value`.
4. Each target provenance entry exists and records the exact source record ID,
   source checksum, import run ID, `EXACT_SOURCE_ID`, `HIGH`, policy/version,
   approved plan SHA, approved manifest SHA, review commit, previous `null`,
   and the new boolean value.
5. The only changed facility columns are the 48 approved scalar fields and the
   expected `updated_at` trigger effects. No unrelated facility field changes.
6. `public.facility_sources` row count and row contents are unchanged.
7. `publication_status` is unchanged for every affected facility.
8. Facility count is unchanged; no facility was created or deleted.
9. No unrelated provenance key changed.
10. The audit row records the exact project, source, plan, manifest, review,
    engine, and transaction outcome identities.

## Deterministic evidence shape

The future postcheck artifact should be canonical JSON with this shape:

```json
{
  "schema_version": "1.0",
  "simulated_only": false,
  "run_id": "<uuid>",
  "project_ref": "bgwxrxkmyaihplaloely",
  "approved_plan_sha256": "<exact pinned value>",
  "approved_manifest_sha256": "<exact pinned value>",
  "source_checksum": "<exact pinned value>",
  "requested_operation_count": 48,
  "applied_count": 48,
  "facility_count_before": "<sha256/count evidence>",
  "facility_count_after": "<sha256/count evidence>",
  "facility_sources_before_after_equal": true,
  "publication_status_unchanged": true,
  "unrelated_provenance_unchanged": true,
  "operations": [
    {
      "operation_id": "<approved>",
      "facility_id": "<approved>",
      "field": "<allowlisted>",
      "expected_value": true,
      "observed_value": true,
      "provenance_present": true
    }
  ],
  "audit_transaction_outcome": "committed",
  "verification_failures": []
}
```

The current branch must never populate this shape with fabricated live values.
