# Toilet Map Refresh 2B new-facility decisions

> Proposed, read-only preparation. No new facility was inserted and Apply 2B execution is not authorized.

- Source version: `2026-08-18T01:00:00+00:00`
- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Candidates assessed: `42`
- Exact source links found in production preflight: `0` of `42`
- Canonical mutations: `0`
- Production mutations: `0`

## Decisions

| Decision | Count | Treatment |
|---|---:|---|
| `PREPARE_INSERT_CANDIDATE` | 36 | Include in a future guarded insert package; no execution authorization is implied |
| `DEFER_EXTERNAL_VERIFICATION` | 5 | Exclude until identity/collision evidence is resolved |
| `QUARANTINE` | 1 | Exclude because the source identity is invalid or unusable |

## Decision policy

- A candidate is prepared only when its frozen public source identity contains a usable name and coordinate, the production exact-source preflight found no existing source link, and no deterministic collision evidence was found.
- The three Refresh 2 collision candidates (Hemsby Beach Toilets, Burns Mall Toilets, and Tesco Extra) remain deferred because a nearby canonical facility requires identity verification before insertion.
- The two exact-name Becky’s Barn Cafe rows are deferred because they are 217.1 m apart within the same source batch; source identity must establish whether they are two toilets or one duplicated source record.
- The `Does not exist` row is quarantined as an invalid placeholder name. A nearby canonical Yates’s record reinforces that it cannot be treated as a new facility without human investigation.
- Neilston Train Station, Neilston Library, and Neilston Leisure Centre are retained as distinct candidates: their names are distinct and their nearest current canonical facility is 1.9–2.3 km away. This is not a substitute for the required execution-time recheck.

## Production boundary

- This package contains proposed future inserts only; it is not an executable migration or apply command.
- It contains no facility IDs, so it cannot target an existing facility for update or deletion.
- A future execution would require a separate owner approval, a fresh read-only preflight, duplicate/collision recheck, and an auditable transaction/postcheck.

## Case register

| Operation | Source record | Name | Town | Decision | Rule |
|---|---|---|---|---|---|
| `TM2-046d175b28808a47eaaa` | `232bc6a31fc2f51f403d077f` | Canary Wharf (Jubilee Line) underground station (ticket entrance area) (unpaid area) (accessible toilet only) | Tower Hamlets | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-078bb4dd79b3b3c3a61a` | `bc286db1008098ef3fcc5ac3` | Coffee#1 Derby | Derby | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-0e4a59faa04f75fa379c` | `6de34ddb3ac6668d98c2334c` | Becky's Barn Cafe | Shropshire | `DEFER_EXTERNAL_VERIFICATION` | `SOURCE_BATCH_DUPLICATE_CANDIDATE_REQUIRES_SOURCE_IDENTITY_VERIFICATION` |
| `TM2-1016ab43c0ec1482185b` | `059ffb72ce5bab427a2de7a1` | RSPB Lochwinnoch | Renfrewshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-1132855a3c36fe78c2c7` | `fc1cf7d0e3edb420148aad20` | Bushey Rose Garden | Hertsmere | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-11c5e038510aa366ec42` | `177c0eaa345c7ce7677eb13c` | Becky's Barn Cafe | Shropshire | `DEFER_EXTERNAL_VERIFICATION` | `SOURCE_BATCH_DUPLICATE_CANDIDATE_REQUIRES_SOURCE_IDENTITY_VERIFICATION` |
| `TM2-1c54e6e3b7cb4ee9d563` | `ce7f310c0293474778934cc5` | Westfield London (lower level, next to Läderach shop) | Hammersmith and Fulham | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-212b01fcac92dbddbec9` | `d6f5596b9d08edc4cfeac7df` | Weston-super-Mare Railway Station | North Somerset | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-2227fed43629d066e325` | `6e3587fd50aaf24da80ea357` | Precinct walk public toilet | South Kesteven | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-24ff0f24c85363e4b423` | `8f8624f23652e467aae5184c` | Dobbies | West Suffolk | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-250dbc4d2277f71259ef` | `53a780f6c6ee963bdd2c1c1e` | Club Oasis | Great Yarmouth | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-28e5c5baa669542e1e93` | `e7afff68c09835856392fee7` | Whirlies McDonald's | South Lanarkshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-3031cf5788b689e30668` | `857c4ddc685fa35c8a6eb0c1` | Lidl Tilehurst | Reading | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-3538ac5875917c1e6c39` | `f3638d10f57ada4c1cf16566` | Petrol and diesel filling Station | South Staffordshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-364b5b3793da4ac1c9dc` | `33aebf2ab67de1b196b4ca15` | Neilston Library | East Renfrewshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-37f7bd619e0124a94c5a` | `4d5844e4e99d8bf8ba9d7e11` | Neilston Leisure Centre | East Renfrewshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-46ed62f00d65a2022216` | `3b49d8f21b9a69ca0eb667ad` | McDonalds | Hertsmere | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-4ff0ea7c4ea81b364de9` | `fb968371c27222e3f758d8e0` | Silverburn Restaurant Concourse Toilets | Glasgow City | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-65d3356f0db58259f72d` | `88c551d0ff726ead4b2fb2ba` | Does not exist | Hounslow | `QUARANTINE` | `INVALID_PLACEHOLDER_OR_MISSING_FACILITY_NAME` |
| `TM2-747763915b2b81f7f6cb` | `1c7f7f431a450c0659bb4d18` | Neilston Train Station | East Renfrewshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-80ac1ebdc8ed3e5f922b` | `02760f05f626d67f29aabc09` | Armada Way Accessible Toilets | Plymouth | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-85c0723eff3e08198921` | `230fbaf1acae2242e54a0ad8` | Council House Entrance Lobby | Derby | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-8c15d16e979adee79d1b` | `a318d929c92290531ea29e1d` | Lidl Reading West | Reading | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-9545f33c0d5216087a68` | `de087518da62852cfb13962d` | Accessible Toilet @ Disability Equality (NW) Community Hub | Preston | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-98d67b4af6c09a6cc41f` | `80f7d5d63fa3acde2acc0e2b` | King George Park | Hertsmere | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-a56e67f1e2ae58757a3e` | `b77ab579ca2eedffc65cdcca` | Rubio’s | Brent | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-a841b3436208824bf19e` | `e700cdd4047203a94a6a9080` | Waitrose | East Hertfordshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-a8f6a27db083eabb5654` | `46da2d339d53dfbd632099f3` | Hemsby Beach Toilets | Great Yarmouth | `DEFER_EXTERNAL_VERIFICATION` | `CURRENT_CANONICAL_NEIGHBOUR_OR_COLLISION_REQUIRES_IDENTITY_VERIFICATION` |
| `TM2-aa20c5d23cab8f4cbbcd` | `319a320ae4671c38ef383f6f` | Birds Bakery Cafe | Charnwood | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-b2b1caad3813b4f5cbf4` | `1d9034f071dab8ee5ee5181f` | Exeter City Library | Exeter | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-b3525ca1ea3b6cfd90f2` | `f56fabed41bdd53b43154561` | Caffe Torta | Erewash | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-b5126a69f1b99f989aff` | `4090f92f66ab256d2938b037` | Marks and Spencer | West Oxfordshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-b51b3088dd1cfe5f930f` | `defc1a12a8026d061ec6c37f` | Manor Café | Hertsmere | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-ba9cd26634c260082ad4` | `7e4d881dc784d265df20994a` | Weston Museum | North Somerset | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-c1f3bc5a0ab1383f8c84` | `6ed2683ff5dbb5a31bafd6ff` | Burns Mall Toilets | East Ayrshire | `DEFER_EXTERNAL_VERIFICATION` | `CURRENT_CANONICAL_NEIGHBOUR_OR_COLLISION_REQUIRES_IDENTITY_VERIFICATION` |
| `TM2-cd448729df1f560728f0` | `14abe0d9023602979da37362` | Chill @ Chives Cafe | Derby | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-d0acc3bb09743e14d080` | `e5605b6c0df6875be110c199` | Tesco Extra | Welwyn Hatfield | `DEFER_EXTERNAL_VERIFICATION` | `CURRENT_CANONICAL_NEIGHBOUR_OR_COLLISION_REQUIRES_IDENTITY_VERIFICATION` |
| `TM2-d184848ddde09ce81b41` | `d4a0b0dfba033bbc5471d0b4` | Copper Cogs Bar and cafe | Erewash | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-ecd6c4b03379941d90c0` | `7cc79e2f00ccb6fed0aa3d9b` | Subway Maghull | Sefton | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-ef55d1714894becddeaf` | `615f57c3f055e295b30e927b` | Starbucks on Sauchiehall Street | Glasgow City | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-f0ebde1c1b6bf0e99b75` | `d4e39ccaa0d82f641d81a998` | Meopham Green Public Toilets | Gravesham | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
| `TM2-ff5b63deaf31a053e80f` | `48da5d2fccb3c30e827ab43b` | Methodist Church | East Hertfordshire | `PREPARE_INSERT_CANDIDATE` | `VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE` |
