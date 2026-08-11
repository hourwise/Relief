# Toilet Map Reconciliation Review 1

> READ-ONLY review. No Supabase mutation, migration, importer, or apply command was used.

## Fixed snapshot

- Foundation SHA: `b074bc314ab72b1d3cb8b4809e7ed9d93f5df4d0`
- Source update: `2026-08-11T01:00:00+00:00`
- Input checksum: `f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624`
- Input records / bytes: **16,057 / 7,856,657**

## Before / after

- Before: `{'relief_baseline_facility_count': 15584, 'current_toilet_map_input_record_count': 16057, 'current_toilet_map_active_records': 16057, 'current_toilet_map_removed_or_inactive_records': 0, 'current_toilet_map_unknown_status_records': 0, 'exact_source_id_matches': 15567, 'high_confidence_inferred_matches': 0, 'ambiguous_candidates': 1, 'likely_new_facilities': 31, 'unchanged_linked_records': 15526, 'changed_linked_records': 41, 'upstream_removed_inactive_records': 0, 'previously_linked_relief_records_absent_upstream': 17, 'invalid_source_records': 458, 'source_quality_warning_records': 2746, 'potential_duplicate_clusters': 0}`
- After: `{'relief_baseline_facility_count': 15584, 'current_toilet_map_input_record_count': 16057, 'current_toilet_map_active_records': 16057, 'current_toilet_map_removed_or_inactive_records': 0, 'current_toilet_map_unknown_status_records': 0, 'exact_source_id_matches': 15567, 'high_confidence_inferred_matches': 0, 'ambiguous_candidates': 1, 'likely_new_facilities': 31, 'unchanged_linked_records': 15526, 'changed_linked_records': 41, 'upstream_removed_inactive_records': 0, 'previously_linked_relief_records_absent_upstream': 17, 'invalid_source_records': 458, 'source_quality_warning_records': 2746, 'potential_duplicate_clusters': 0}`
- Explanation: Top-level match/lifecycle totals remain unchanged. The day-aware comparison exposes one additional opening-hours omission (62 to 63); same-day agreement, explicit source additions, and day conflicts remain separately classified instead of collapsing a partial schedule into same.

## Out-of-envelope classification

- Counts: `{'OTHER_VALID_GEOGRAPHY': 198, 'CONTINENTAL_EUROPE': 221, 'REPUBLIC_OF_IRELAND': 38, 'OBVIOUS_COORDINATE_CORRUPTION': 1}`
- Ranges: `{'OTHER_VALID_GEOGRAPHY': {'latitude_min': -45.0299443, 'latitude_max': 51.0453246, 'longitude_min': -122.47492218, 'longitude_max': 174.722456038}, 'CONTINENTAL_EUROPE': {'latitude_min': 38.346941712, 'latitude_max': 59.326033019, 'longitude_min': -9.158335626, 'longitude_max': 23.589671552}, 'REPUBLIC_OF_IRELAND': {'latitude_min': 51.482331671, 'latitude_max': 54.23330666, 'longitude_min': -10.46235323, 'longitude_max': -9.0137526}, 'OBVIOUS_COORDINATE_CORRUPTION': {'latitude_min': 42.2524599, 'latitude_max': 42.2524599, 'longitude_min': -87.8403805, 'longitude_max': -87.8403805}}`
- Valid external geography should be distinguished from invalid/corrupt source data as `OUT_OF_SCOPE` in future policy; production scope is unchanged here.

| Category | ID | Name | Latitude | Longitude | Reason |
|---|---|---|---:|---:|---|
| OTHER_VALID_GEOGRAPHY | 00ec010072e80d78c6533cec | BV Nhi đồng 2 | 10.781271929 | 106.701568365 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| OTHER_VALID_GEOGRAPHY | 0134d0ada3e6cc2afd3c284d | Swimming Pool | 41.8439673 | -72.939212 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| OTHER_VALID_GEOGRAPHY | 020576934a1398b9ba0ece23 | PVT-LTR | 10.771188136 | 106.691515446 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| CONTINENTAL_EUROPE | 02699d114e48200dc8d1ee15 | Poperinge - Hop Museum | 50.855259154 | 2.721911073 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| CONTINENTAL_EUROPE | 02cc56574891270c067356be | Multi-Storey Car Park Toilets | 46.949008017 | 7.451769412 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| REPUBLIC_OF_IRELAND | 0332494afedb06145742202d | Baltimore | 51.482331671 | -9.374325871 | Coordinate falls inside the deterministic Republic of Ireland bounding box and outside the current UK envelope. |
| OTHER_VALID_GEOGRAPHY | 03ab0c1c424fb41bc762a20c | BV Từ Dũ | 10.768779781 | 106.685222983 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| OTHER_VALID_GEOGRAPHY | 03acb6e368dec039481e92f8 | Khu B CV Gia Định | 10.811782104 | 106.677010059 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| OTHER_VALID_GEOGRAPHY | 04b6cc3550b7a1490fdbfce7 | Cao Bá Quát | 10.777859761 | 106.704191566 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| CONTINENTAL_EUROPE | 06f1fb6c90c694337f24829b | Lion toilet | 50.961901847 | 6.978389025 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| OTHER_VALID_GEOGRAPHY | 070bc5a1351dc1c9d19dc63d | UBND Q5 | 10.755251525 | 106.666688919 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| CONTINENTAL_EUROPE | 07c0627abb0f6de81e308c05 | Aire de Ghyvelde (Westbound) | 51.053622509 | 2.547025681 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| OTHER_VALID_GEOGRAPHY | 083aa59230e0a59a33018263 | 33 Tân Sơn Nhì | 10.796298183 | 106.630355716 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| OTHER_VALID_GEOGRAPHY | 08a3e920268b6d018303863c | bo ho 5 | 21.026748022 | 105.851769447 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| CONTINENTAL_EUROPE | 0a5f3f00dcd3a6c2411a09ae | Texaco Filling Station | 51.543379227 | 3.604009151 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| REPUBLIC_OF_IRELAND | 0b87d486bbe6ebf7810ac3bb | Ballydonegan Public toilets | 51.633195678 | -10.061617792 | Coordinate falls inside the deterministic Republic of Ireland bounding box and outside the current UK envelope. |
| CONTINENTAL_EUROPE | 0bfd817788583af3c68bb2a6 | Poperinge Train Station | 50.854492115 | 2.735949755 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| OTHER_VALID_GEOGRAPHY | 0c076f40bc8fc9142ac4fa83 | BV Chợ Rẫy | 10.757449183 | 106.658357978 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |
| CONTINENTAL_EUROPE | 0ca2a3065fd83cc64ae16a02 | Aire de Zutkerque | 50.847154655 | 2.03204155 | Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope. |
| OTHER_VALID_GEOGRAPHY | 0d06fef214f05d070a4ae747 | BV Phạm Ngọc Thạch | 10.757849714 | 106.665878892 | Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt. |

The machine-readable report contains all 458 records. The representative table is intentionally capped for readability.

## All 31 likely-new records

| Source ID | Name | Classification | Nearest evidence | Reason |
|---|---|---|---|---|
| 02760f05f626d67f29aabc09 | Armada Way Accessible Toilets | POSSIBLE_DUPLICATE | Armada Way underground public conveniences; 33.122m; sim 0.40625 | A nearby facility is very close geographically but has materially different naming. |
| 059ffb72ce5bab427a2de7a1 | RSPB Lochwinnoch | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 14abe0d9023602979da37362 | Chill @ Chives Cafe | CONFIRMED_LIKELY_NEW | Derby Bus Station; 441.214m; sim 0.066667 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 177c0eaa345c7ce7677eb13c | Becky's Barn Cafe | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 1c7f7f431a450c0659bb4d18 | Neilston Train Station | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 1d9034f071dab8ee5ee5181f | Exeter City Library | CONFIRMED_LIKELY_NEW | St. Stephens House, Changing Places and Baby Change; 144.314m; sim 0.20339 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 230fbaf1acae2242e54a0ad8 | Council House Entrance Lobby | CONFIRMED_LIKELY_NEW | Unnamed Toilet; 82.773m; sim 0.315789 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 232bc6a31fc2f51f403d077f | Canary Wharf (Jubilee Line) underground station (ticket entrance area) (unpaid area) (accessible toilet only) | CONFIRMED_LIKELY_NEW | The Alchemist; 53.932m; sim 0.1 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 319a320ae4671c38ef383f6f | Birds Bakery Cafe | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 33aebf2ab67de1b196b4ca15 | Neilston Library | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 3b49d8f21b9a69ca0eb667ad | McDonalds | CONFIRMED_LIKELY_NEW | The Hart & Spool; 140.625m; sim 0.190476 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 4090f92f66ab256d2938b037 | Marks and Spencer | CONFIRMED_LIKELY_NEW | Marriott's Walk; 73.168m; sim 0.285714 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 4d5844e4e99d8bf8ba9d7e11 | Neilston Leisure Centre | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 53a780f6c6ee963bdd2c1c1e | Club Oasis | CONFIRMED_LIKELY_NEW | Scratby, Rottenstone Lane.; 500.327m; sim 0.193548 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 615f57c3f055e295b30e927b | Starbucks on Sauchiehall Street | CONFIRMED_LIKELY_NEW | Glasgow Royal Concert Hall; 102.553m; sim 0.431373 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 6de34ddb3ac6668d98c2334c | Becky's Barn Cafe | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 6e3587fd50aaf24da80ea357 | Precinct walk public toilet | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| 7e4d881dc784d265df20994a | Weston Museum | CONFIRMED_LIKELY_NEW | Sanatorium; 236.98m; sim 0.454545 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 80f7d5d63fa3acde2acc0e2b | King George Park | CONFIRMED_LIKELY_NEW | The Three Crowns; 828.261m; sim 0.071429 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 857c4ddc685fa35c8a6eb0c1 | Lidl Tilehurst | CONFIRMED_LIKELY_NEW | KFC; 163.529m; sim 0.0 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| 8f8624f23652e467aae5184c | Dobbies | CONFIRMED_LIKELY_NEW | BP Petrol Station; 147.349m; sim 0.181818 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| a318d929c92290531ea29e1d | Lidl Reading West | CONFIRMED_LIKELY_NEW | Tesco Reading W Extra; 600.918m; sim 0.606061 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| b7a6f2ba6748614e3a73877e | Rosa's Thai, Reading | CONFIRMED_LIKELY_NEW | Trafalgar Square; 98.109m; sim 0.322581 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| ce7f310c0293474778934cc5 | Westfield London (lower level, next to Läderach shop) | POSSIBLE_DUPLICATE | Westfield London; 19.704m; sim 0.517241 | A nearby facility is very close geographically but has materially different naming. |
| d4e39ccaa0d82f641d81a998 | Meopham Green Public Toilets | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| d6f5596b9d08edc4cfeac7df | Weston-super-Mare Railway Station | CONFIRMED_LIKELY_NEW | Locking Road car park; 154.0m; sim 0.255319 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| defc1a12a8026d061ec6c37f | Manor Café | CONFIRMED_LIKELY_NEW | Tesco; 692.189m; sim 0.142857 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| e7afff68c09835856392fee7 | Whirlies McDonald's | CONFIRMED_LIKELY_NEW | none within 1km | No Relief facility is within the 1km review radius. |
| f3638d10f57ada4c1cf16566 | Petrol and diesel filling Station | CONFIRMED_LIKELY_NEW | Codsall Community Hub; 533.045m; sim 0.25 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| fb968371c27222e3f758d8e0 | Silverburn Restaurant Concourse Toilets | CONFIRMED_LIKELY_NEW | Unnamed Toilet; 52.507m; sim 0.285714 | Nearby evidence is below the review thresholds for an existing-facility explanation. |
| fc1cf7d0e3edb420148aad20 | Bushey Rose Garden | CONFIRMED_LIKELY_NEW | The Red Lion Pub; 401.704m; sim 0.344828 | Nearby evidence is below the review thresholds for an existing-facility explanation. |

## All 17 absent source IDs

| Old source ID | Facility | Classification | Nearest unseen source evidence | Reason |
|---|---|---|---|---|
| 2085e12709f990ca33f76124 | Sunshine Cafe | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| 23ad0e71522812a22f84ab1e | josh kingham | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| 2bdb80decb9602132b1320e2 | Torpoint ferry lanes devonport | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| 459c11b3fb79b6bf6f33caaf | Cabot Place - Mall, Level -1 (by Flip Out & Leon) | UNRESOLVED | 232bc6a31fc2f51f403d077f; 289.714m; sim 0.264463 | Nearby current source evidence exists but is not sufficiently similar to classify safely. |
| 750f8541c3fbbdae1f1d7d24 | Kirkgate Market | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| 8395257ee9cd73946ddca152 | The Hart & Spool | UNRESOLVED | 3b49d8f21b9a69ca0eb667ad; 140.625m; sim 0.190476 | Nearby current source evidence exists but is not sufficiently similar to classify safely. |
| 8b3f7e4ae100ba40cd8adc41 | Unnamed Toilet | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| acd99438140a65b1c9bd75d6 | Riverside Shopping Centre | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| c4e81d85d6dd8976f67cac42 | High Street | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| cc951fdb4053e76d9b9889a4 | High Street Car Park | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| cee05cda1b7fbad0f6aa7900 | Shenley Parish Council | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| d4fb29220671733629b0a205 | Addlestone Station | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| e18069104e711b9f62758c3a | John Lewis Department Store - Watford | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| e424999240e9922173681e57 | Oastler Centre Market | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| e783b2bc1c9bf2336fd371ed | Torpoint Ferry | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| ee365d235bd52120b62472d5 | Kirkgate Centre | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |
| fa3fba0530eda567254df9fd | Spice Up | UNRESOLVED | none within 1km | No unseen current source record is within the 1km review radius; absence alone cannot prove removal. |

Proposed strong crosswalk candidates: `[]`.

## Ambiguous candidate

- `46da2d339d53dfbd632099f3` **Hemsby Beach Toilets**: `SAME_FACILITY_HIGH_CONFIDENCE_AFTER_REVIEW`.
  - `f9aa75af-9dd4-4d1c-a59d-9054549a03f9` Hemsby Beach.; 15.546m; similarity 0.758621; links `['63b46bf28afc2f4315c11993']`.

## All 41 changed linked records

- Name change categories: `{'suspicious': 6, 'expanded/more descriptive name': 7, 'materially different identity': 6}`
- Coordinate movement buckets: `{'<=5m': 1, '>5m to 25m': 1, '>25m to 100m': 4, '>100m': 2, 'extreme/suspicious (>1km)': 1}`
- Amenity classifications: `{'is_accessible:SOURCE_AND_RELIEF_DISAGREE': 15, 'requires_radar_key:SOURCE_AND_RELIEF_DISAGREE': 4, 'requires_radar_key:RELIEF_UNKNOWN_SOURCE_KNOWN': 14, 'has_baby_changing:RELIEF_UNKNOWN_SOURCE_KNOWN': 16, 'is_gender_neutral:RELIEF_UNKNOWN_SOURCE_KNOWN': 15, 'is_gender_neutral:SOURCE_AND_RELIEF_DISAGREE': 1, 'is_free:RELIEF_UNKNOWN_SOURCE_KNOWN': 1, 'is_accessible:RELIEF_UNKNOWN_SOURCE_KNOWN': 2, 'has_baby_changing:SOURCE_AND_RELIEF_DISAGREE': 1}`
- Opening-hours day-level counts: `{'records_with_conflicting_days': 11, 'source_conflicting_days': 73, 'records_with_source_omitted_days': 2, 'source_omitted_days': 9}`

| Source ID | Facility | Changed fields |
|---|---|---|
| 048aa55c0c44d7aba3818f53 | Silverburn Shopping Centre 2 (`7213db1f-fac9-4cec-8c9b-83b23336c7ce`) | opening_hours |
| 0919600062e662375ae07ca5 | Buckshaw Parkway (`493207a8-cf6c-4d8d-ba32-614983baa427`) | is_accessible, requires_radar_key |
| 1050bb89634e172910d88402 | Durham Clayport Library (`5742c567-92c6-47f3-b755-9c936886d905`) | has_baby_changing, is_gender_neutral, requires_radar_key |
| 14a1c966324c38bd332208b1 | Unnamed Toilet (`e0d843f6-931d-42fa-811f-54d333c1bff9`) | name |
| 1e71d9a13cbb1d1f32455bff | Promenade (Senna Road) (`4a6cff49-1286-47e2-8c0e-9678638e08b6`) | is_accessible, is_gender_neutral, longitude |
| 2793dd03c8dcacd811e23691 | Unnamed Toilet (`ba77f1fd-b878-4347-beeb-26f5a8a38291`) | has_baby_changing, is_accessible, is_gender_neutral, name, opening_hours |
| 2a7ea23fbbb9a8e0c3db5ffd | Port Jack (`cf385907-c050-44d7-bd14-b5cb4be94a8e`) | has_baby_changing, is_accessible, is_gender_neutral, requires_radar_key |
| 2af1f5fe27a2e4a6ee9df327 | Loch Promenade (`8c838ebd-4939-4913-98a5-4f85825bf7d2`) | has_baby_changing, is_gender_neutral, requires_radar_key |
| 2cc4a8be56b4123f4c6b9cdf | Twickenham (`1a86877d-aec2-413c-8dd1-172c911c1948`) | latitude, longitude |
| 3596d85e074dbcee6eb47e42 | Isle of Man Sea Terminal (`43d0fa52-7ee2-453a-9400-5fefa07dc4e8`) | is_gender_neutral, requires_radar_key |
| 43119c8c4a6c8435eb0a98c7 | The Radlett Centre (`b38ccc30-9b2d-4d98-be93-52b7597e7469`) | has_baby_changing |
| 435c5eb4425b1f4197fdc415 | Wyllyotts Centre (`f746e2c4-3684-46f5-bb12-7b8206f19dbf`) | is_accessible, name |
| 439082c9b8bdf249c7799223 | Unnamed Toilet (`4cddc62f-71e0-4106-a1aa-13080a6a2934`) | is_accessible, is_gender_neutral, name, requires_radar_key |
| 47931cc3659d98b3ff90623d | Community Shop, Leeming Road (`a4c31707-e414-454c-addd-e8e4bf34c6b7`) | has_baby_changing, is_accessible, name, opening_hours, requires_radar_key |
| 5577f4ba2cf8063eb3250cce | Peel Breakwater (`cef8cd94-4722-4a0a-af99-d41d89162eaa`) | has_baby_changing, is_accessible, is_gender_neutral, requires_radar_key |
| 59908a2a56693539d819a451 | Canada Place - Mall, Level -1 (by Vodafone & Tian Tian Market) (`f0beb033-f4e7-4911-8c99-e0b15a15da2e`) | is_gender_neutral, name, opening_hours, requires_radar_key |
| 6546ab62101dcc2b657eedcc | Unnamed Toilet (`9f63fb9b-e2c5-4e61-98fb-120288db3764`) | name |
| 6edfb3b672f93d881c971075 | Ealing Broadway station (`0263f629-ce2e-415d-9a04-8ca326a98224`) | name, requires_radar_key |
| 717915db1407696a7aeca883 | Westfield London (`5d9e20fd-4e64-417e-9942-11472e59c715`) | is_accessible, is_gender_neutral, name, opening_hours, requires_radar_key |
| 72d4de0ff7f5180a8c1ac83d | Unnamed Toilet (`88e5418e-2dbd-454e-9c6f-af53c5e45780`) | has_baby_changing, is_accessible, is_gender_neutral, name, opening_hours, requires_radar_key |
| 81b56dd4b43119b1923c711c | KFC (`52908cd1-821c-40b4-a759-cae3072348fa`) | latitude, longitude |
| 85b55c1bf2609e112e0dfb0f | Glasgow Queen Street - Accessible Toilet (`41bb7d76-9416-4e46-a065-7a51c9735d0e`) | is_free |
| 892d3b2712e46852deb18efa | Inverleith park public toilet (`cfa1b9d0-8976-4d41-8cc3-2150a35252a2`) | has_baby_changing, is_gender_neutral, latitude, longitude |
| 932cba5c4208d78738047baa | Victoria Park (`ca87bd4e-b6fc-458b-81fd-011e126b7604`) | opening_hours |
| 99d0772ee2a69460b4071fc1 | Whitefriars (`8362daeb-22d9-43aa-817e-d08e3b1c741f`) | latitude, longitude |
| a715e37cd85cefda2cf7488f | The Wellington pub (`0dab87d1-fc22-4681-9bb9-261592d5c124`) | has_baby_changing, is_accessible, opening_hours, requires_radar_key |
| acb5bd8c054de53ee570635e | Greenwich (`0ee69f7f-940d-44da-b53d-aaea3885f262`) | is_accessible, is_gender_neutral, latitude, longitude, name, opening_hours |
| bd1a4cf729701d698457c96a | The Admiral Byng (`46fccd66-378c-47dc-91d6-16b33b36b2fe`) | has_baby_changing, is_accessible, name, opening_hours, requires_radar_key |
| c1ee470be276e3668604a6c4 | Kelvingrove Park (`94a84cb4-5ba9-4b2d-8cec-ada6b6aac50c`) | latitude, longitude, opening_hours |
| c4cb8ce171d428c6df643021 | Unnamed Toilet (`24bbdcc9-8bef-4565-a628-40dcc076dbf6`) | name |
| c5f65b256609c21ce0b3d170 | IKEA Glasgow (`7c5bbff3-1cfa-4d3e-916f-c89d12ff584a`) | is_accessible, is_gender_neutral, latitude, longitude |
| ce574c14a011cf31129647bd | The Centre/Salisbury Street (`14be9cfa-9925-4690-aa9e-95f984971dcb`) | is_accessible, is_gender_neutral, latitude, longitude, name, opening_hours |
| ce9db1854310c73d5d981099 | The Red Lion Pub (`e268da6e-7717-480b-8e73-cce1829e23c7`) | has_baby_changing, is_accessible, name, opening_hours, requires_radar_key |
| d07b48635f4c6704deb97183 | The Three Crowns (`1952126a-2910-43e6-a3b9-0b3a6cca0030`) | has_baby_changing, name, opening_hours, requires_radar_key |
| d5a6b67cdf6be9b5a7d122d8 | Cabot Place - Mall, Level -1 (by Flip Out & Leon) (`f73a3e6e-5420-4090-b7ed-2fa49c17d329`) | has_baby_changing, name, opening_hours |
| d6a814c2f04e92c2cc621951 | Westfield (`6067c02c-993c-426c-b0ea-100b11b658df`) | has_baby_changing, name, requires_radar_key |
| d92d50344bbe4bc65a6535ff | Lincoln's Inn Field Public Toilets (`4aab824e-b0ed-4722-a414-7bd94df34b77`) | name |
| f0f4b839449d3f093fcd40cb | Mayfair Library (`7b7c91a5-febf-4999-9cc6-cb94b81ab99c`) | has_baby_changing |
| f3045f53a3336236fe5c2fae | Sainsbury's Enfield Highlands (`c996e8a5-2040-494c-b5aa-48a3e69ce56f`) | opening_hours |
| fd83a87fa4acc5f1915ecad9 | Turnpike Lane Bus Station (`a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23`) | has_baby_changing, is_accessible, is_gender_neutral, requires_radar_key |
| ff407279699cc7ce345217e5 | Montrose Seafront (`d8359adb-bb85-4335-8473-f3e1f72d7a8d`) | opening_hours |

Coordinate movement and name/amenity/opening-hours detail are in the JSON artifact for every changed record.

## Quality warnings

- `2,746` records carry at least one warning.
- Warning counts: `{'missing source name': 2682, 'opening_times present but not a usable seven-day time array': 64}`
- Warning/match decisions: `{'missing source name': {'EXACT_SOURCE_ID': 2608, 'INVALID_SOURCE_RECORD': 74}, 'opening_times present but not a usable seven-day time array': {'EXACT_SOURCE_ID': 64}}`
- Missing names on exact-linked records do not break identity; they block name enrichment. Missing names without an exact source link block new-facility creation.
- Malformed opening times limit only hours enrichment; they do not automatically invalidate an exact-linked facility.

## Provenance and proposed policy

- Provenance observation: `{'baseline_non_empty_records': 10922, 'observed_field_counts': {'access_notes': 7202, 'is_gender_neutral': 3888, 'is_family_friendly': 2765, 'is_24h': 984, 'price_note': 1315, 'has_staff_nearby': 4534, 'last_verified_at': 2219, 'is_single_occupancy': 101}, 'observed_provenance_sources': {'Toilet Map UK': 23008}, 'verification_status_counts': {'source_imported': 15584}, 'observation': 'The snapshot shows source_imported verification status and Toilet Map UK provenance; no community-confirmed or staff-verified provenance marker was observed in the captured schema values.'}`
- Exact source IDs remain authoritative for identity.
- Unknown-to-known scalar values may be candidates for future `AUTO_ENRICH` only where no stronger provenance exists.
- Conflicts, coordinates, names, opening hours, source-ID churn, absent upstream records, and new-facility identity require review.
- No field value, source link, publication status, or production scope was changed.

The complete future mutation proposal is in `TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json`; it is a plan only and has no executable apply path.
