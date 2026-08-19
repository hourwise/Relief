# Toilet Map Refresh 2A existing-facility decisions

> Proposed, read-only preparation. Apply 2A is not authorized and was not executed.

- Source version: `2026-08-18T01:00:00+00:00`
- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Existing-facility operations assessed: `132`
- Remaining review cases assessed: `110`
- Canonical mutations: `0`
- Production mutations: `0`

## Decisions

| Decision | Count | Treatment |
|---|---:|---|
| `APPLY_SOURCE` | 22 | Eligible for a future guarded Apply 2A preflight |
| `KEEP_CANONICAL` | 98 | Preserve the current accepted canonical value |
| `PROTECTED` | 2 | Preserve because current provenance is present |
| `DEFER_EXTERNAL_VERIFICATION` | 10 | Exclude until independent current-hours evidence exists |
| `QUARANTINE` | 0 | No execution candidate; none in this bounded set |

## Decision policy

- The 22 `SAFE_BOOLEAN_ENRICHMENT` records are `APPLY_SOURCE` only because they have an exact source record ID, an explicit boolean, an unknown canonical value, and no current field provenance.
- The 98 unprotected `SOURCE_CANONICAL_CONFLICT` records are `KEEP_CANONICAL`. An exact source link alone does not establish that a fresh source value should overwrite an accepted non-null canonical value.
- The 2 source conflicts with existing Toilet Map provenance are `PROTECTED`; the package does not weaken or replace that provenance.
- The 10 `open_hours` enrichments are `DEFER_EXTERNAL_VERIFICATION`. Hours are material and affect urgent search behaviour; the source snapshot alone is not independent current verification.

## Case register

| Operation | Facility | Field | Before | Proposed source value | Decision |
|---|---|---|---|---|---|
| `TM2-0045c5c6880a297bc03b` | `94a84cb4-5ba9-4b2d-8cec-ada6b6aac50c` | `latitude` | `55.869895` | `55.87075389` | `KEEP_CANONICAL` |
| `TM2-03765ba0e1eadc41fb1c` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `open_hours` | `null` | `{"monday":{"open":"06:00","close":"19:00"},"tuesday":{"open":"06:00","close":"19:00"},"wednesday":{"open":"06:00","close":"19:00"},"thursday":{"open":"06:00","close":"19:00"},"friday":{"open":"06:00","close":"19:00"},"saturday":{"open":"06:00","close":"19:00"},"sunday":{"open":"07:30","close":"18:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-0709324cc1f5d30e1e2a` | `5b0f54bf-48ce-45b0-a1fb-47eb7f55e1de` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-07e390b5dd02b78219a3` | `ca87bd4e-b6fc-458b-81fd-011e126b7604` | `open_hours` | `{"monday":{"open":"10:00","close":"19:00"},"tuesday":{"open":"10:00","close":"19:00"},"wednesday":{"open":"10:00","close":"19:00"},"thursday":{"open":"10:00","close":"19:00"},"friday":{"open":"10:00","close":"19:00"},"saturday":{"open":"10:00","close":"19:00"},"sunday":{"open":"10:00","close":"19:00"}}` | `{"monday":{"open":"10:00","close":"16:30"},"tuesday":{"open":"10:00","close":"16:30"},"wednesday":{"open":"10:00","close":"16:30"},"thursday":{"open":"10:00","close":"16:30"},"friday":{"open":"10:00","close":"16:30"},"saturday":{"open":"10:00","close":"16:30"},"sunday":{"open":"10:00","close":"16:30"}}` | `KEEP_CANONICAL` |
| `TM2-0a057ea709521c89385b` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `name` | `"Unnamed Toilet"` | `"Market Square Toliets"` | `KEEP_CANONICAL` |
| `TM2-0b4c149e192636b2cb35` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `open_hours` | `null` | `{"monday":{"open":"09:00","close":"16:00"},"tuesday":{"open":"09:00","close":"16:00"},"wednesday":{"open":"09:00","close":"16:00"},"thursday":{"open":"09:00","close":"16:00"},"friday":{"open":"09:00","close":"16:00"},"saturday":{"open":"09:00","close":"16:00"},"sunday":{"open":"09:00","close":"16:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-0d899dcabc835438b8b8` | `e268da6e-7717-480b-8e73-cce1829e23c7` | `open_hours` | `{"monday":{"open":"09:00","close":"17:00"},"tuesday":{"open":"09:00","close":"17:00"},"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"},"saturday":{"open":"09:00","close":"17:00"},"sunday":{"open":"09:00","close":"17:00"}}` | `{"monday":{"open":"12:00","close":"23:00"},"tuesday":{"open":"11:00","close":"23:00"},"wednesday":{"open":"11:00","close":"23:00"},"thursday":{"open":"11:00","close":"23:00"},"friday":{"open":"11:00","close":"00:00"},"saturday":{"open":"11:00","close":"00:00"},"sunday":{"open":"12:00","close":"23:00"}}` | `KEEP_CANONICAL` |
| `TM2-0d9fc3a97ed11c5881ce` | `e268da6e-7717-480b-8e73-cce1829e23c7` | `name` | `"The Red Lion Pub"` | `"The Red Lion PH"` | `KEEP_CANONICAL` |
| `TM2-0ec4f7590514792cb7f4` | `5f131505-7a72-447c-a147-d452956a246f` | `latitude` | `55.070133` | `55.069756889` | `KEEP_CANONICAL` |
| `TM2-1177a4c656db7c2e7fd7` | `6edf994d-aa97-4243-aaa6-3a11ee844328` | `is_free` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-12dc9d849ad3d63b2e31` | `0fe9908b-bfa9-4bea-a77c-9c2cb5e2429d` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-142598287c0d610629ed` | `f746e2c4-3684-46f5-bb12-7b8206f19dbf` | `name` | `"Wyllyotts Centre"` | `"The Wyllyotts Centre"` | `KEEP_CANONICAL` |
| `TM2-156d2b1b74ae196ac630` | `7245c864-3c4d-4951-a2d3-0aa476b27e2e` | `has_baby_changing` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-1574177193fab1041a2c` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `open_hours` | `{"monday":{"open":"00:00","close":"00:00"},"tuesday":{"open":"00:00","close":"00:00"},"wednesday":{"open":"00:00","close":"00:00"},"thursday":{"open":"00:00","close":"00:00"},"friday":{"open":"00:00","close":"00:00"},"saturday":{"open":"00:00","close":"00:00"},"sunday":{"open":"00:00","close":"00:00"}}` | `{"monday":{"open":"08:00","close":"17:00"},"tuesday":{"open":"08:00","close":"17:00"},"wednesday":{"open":"08:00","close":"17:00"},"thursday":{"open":"08:00","close":"17:00"},"friday":{"open":"08:00","close":"17:00"},"saturday":{"open":"08:00","close":"17:00"},"sunday":{"open":"10:00","close":"16:00"}}` | `KEEP_CANONICAL` |
| `TM2-1748c3a38ee0860ef256` | `3c32648e-ddcc-4532-ae09-40ebce5b6bb5` | `longitude` | `-3.616229` | `-3.58250748` | `KEEP_CANONICAL` |
| `TM2-1ea9b3e6727b73b0ae40` | `f73a3e6e-5420-4090-b7ed-2fa49c17d329` | `name` | `"Cabot Place - Mall, Level -1 (by Flip Out & Leon)"` | `"Cabot Place - Mall, Level -1 (next to Flip Out, Buns From Home, Boss)"` | `KEEP_CANONICAL` |
| `TM2-224f5eece17c3b8fc608` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `is_gender_neutral` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-22f51c372a6d495f8e95` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-23688b2746dea8c27cf7` | `f0beb033-f4e7-4911-8c99-e0b15a15da2e` | `name` | `"Canada Place - Mall, Level -1 (by Vodafone & Tian Tian Market)"` | `"Canada Place - Mall, Level -1 (underground level -1) (opposite Robert Dyas)"` | `KEEP_CANONICAL` |
| `TM2-23745a7790b19204fc22` | `7c5bbff3-1cfa-4d3e-916f-c89d12ff584a` | `longitude` | `-4.359545` | `-4.359358748` | `KEEP_CANONICAL` |
| `TM2-238856aeee9ce2a57485` | `5d9e20fd-4e64-417e-9942-11472e59c715` | `name` | `"Westfield London"` | `"Westfield London (food court, upper level)"` | `KEEP_CANONICAL` |
| `TM2-25547fd9ce925a33c9ed` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-297866cb1716901f8096` | `3e9835c4-bc8e-4cc0-bc2e-c604945a1fe8` | `is_free` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-2983283c0606f603d866` | `0263f629-ce2e-415d-9a04-8ca326a98224` | `name` | `"Ealing Broadway station"` | `"Ealing Broadway station (inside paid area)"` | `KEEP_CANONICAL` |
| `TM2-2a8541ff364e010d98f9` | `e268da6e-7717-480b-8e73-cce1829e23c7` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-2bbc9bc38bcf52920658` | `3c32648e-ddcc-4532-ae09-40ebce5b6bb5` | `latitude` | `55.069018` | `55.075334899` | `KEEP_CANONICAL` |
| `TM2-2dc0ce9d6beeefb641ca` | `24bbdcc9-8bef-4565-a628-40dcc076dbf6` | `name` | `"Unnamed Toilet"` | `"Maytree Rd Public Toilet"` | `KEEP_CANONICAL` |
| `TM2-2e3a67f0b62ba7dc22fb` | `f73a3e6e-5420-4090-b7ed-2fa49c17d329` | `has_baby_changing` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-2f7af890c7d285b30d1b` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `name` | `"The Centre/Salisbury Street"` | `"Central Car Park Toilets"` | `KEEP_CANONICAL` |
| `TM2-32720fba00c13d8aa8f0` | `46fccd66-378c-47dc-91d6-16b33b36b2fe` | `name` | `"The Admiral Byng"` | `"The Admiral Byng PH"` | `KEEP_CANONICAL` |
| `TM2-32f76ff5135ae5062244` | `6edf994d-aa97-4243-aaa6-3a11ee844328` | `latitude` | `51.881851` | `51.881791154` | `KEEP_CANONICAL` |
| `TM2-35ee2f70b076427b851a` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `open_hours` | `null` | `{"monday":{"open":"07:30","close":"18:00"},"tuesday":{"open":"07:30","close":"18:00"},"wednesday":{"open":"07:30","close":"18:00"},"thursday":{"open":"07:30","close":"18:00"},"friday":{"open":"07:30","close":"18:00"},"saturday":{"open":"07:30","close":"18:00"},"sunday":{"open":"08:00","close":"18:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-3a32d4626c6749c7b25f` | `8362daeb-22d9-43aa-817e-d08e3b1c741f` | `latitude` | `54.06965` | `54.049644896` | `KEEP_CANONICAL` |
| `TM2-3a9f6996ac955caa5896` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-3b72d75647e1c9a69e2e` | `d8359adb-bb85-4335-8473-f3e1f72d7a8d` | `open_hours` | `null` | `{"monday":{"open":"10:00","close":"19:00"},"tuesday":{"open":"10:00","close":"19:00"},"wednesday":{"open":"10:00","close":"19:00"},"thursday":{"open":"10:00","close":"19:00"},"friday":{"open":"10:00","close":"19:00"},"saturday":{"open":"10:00","close":"19:00"},"sunday":{"open":"10:00","close":"19:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-3e2431f9f9c3422e6501` | `7213db1f-fac9-4cec-8c9b-83b23336c7ce` | `open_hours` | `null` | `{"monday":{"open":"09:00","close":"22:00"},"tuesday":{"open":"09:00","close":"22:00"},"wednesday":{"open":"09:00","close":"22:00"},"thursday":{"open":"09:00","close":"22:00"},"friday":{"open":"09:00","close":"22:00"},"saturday":{"open":"09:00","close":"22:00"},"sunday":{"open":"09:00","close":"22:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-42ef9b74c7f12e4f3aca` | `7c5bbff3-1cfa-4d3e-916f-c89d12ff584a` | `latitude` | `55.869328` | `55.869643621` | `KEEP_CANONICAL` |
| `TM2-47a6b52e466aafc9fca7` | `7245c864-3c4d-4951-a2d3-0aa476b27e2e` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-4a9a15a1920b4d9a5247` | `493207a8-cf6c-4d8d-ba32-614983baa427` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-4b8e8cff81a0428c64b1` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-4c2a22a27905ccdf3d61` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `latitude` | `51.171909` | `51.172384567` | `KEEP_CANONICAL` |
| `TM2-4caccceaa574a280ab65` | `8362daeb-22d9-43aa-817e-d08e3b1c741f` | `longitude` | `-2.277779` | `-2.281916142` | `KEEP_CANONICAL` |
| `TM2-508b456fef1754e5b13f` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `has_baby_changing` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-5492972332c6f04d8ce4` | `cef8cd94-4722-4a0a-af99-d41d89162eaa` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-559be8b303993c4faaa3` | `f746e2c4-3684-46f5-bb12-7b8206f19dbf` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-5852ee4ab2157a8508a9` | `f0beb033-f4e7-4911-8c99-e0b15a15da2e` | `open_hours` | `{"monday":{"open":"10:00","close":"20:00"},"tuesday":{"open":"10:00","close":"20:00"},"wednesday":{"open":"10:00","close":"20:00"},"thursday":{"open":"10:00","close":"20:00"},"friday":{"open":"10:00","close":"20:00"},"saturday":{"open":"10:00","close":"19:00"},"sunday":{"open":"12:00","close":"18:00"}}` | `{"monday":{"open":"00:00","close":"00:00"},"tuesday":{"open":"00:00","close":"00:00"},"wednesday":{"open":"00:00","close":"00:00"},"thursday":{"open":"00:00","close":"00:00"},"friday":{"open":"00:00","close":"00:00"},"saturday":{"open":"00:00","close":"00:00"},"sunday":{"open":"00:00","close":"00:00"}}` | `KEEP_CANONICAL` |
| `TM2-5bbdc4996e9bf08e60c0` | `6067c02c-993c-426c-b0ea-100b11b658df` | `name` | `"Westfield"` | `"Westfield (next to Marks & Spencer lower level)"` | `KEEP_CANONICAL` |
| `TM2-5dfb13482b76c9cffd2d` | `5d9e20fd-4e64-417e-9942-11472e59c715` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-5e8c0f38956f20c66ae5` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `requires_radar_key` | `true` | `false` | `KEEP_CANONICAL` |
| `TM2-6044b4db3a4e45ada8d6` | `5d9e20fd-4e64-417e-9942-11472e59c715` | `open_hours` | `{"monday":{"open":"09:00","close":"17:00"},"tuesday":{"open":"09:00","close":"17:00"},"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"},"saturday":{"open":"09:00","close":"17:00"},"sunday":{"open":"09:00","close":"17:00"}}` | `{"monday":{"open":"09:00","close":"21:00"},"tuesday":{"open":"09:00","close":"21:00"},"wednesday":{"open":"09:00","close":"21:00"},"thursday":{"open":"09:00","close":"21:00"},"friday":{"open":"09:00","close":"21:00"},"saturday":{"open":"09:00","close":"21:00"},"sunday":{"open":"09:00","close":"21:00"}}` | `KEEP_CANONICAL` |
| `TM2-609b3185233e1adec829` | `f82adba4-6870-457e-ba86-c412817ef381` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-627f4b2c3dca3e45adda` | `0dab87d1-fc22-4681-9bb9-261592d5c124` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-6662d21eeb008d93e54c` | `9bef8360-2c99-4111-aa5e-1dbc2b061e46` | `requires_radar_key` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-66799d0095a63be2186b` | `94a84cb4-5ba9-4b2d-8cec-ada6b6aac50c` | `open_hours` | `{"monday":{"open":"10:00","close":"19:00"},"tuesday":{"open":"10:00","close":"19:00"},"wednesday":{"open":"10:00","close":"19:00"},"thursday":{"open":"10:00","close":"19:00"},"friday":{"open":"10:00","close":"19:00"},"saturday":{"open":"10:00","close":"19:00"},"sunday":{"open":"10:00","close":"19:00"}}` | `{"monday":{"open":"10:00","close":"16:30"},"tuesday":{"open":"10:00","close":"16:30"},"wednesday":{"open":"10:00","close":"16:30"},"thursday":{"open":"10:00","close":"16:30"},"friday":{"open":"10:00","close":"16:30"},"saturday":{"open":"10:00","close":"16:30"},"sunday":{"open":"10:00","close":"16:30"}}` | `KEEP_CANONICAL` |
| `TM2-6812f44260e48e26ca3d` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `name` | `"Unnamed Toilet"` | `"LEVEN BEACH"` | `KEEP_CANONICAL` |
| `TM2-68a58feec0e6d7216f8b` | `6067c02c-993c-426c-b0ea-100b11b658df` | `requires_radar_key` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-68d13dffec6ccc71ad04` | `5f131505-7a72-447c-a147-d452956a246f` | `longitude` | `-3.588618` | `-3.584510007` | `KEEP_CANONICAL` |
| `TM2-69df9bbf1853e77328c9` | `3e9835c4-bc8e-4cc0-bc2e-c604945a1fe8` | `longitude` | `-4.817156` | `-4.816878319` | `KEEP_CANONICAL` |
| `TM2-6d643cc4b2a05e3eb597` | `f82adba4-6870-457e-ba86-c412817ef381` | `requires_radar_key` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-7112ab31c6f1f7d6629a` | `f82adba4-6870-457e-ba86-c412817ef381` | `name` | `"Abbey Wood Station"` | `"Abbey Wood Station (paid area)"` | `KEEP_CANONICAL` |
| `TM2-725001b2fe017f49a3b4` | `bbac6890-1199-449d-801d-1672d046e857` | `is_gender_neutral` | `false` | `true` | `PROTECTED` |
| `TM2-72f8fbafcf0f6f728609` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `name` | `"Greenwich"` | `"Greenwich National Rail station"` | `KEEP_CANONICAL` |
| `TM2-742c0959254c85a2c407` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-74da1ed34b7360bb3b0f` | `52908cd1-821c-40b4-a759-cae3072348fa` | `longitude` | `-1.014133` | `-1.01344925` | `KEEP_CANONICAL` |
| `TM2-78f5e19a43d160d612fa` | `f9c09fa5-a8a7-478b-8bc9-d94512018e8f` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-7c2ecb8cd911026d8297` | `a162ba22-9aa8-49b5-aa64-b2618e5a12fe` | `is_gender_neutral` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-7dfe3d413cb477c89bf9` | `5b0f54bf-48ce-45b0-a1fb-47eb7f55e1de` | `requires_radar_key` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-7e983e72d012ee996519` | `0fe9908b-bfa9-4bea-a77c-9c2cb5e2429d` | `requires_radar_key` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-8a0d3d8a51d4e0eb4ac8` | `4a6cff49-1286-47e2-8c0e-9678638e08b6` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-8bc6451d485901d982d5` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-902daa80e4cea04b30a3` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `has_baby_changing` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-91df144634b60c864a7a` | `a162ba22-9aa8-49b5-aa64-b2618e5a12fe` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-94387988b07a821c743c` | `9f63fb9b-e2c5-4e61-98fb-120288db3764` | `name` | `"Unnamed Toilet"` | `"Hartington Station"` | `KEEP_CANONICAL` |
| `TM2-96225cd5c7b6394fcded` | `3a1e0c57-9e74-4f75-9fda-7c033723cd01` | `is_free` | `true` | `false` | `KEEP_CANONICAL` |
| `TM2-98952f06ae7145f89f0e` | `3e9835c4-bc8e-4cc0-bc2e-c604945a1fe8` | `name` | `"Shore Street"` | `"Shore street"` | `KEEP_CANONICAL` |
| `TM2-996da0fc14949cc79b9e` | `cfa1b9d0-8976-4d41-8cc3-2150a35252a2` | `longitude` | `-3.213911` | `-3.214236735` | `KEEP_CANONICAL` |
| `TM2-9d0ea5a5d2713406a537` | `0fe9908b-bfa9-4bea-a77c-9c2cb5e2429d` | `open_hours` | `null` | `{"monday":{"open":"06:00","close":"00:00"},"tuesday":{"open":"06:00","close":"00:00"},"wednesday":{"open":"06:00","close":"00:00"},"thursday":{"open":"06:00","close":"00:00"},"friday":{"open":"06:00","close":"00:00"},"saturday":{"open":"00:00","close":"00:00"},"sunday":{"open":"07:00","close":"23:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-9e0590c067b4c0bd3d67` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `name` | `"Unnamed Toilet"` | `"Brandwood End Cemetery"` | `KEEP_CANONICAL` |
| `TM2-a1ff7407228623f4f54d` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `is_free` | `true` | `false` | `KEEP_CANONICAL` |
| `TM2-a47f1089b689f65ce021` | `6edf994d-aa97-4243-aaa6-3a11ee844328` | `longitude` | `-2.051525` | `-2.051718414` | `KEEP_CANONICAL` |
| `TM2-a56ef8a55ec37d328976` | `4a6cff49-1286-47e2-8c0e-9678638e08b6` | `longitude` | `-4.477988` | `-4.477962242` | `KEEP_CANONICAL` |
| `TM2-a5e8a88d4f501cc3ba02` | `1a86877d-aec2-413c-8dd1-172c911c1948` | `latitude` | `51.450377` | `51.450274216` | `KEEP_CANONICAL` |
| `TM2-aa3552f977d83f280960` | `f0beb033-f4e7-4911-8c99-e0b15a15da2e` | `is_gender_neutral` | `true` | `false` | `PROTECTED` |
| `TM2-abb13e538d525f8b3e50` | `9bef8360-2c99-4111-aa5e-1dbc2b061e46` | `longitude` | `-3.616229` | `-3.2487343` | `KEEP_CANONICAL` |
| `TM2-ac6b1308c0bfeee58b80` | `f0beb033-f4e7-4911-8c99-e0b15a15da2e` | `requires_radar_key` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-ac6ef76cc481c6d8ecc6` | `ba77f1fd-b878-4347-beeb-26f5a8a38291` | `open_hours` | `null` | `{"monday":{"open":"09:00","close":"22:00"},"tuesday":{"open":"09:00","close":"22:00"},"wednesday":{"open":"09:00","close":"22:00"},"thursday":{"open":"09:00","close":"22:00"},"friday":{"open":"09:00","close":"22:00"},"saturday":{"open":"09:00","close":"22:00"},"sunday":{"open":"09:00","close":"22:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-adfc1e1af63003748c8e` | `4cddc62f-71e0-4106-a1aa-13080a6a2934` | `name` | `"Unnamed Toilet"` | `"Shore Road"` | `KEEP_CANONICAL` |
| `TM2-ae3ef93a73d66f45dc96` | `f9c09fa5-a8a7-478b-8bc9-d94512018e8f` | `open_hours` | `null` | `{"monday":{"open":"06:55","close":"13:25"},"tuesday":{"open":"06:55","close":"13:25"},"wednesday":{"open":"06:55","close":"13:25"},"thursday":{"open":"06:55","close":"13:25"},"friday":{"open":"06:55","close":"13:25"},"saturday":{"open":"08:00","close":"14:00"},"sunday":{"open":"08:55","close":"16:25"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-b160a3fc438d215ef0f2` | `f73a3e6e-5420-4090-b7ed-2fa49c17d329` | `open_hours` | `{"monday":{"open":"10:00","close":"20:00"},"tuesday":{"open":"10:00","close":"20:00"},"wednesday":{"open":"10:00","close":"20:00"},"thursday":{"open":"10:00","close":"20:00"},"friday":{"open":"10:00","close":"20:00"},"saturday":{"open":"10:00","close":"19:00"},"sunday":{"open":"12:00","close":"18:00"}}` | `{"monday":{"open":"00:00","close":"00:00"},"tuesday":{"open":"00:00","close":"00:00"},"wednesday":{"open":"00:00","close":"00:00"},"thursday":{"open":"00:00","close":"00:00"},"friday":{"open":"00:00","close":"00:00"},"saturday":{"open":"00:00","close":"00:00"},"sunday":{"open":"00:00","close":"00:00"}}` | `KEEP_CANONICAL` |
| `TM2-b28a50d2bcb476c86fb2` | `46fccd66-378c-47dc-91d6-16b33b36b2fe` | `open_hours` | `{"monday":{"open":"09:00","close":"17:00"},"tuesday":{"open":"09:00","close":"17:00"},"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"},"saturday":{"open":"09:00","close":"17:00"},"sunday":{"open":"09:00","close":"17:00"}}` | `{"monday":{"open":"08:00","close":"00:00"},"tuesday":{"open":"08:00","close":"00:00"},"wednesday":{"open":"08:00","close":"00:00"},"thursday":{"open":"08:00","close":"00:00"},"friday":{"open":"08:00","close":"00:30"},"saturday":{"open":"08:00","close":"23:30"},"sunday":{"open":"08:00","close":"23:00"}}` | `KEEP_CANONICAL` |
| `TM2-b2aece719d7b2c94a8a9` | `a4c31707-e414-454c-addd-e8e4bf34c6b7` | `name` | `"Community Shop, Leeming Road"` | `"Communities 1st Community Hub"` | `KEEP_CANONICAL` |
| `TM2-b4693d526db5f1ef790e` | `5d0c04bf-0f70-4737-99eb-751a35a9a7ba` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-b474a1baae7d8eb2f773` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `longitude` | `-0.01421` | `-0.013354677` | `KEEP_CANONICAL` |
| `TM2-b6b17ff836fd0fc0e096` | `1952126a-2910-43e6-a3b9-0b3a6cca0030` | `open_hours` | `{"monday":{"open":"09:00","close":"17:00"},"tuesday":{"open":"09:00","close":"17:00"},"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"},"saturday":{"open":"09:00","close":"17:00"},"sunday":{"open":"09:00","close":"17:00"}}` | `{"monday":{"open":"12:00","close":"23:00"},"tuesday":{"open":"12:00","close":"23:00"},"wednesday":{"open":"12:00","close":"23:00"},"thursday":{"open":"12:00","close":"23:00"},"friday":{"open":"12:00","close":"00:00"},"saturday":{"open":"12:00","close":"00:00"},"sunday":{"open":"12:00","close":"23:00"}}` | `KEEP_CANONICAL` |
| `TM2-b72da58b04b703f44b6a` | `52908cd1-821c-40b4-a759-cae3072348fa` | `latitude` | `51.462109` | `51.461974385` | `KEEP_CANONICAL` |
| `TM2-b80f353bd3525d5d3568` | `9bef8360-2c99-4111-aa5e-1dbc2b061e46` | `latitude` | `55.069018` | `54.98509591` | `KEEP_CANONICAL` |
| `TM2-b9a2a8fdf3dda94672d7` | `1952126a-2910-43e6-a3b9-0b3a6cca0030` | `name` | `"The Three Crowns"` | `"The Three Crowns PH"` | `KEEP_CANONICAL` |
| `TM2-bd76553b011896199bee` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `requires_radar_key` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-bfcabb1472b6792ece0c` | `a4c31707-e414-454c-addd-e8e4bf34c6b7` | `open_hours` | `{"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"}}` | `{"wednesday":{"open":"09:00","close":"15:00"},"thursday":{"open":"09:00","close":"15:00"},"friday":{"open":"09:00","close":"15:00"}}` | `KEEP_CANONICAL` |
| `TM2-c0d3b5b2a644a15f1215` | `1a86877d-aec2-413c-8dd1-172c911c1948` | `longitude` | `-0.32916` | `-0.329431593` | `KEEP_CANONICAL` |
| `TM2-c2e884f90f8fe13f0542` | `a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23` | `requires_radar_key` | `true` | `false` | `KEEP_CANONICAL` |
| `TM2-c42d4a457af10a5c115b` | `f82adba4-6870-457e-ba86-c412817ef381` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-c5445961cdb2e8c4ef66` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `requires_radar_key` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-c87dc5897e0707a7e60e` | `7245c864-3c4d-4951-a2d3-0aa476b27e2e` | `requires_radar_key` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-ca774b68cde042ce481a` | `ba77f1fd-b878-4347-beeb-26f5a8a38291` | `name` | `"Unnamed Toilet"` | `"Silverburn Shopping Centre 1"` | `KEEP_CANONICAL` |
| `TM2-cd86dfd9019d42edb4e3` | `94a84cb4-5ba9-4b2d-8cec-ada6b6aac50c` | `longitude` | `-4.28587` | `-4.285172224` | `KEEP_CANONICAL` |
| `TM2-cf5816a50ee50aadd66f` | `88d36e31-a1f9-4c3e-a639-b07c022839f8` | `open_hours` | `null` | `{"monday":{"open":"08:30","close":"16:00"},"tuesday":{"open":"08:30","close":"16:00"},"wednesday":{"open":"08:30","close":"16:00"},"thursday":{"open":"08:30","close":"16:00"},"friday":{"open":"08:30","close":"16:00"},"saturday":{"open":"08:30","close":"16:00"},"sunday":{"open":"08:30","close":"16:00"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-d29b30736df88b206772` | `ba77f1fd-b878-4347-beeb-26f5a8a38291` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-d5a24eb9bd6fd0ce9d0f` | `3e9835c4-bc8e-4cc0-bc2e-c604945a1fe8` | `latitude` | `55.96101` | `55.961051941` | `KEEP_CANONICAL` |
| `TM2-d77587138bf23295e32c` | `cf385907-c050-44d7-bd14-b5cb4be94a8e` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-da013e48856dd89ae918` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `longitude` | `-3.885528` | `-3.885560925` | `KEEP_CANONICAL` |
| `TM2-dbcf2b277f46afd58823` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-e418a8eb37c0d2bc5006` | `e0d843f6-931d-42fa-811f-54d333c1bff9` | `name` | `"Unnamed Toilet"` | `"Oakmere Park"` | `KEEP_CANONICAL` |
| `TM2-e5589798bd9ab2d578af` | `c996e8a5-2040-494c-b5aa-48a3e69ce56f` | `open_hours` | `{"monday":{"open":"09:00","close":"17:00"},"tuesday":{"open":"09:00","close":"17:00"},"wednesday":{"open":"09:00","close":"17:00"},"thursday":{"open":"09:00","close":"17:00"},"friday":{"open":"09:00","close":"17:00"},"saturday":{"open":"09:00","close":"17:00"},"sunday":{"open":"09:00","close":"17:00"}}` | `{"monday":{"open":"07:00","close":"21:00"},"tuesday":{"open":"07:00","close":"21:00"},"wednesday":{"open":"07:00","close":"21:00"},"thursday":{"open":"07:00","close":"21:00"},"friday":{"open":"07:00","close":"21:00"},"saturday":{"open":"07:00","close":"21:00"},"sunday":{"open":"11:00","close":"17:00"}}` | `KEEP_CANONICAL` |
| `TM2-e762e3a8084a4a6ee06d` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `longitude` | `-1.780365` | `-1.779567926` | `KEEP_CANONICAL` |
| `TM2-e9b5c27c95462ff4c6fd` | `4aab824e-b0ed-4722-a414-7bd94df34b77` | `name` | `"Lincoln's Inn Field Public Toilets"` | `"Lincoln's Inn Fields Public Toilets (closed for refurbishment until 16 September 2026)"` | `KEEP_CANONICAL` |
| `TM2-edfab1df4c6fe24a543e` | `5f08f49f-51db-44bc-b5b9-7fe140d109c3` | `requires_radar_key` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-ee3c5286a7d99541d5b4` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-ee7f75d8fa289225d05f` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `name` | `"Unnamed Toilet"` | `"Dolgellau Car Park"` | `KEEP_CANONICAL` |
| `TM2-ee821e4561b8cb35fb0a` | `0fe9908b-bfa9-4bea-a77c-9c2cb5e2429d` | `has_baby_changing` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-f0d64c57f2112db64587` | `f9c09fa5-a8a7-478b-8bc9-d94512018e8f` | `is_free` | `null` | `true` | `APPLY_SOURCE` |
| `TM2-f11bb355be80302f78a1` | `493207a8-cf6c-4d8d-ba32-614983baa427` | `requires_radar_key` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-f331361fb5a0c3272450` | `a4c31707-e414-454c-addd-e8e4bf34c6b7` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-f37b648ba818c7ccfd52` | `0fe9908b-bfa9-4bea-a77c-9c2cb5e2429d` | `name` | `"Bank Station (Cannon St Entrance)"` | `"Bank Station (London Underground) (Cannon Street entrance) (paid area)"` | `KEEP_CANONICAL` |
| `TM2-f407681ad3d42e8dc16d` | `0dab87d1-fc22-4681-9bb9-261592d5c124` | `open_hours` | `null` | `{"monday":{"open":"11:00","close":"23:00"},"tuesday":{"open":"11:00","close":"23:00"},"wednesday":{"open":"11:00","close":"23:00"},"thursday":{"open":"11:00","close":"23:00"},"friday":{"open":"11:00","close":"23:00"},"saturday":{"open":"11:00","close":"00:00"},"sunday":{"open":"12:00","close":"22:30"}}` | `DEFER_EXTERNAL_VERIFICATION` |
| `TM2-f7ff25177bbff8b042dd` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `latitude` | `51.477838` | `51.47809667` | `KEEP_CANONICAL` |
| `TM2-f8c1b9c603d4c408a08d` | `5b0f54bf-48ce-45b0-a1fb-47eb7f55e1de` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-f97e7e7b3de87c9fa459` | `c177c1d5-efa0-45c5-b36c-91aed5598d2a` | `has_baby_changing` | `null` | `false` | `APPLY_SOURCE` |
| `TM2-ff1f071a1533b75559c0` | `cfa1b9d0-8976-4d41-8cc3-2150a35252a2` | `latitude` | `55.964528` | `55.962364138` | `KEEP_CANONICAL` |
| `TM2-ff498263910227167753` | `46fccd66-378c-47dc-91d6-16b33b36b2fe` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-ff60d538cb803b280bc8` | `4cddc62f-71e0-4106-a1aa-13080a6a2934` | `is_accessible` | `false` | `true` | `KEEP_CANONICAL` |
| `TM2-ffeb7fe7d253a0f38c8d` | `5f131505-7a72-447c-a147-d452956a246f` | `open_hours` | `{"monday":{"open":"09:00","close":"20:00"},"tuesday":{"open":"09:00","close":"20:00"},"wednesday":{"open":"09:00","close":"20:00"},"thursday":{"open":"09:00","close":"20:00"},"friday":{"open":"09:00","close":"20:00"},"saturday":{"open":"09:00","close":"20:00"}}` | `{"monday":{"open":"08:00","close":"22:00"},"tuesday":{"open":"08:00","close":"22:00"},"wednesday":{"open":"08:00","close":"22:00"},"thursday":{"open":"08:00","close":"22:00"},"friday":{"open":"08:00","close":"22:00"},"saturday":{"open":"08:00","close":"22:00"}}` | `KEEP_CANONICAL` |
