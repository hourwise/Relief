# UK source expansion Phase 3 — Sheffield adjudication and access handoff

**Status:** `SHEFFIELD ADJUDICATED / MAJOR FEED ACCESS HANDOFF / PRODUCTION APPLY NOT AUTHORIZED`
**Review date:** 2026-08-20
**Starting commit:** `1a8b6252a9584dd286518425a489b1f86aa8e0cf`

## Sheffield adjudication

The official Sheffield ArcGIS layer metadata confirms that the source exposes
only `objectid`, `uprn`, and `blpu_state`. All 41 downloaded records have
`blpu_state=2`, but none has a display name. This is a source limitation, not a
normalization failure.

The exact read-only PostGIS check found:

- 18 rows with exactly one existing Relief facility within 100 metres;
- 23 rows with no existing Relief facility within 100 metres;
- 0 rows with multiple nearby facilities;
- 0 exact Sheffield source links.

The 18 proximity results are not safe `SOURCE_LINK` operations. Without a name
or another authoritative identity join, proximity cannot distinguish a true
duplicate from a separate toilet, a coordinate discrepancy, or a facility that
has already been represented by a different source. The 23 other rows are not
safe `INSERT` operations because they lack names. No `ENRICHMENT` operation is
supported either.

The frozen package therefore contains 41
`DEFER_EXTERNAL_VERIFICATION` decisions and exactly zero `INSERT`,
`SOURCE_LINK`, or `ENRICHMENT` operations. See
[`UK_PUBLIC_SOURCE_EXPANSION_SHEFFIELD_PACKAGE.json`](data/UK_PUBLIC_SOURCE_EXPANSION_SHEFFIELD_PACKAGE.json).

The next acceptable evidence is an authoritative name-bearing source or a
council/Ordnance Survey/UPRN lookup whose reuse rights and stable facility
identity are explicit. No reverse-geocoder or community map was promoted into
the canonical ingestion path.

## National Rail registration handoff

Use the official [NRE Data Feeds request form](https://rdg-forms.plumsail.io/76dbbe48-b1f9-4280-b463-321272ca47fa).
Request the current Knowledgebase station-facilities feed, specifically the
Stations XML product and any Stations Made Easy detail required to interpret
facility access. If the product is not available in the form, check the
[Rail Data Marketplace](https://raildata.org.uk/).

Return the approved product name, endpoint or download mechanism, NRE licence
and attribution wording, rate limits, update/version field, and stable station
identifier. National Rail’s developer page says Knowledgebase is available via
self-sign-up and REST/XML access; the feed terms must be retained with the
future snapshot. Do not provide a website scrape or unofficial mirror instead.

## TfL registration handoff

Use the [TfL API portal](https://api-portal.tfl.gov.uk/). TfL’s documented flow
is: register and activate the account, sign in, open Products, create the 500
requests data-plan subscription, then retrieve the API key from Profile. The
next source request should identify the current station-facilities feed and
the current bus-stations-with-public-toilets resource.

Return each resource’s identifier, schema/version, refresh cadence, terms, and
attribution wording. TfL requires the attribution `Data provided by Transport
for London`. Keep the API key out of Git and out of `EXPO_PUBLIC_*` variables;
the next ingestion run should receive it through a local/server-only secret
mechanism. TfL’s [open-data page](https://tfl.gov.uk/info-for/open-data-users/our-open-data?intcmp=3671)
also states that the example feeds are not updated and are for demonstration
only.

## Boundary

This batch performed no canonical, source-link, provenance, staging, import-run,
migration, RLS, grant, or Edge Function mutation. The required production
mutation count remains `0`.
