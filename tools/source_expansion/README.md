# UK public-source expansion

This package is a bounded, read-only discovery and ingestion-preparation layer
for additional UK public-toilet sources. It does not connect to Supabase, does
not create a staging row, and has no apply option.

The registry records the source publisher, official source page, licence or
access-term status, attribution, parser version, and the boundary that must be
resolved before a source can become `CURRENT_SOURCE_READY`.

The pipeline accepts a locally obtained source snapshot and emits normalized
evidence with immutable snapshot metadata, source-record identity, explicit
null semantics, duplicate checks, conservative read-only comparison results,
and an all-zero mutation ledger. Raw snapshots belong in the ignored local
cache; only sanitized derived evidence should be committed.

The TfL bus-toilet example is intentionally treated as enrichment-only: its
published example has station names and toilet flags but no coordinates, and
TfL says the example feed is not updated. Live TfL data requires registration.
National Rail Knowledgebase data likewise requires registered access and the
applicable NRE feed terms. DataMapWales metadata names PSGA for the National
Toilet Map, so no OGL assumption is made.

Example:

```text
python -m tools.source_expansion.pipeline \
  --source-id tfl_bus_public_toilets \
  --input <local-official-snapshot.csv> \
  --output docs/data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REVIEW.json \
  --source-version official-example-not-production
```

Any future canonical ingestion must be a separately approved, source-specific
generation with current licensing, stable identity, coordinate provenance,
duplicate analysis, and a separate manifest. This package never broadens the
existing Toilet Map authorization.
