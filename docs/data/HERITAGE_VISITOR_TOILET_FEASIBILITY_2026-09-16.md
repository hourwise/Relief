# Heritage and visitor-site toilet feasibility — R5A

## Finding

Wikidata is the strongest lawful structured lead found in this pass. A bounded `P912 (has facility)` query found 2,906 statements across 1,258 unique UK-qualified items with toilet-related labels and coordinates. The item counts overlap across ordinary, accessible and Changing Places statements; they are not additive.

The structured statements are reusable under Wikidata's CC0 terms, but the current query does not prove that the coordinate is the physical toilet, that access is public without entry, or that the claim is current. The production-ready heritage count is therefore **0**. The measured 1,258-item cohort is a review/coarse-location opportunity, not an ingestion pool.

## Lawful source assessment

- VocalEyes Heritage Access 2022 demonstrates meaningful scale — 1,883 museum/heritage sites are described in the published project — but no raw database reuse licence or downloadable structured source was established. Classify `PERMISSION_REQUIRED`.
- Historic England NHLE is useful OGL identity/geometry backbone data. It does not itself prove a toilet and is `OPEN_IDENTITY_BACKBONE_ONLY`.
- National Trust and English Heritage publish useful site facility information, but the bounded check found no open structured facility export. Classify `HIGH_VALUE_PARTNERSHIP_SOURCE / PERMISSION_REQUIRED`; do not scrape.
- Other museum/heritage catalogues may improve identity coverage, but a catalogue of venues without an explicit toilet field is not a toilet source.

## Production comparison sample

A stable first-100-QID sample was compared read-only with the 15,709 current Relief facilities. Four items were within 25m, 16 within 100m, 33 within 250m and 47 beyond 250m. The median nearest-facility distance was 241.6m and p95 5,952.0m. These are diagnostic scale figures only: proximity is not toilet identity and the venue coordinate is not a toilet-specific coordinate.

## Next gate

The next heritage slice should be a small, separately authorized evidence review that adds only toilet-specific coordinate/access qualifiers where directly supported. It should not start with automatic creation from the 1,258-item cohort.
