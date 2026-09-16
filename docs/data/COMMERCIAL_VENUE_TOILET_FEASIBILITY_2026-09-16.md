# Expanded commercial and hospitality toilet feasibility — R5A

## Executive result

The expanded pass confirms that commercial operators often maintain richer toilet/accessibility information than councils expose in open data. The limiting factor is lawful reuse, not the existence of facility information.

No commercial source was promoted to open reusable data, no commercial record was compared nationally with Relief, and the council `READY_NET_NEW` count remains exactly **23**. Commercial `READY_NET_NEW = 0`.

## Hospitality and individual premises

### Strongest direct evidence

- **McDonald's UK**: official help material says the restaurant locator identifies disabled toilets and wheelchair access. Official restaurant guidance also mentions baby-changing facilities. The apparent estate is large; the published material confirms more than 600 restaurants open 24 hours, but that is not a total UK location count. Classification: `PERMISSION_REQUIRED`.
- **KFC UK**: official location pages state that some restaurants have toilets and publish branch-level baby-changing, disability-access, address and opening-hour information. Regional pages show more than 145 London restaurants and more than 90 in the North West, but these are not a UK total. Classification: `PERMISSION_REQUIRED`.
- **Harvester / Mitchells & Butlers**: sample official restaurant pages expose `Disabled Toilets`, `Baby Changing`, opening hours, address and a stable restaurant slug. This is the strongest direct per-premises field pattern found among pub-restaurant families. Classification: `PERMISSION_REQUIRED`.
- **ODEON**: ODEON says AccessAble produces guides for all ODEON cinemas and that the guides contain factual measurements and photographs, including toilet/accessibility information. Classification: `PERMISSION_REQUIRED`.

Other restaurant, pub and café chains have location systems, addresses and opening hours, but the bounded pass did not establish reusable branch-level toilet fields. Brand presence, dining space or a store locator is not evidence that a toilet exists at every branch.

Access semantics remain `customer_only`, `patrons_only` or `unknown` unless the operator explicitly says otherwise. No operator was treated as `public_without_purchase`.

## Shopping centres and outlet destinations

Destination venues are more promising than individual tenants because one agreement could describe communal washrooms rather than thousands of separate shops.

- **Westfield UK**: official pages describe accessible toilets, RADAR-key access, staff assistance, parent rooms and a hoist/changing table at a named location. This is `WASHROOM_BLOCK_LOCATION`, not a centre centroid. [Westfield accessible toilets](https://www.westfield.com/en/united-kingdom/london/services/accessible-toilets)
- **Landsec-managed centres**: official centre maps expose toilets, accessible toilets, Changing Places, baby changing and stoma-friendly facilities, sometimes as distinct map symbols. These are useful washroom-block evidence but do not automatically provide machine coordinates. [Landsec centre guide example](https://content.landsec.com/media/nmobhrc2/65412-land-sec-large-print-guide-ss25_v4.pdf)
- **McArthurGlen Designer Outlets**: official outlet pages expose disabled toilets, Changing Places, baby changing, opening hours, guest services and AccessAble guides. This is the strongest outlet-family partnership target. [McArthurGlen Ashford services](https://www.mcarthurglen.com/en/outlets/uk/designer-outlet-ashford/services/)
- **Clarks Village**: an official centre map exposes toilets, baby changing and disabled facilities. It is a useful bounded pilot, not evidence of a national reusable feed. [Clarks Village map](https://content.landsec.com/media/wpeeww1q/cv_centre-map_oct25.pdf)
- Bicester Village and other outlet families remain permission-gated because a current reusable structured facility feed was not established in this pass.

Centre-level facility data is potentially valuable under a future place/complex model. Under the current canonical facility model, centre-level coordinates must stay outside automatic production-ready status unless the washroom block is specifically located and the representation is product-approved.

## Leisure and entertainment

ODEON is the clearest opportunity because the operator has a formal AccessAble programme covering all cinemas. Vue, Cineworld, Showcase, Hollywood Bowl and Tenpin may have useful branch information, but no lawful structured toilet feed was established here. Tenpin operational material proves toilets exist in bowling centres generally; it does not provide a reusable branch dataset.

No leisure-chain records were counted as ready.

## Data-reuse classifications

| Family | Classification | Direct evidence | Location precision | Ready count |
|---|---|---|---|---:|
| McDonald's, KFC, Harvester | `PERMISSION_REQUIRED` | strong sample/per-site fields | premises-level pages | 0 |
| ODEON / AccessAble | `PERMISSION_REQUIRED` | rich accessibility guide programme | premises/guide-level | 0 |
| Westfield | `PERMISSION_REQUIRED` | accessible toilets, RADAR, parent rooms | washroom-block descriptions | 0 |
| Landsec centres | `PERMISSION_REQUIRED` | centre maps with multiple facility symbols | washroom-block map locations | 0 |
| McArthurGlen | `PERMISSION_REQUIRED` | toilets, accessible, Changing Places, baby changing | centre/block-level | 0 |
| Clarks Village | `PERMISSION_REQUIRED` | official centre map | centre/block-level | 0 |
| Other retail, pub, cinema and leisure families | `NO_STRUCTURED_FACILITY_DATA` or `LICENCE_UNCLEAR` | insufficient bounded evidence | unknown | 0 |

## Partnership ranking

The planning score is 1–5 in each dimension: UK scale, apparent toilet coverage, facility richness, likely uniqueness and ease of obtaining permission. It is not a count, probability or authorization.

### Hospitality / restaurant targets

1. McDonald's UK — largest apparent premises opportunity with explicit accessibility locator fields.
2. Harvester / Mitchells & Butlers — direct toilet, disabled-toilet, baby-changing, address and hours fields.
3. KFC UK — large estate and direct per-location toilet/accessibility examples.
4. ODEON — formal all-cinema AccessAble accessibility programme.
5. Wetherspoon / Greene King / Marston's / Stonegate — large estates, but direct structured toilet coverage remains unproven.

### Retail-centre / outlet targets

1. McArthurGlen Designer Outlets — multi-centre scale with direct Changing Places and accessibility fields.
2. Landsec-managed centres — richest map vocabulary, including stoma-friendly and Changing Places facilities.
3. Westfield UK — precise RADAR and accessible-toilet descriptions at major centres.
4. Hammerson / British Land / NewRiver portfolio partnership — strong portfolio leverage, but common facility schema unproven.
5. Clarks Village — good bounded centre-map pilot.

## Common operator export request

Request a governed export containing:

- operator, stable site ID, site name, site type;
- address, postcode, latitude and longitude;
- ordinary toilet, accessible toilet, Changing Places, baby changing, RADAR-key and stoma-friendly flags;
- access scope: public without purchase, customer-only, patrons-only, visitor-only, secure/ticketed or unknown;
- store/centre opening hours and toilet-specific opening hours;
- last verified and source-updated timestamps;
- for large centres, toilet-block ID/name, internal map description and separate block coordinates;
- explicit permission to store, transform, compare and display the data, plus attribution requirements.

## Strategic answers

1. **Largest lawful hospitality opportunity:** McDonald's is the strongest apparent scale candidate, but permission is required and direct toilet coverage is not universal.
2. **Richest centre/outlet opportunity:** McArthurGlen and Landsec are strongest overall; Westfield has the clearest RADAR/hoist location detail.
3. **Usefulness of centre-level records:** useful as supporting place/complex evidence, but not automatically as a current Relief facility point. Multiple blocks must remain distinct when independently located.
4. **Legitimately reusable structured commercial data today:** none established in this pass.
5. **Three highest-return permission requests:** McDonald's UK, McArthurGlen, and Landsec; if prioritising direct public-facing premises rather than destination centres, replace Landsec with Harvester/Mitchells & Butlers.
6. **Programme value:** worth pursuing only as a small number of partnership requests after the 23-record council batch. Councils remain the faster low-friction route; commercial data has higher potential richness but materially higher permission and access-semantics risk.

Classification: **`PERMISSION_REQUIRED`**. Commercial `READY_NET_NEW = 0`.
