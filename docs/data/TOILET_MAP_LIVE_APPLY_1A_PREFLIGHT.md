# Relief Apply Engine 1A Simulation

> SIMULATED_ONLY. This artifact was produced by GET-only live preflight and in-memory copies. No database transaction was opened.

## Frozen inputs

- Review commit: `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77`
- Approved plan SHA-256: `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45`
- Manifest SHA-256: `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0`
- Source snapshot checksum: `F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624`
- Supabase project: `bgwxrxkmyaihplaloely`
- Snapshot mode: **read-only Supabase REST GET**

## Scope and preflight

- Requested operations: **48**
- READY: **48**
- STALE / PRECONDITION_FAILED: **0**
- Counts by field: `{'has_baby_changing': 16, 'is_accessible': 2, 'is_free': 1, 'is_gender_neutral': 15, 'requires_radar_key': 14}`
- Failure counts: `{}`

The simulator accepted only exact source-ID linked, HIGH-confidence, null-to-boolean entries on the five-field Apply 1A allowlist. New facilities, absent upstream IDs, out-of-scope records, quarantine candidates, conflicts, names, coordinates, addresses, towns, postcodes, and opening-hours fields are excluded by code and do not have an execution path.

## Operation results

| Operation | Facility | Source ID | Field | Current | Proposed | Result | Hypothetical rows |
|---|---|---|---|---:|---:|---|---:|
| `A1A-c5dbe77c3c08ad19` | `0263f629-ce2e-415d-9a04-8ca326a98224` | `6edfb3b672f93d881c971075` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-942a34c2f2f43842` | `0dab87d1-fc22-4681-9bb9-261592d5c124` | `a715e37cd85cefda2cf7488f` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-131cef5192c07f27` | `0dab87d1-fc22-4681-9bb9-261592d5c124` | `a715e37cd85cefda2cf7488f` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-a710244c4057201b` | `0ee69f7f-940d-44da-b53d-aaea3885f262` | `acb5bd8c054de53ee570635e` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-fcd6a18b9db47cf2` | `14be9cfa-9925-4690-aa9e-95f984971dcb` | `ce574c14a011cf31129647bd` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-6e56d5fa754ed9d4` | `1952126a-2910-43e6-a3b9-0b3a6cca0030` | `d07b48635f4c6704deb97183` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-6b0cd475fe2068df` | `1952126a-2910-43e6-a3b9-0b3a6cca0030` | `d07b48635f4c6704deb97183` | `requires_radar_key` | `None` | `False` | `READY` | `1` |
| `A1A-85fa5a8044acc84a` | `41bb7d76-9416-4e46-a065-7a51c9735d0e` | `85b55c1bf2609e112e0dfb0f` | `is_free` | `None` | `True` | `READY` | `1` |
| `A1A-75321260fe546b96` | `43d0fa52-7ee2-453a-9400-5fefa07dc4e8` | `3596d85e074dbcee6eb47e42` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-03a30b1bd39c996f` | `43d0fa52-7ee2-453a-9400-5fefa07dc4e8` | `3596d85e074dbcee6eb47e42` | `requires_radar_key` | `None` | `False` | `READY` | `1` |
| `A1A-2c7ae5aec54deae4` | `46fccd66-378c-47dc-91d6-16b33b36b2fe` | `bd1a4cf729701d698457c96a` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-780d5f061b6f248e` | `46fccd66-378c-47dc-91d6-16b33b36b2fe` | `bd1a4cf729701d698457c96a` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-a90af4b597bb25fc` | `4a6cff49-1286-47e2-8c0e-9678638e08b6` | `1e71d9a13cbb1d1f32455bff` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-7e3ff5fb6865fb99` | `4cddc62f-71e0-4106-a1aa-13080a6a2934` | `439082c9b8bdf249c7799223` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-25bc3d6c2c00c96a` | `4cddc62f-71e0-4106-a1aa-13080a6a2934` | `439082c9b8bdf249c7799223` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-37aa8efbc6d58174` | `5742c567-92c6-47f3-b755-9c936886d905` | `1050bb89634e172910d88402` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-7c11865f296a4aee` | `5742c567-92c6-47f3-b755-9c936886d905` | `1050bb89634e172910d88402` | `is_gender_neutral` | `None` | `True` | `READY` | `1` |
| `A1A-9eae67b1ab6e9c68` | `5742c567-92c6-47f3-b755-9c936886d905` | `1050bb89634e172910d88402` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-4718b4db01684dc5` | `5d9e20fd-4e64-417e-9942-11472e59c715` | `717915db1407696a7aeca883` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-1649d4a9bf6c901d` | `5d9e20fd-4e64-417e-9942-11472e59c715` | `717915db1407696a7aeca883` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-a43bc3a0623396af` | `6067c02c-993c-426c-b0ea-100b11b658df` | `d6a814c2f04e92c2cc621951` | `has_baby_changing` | `None` | `False` | `READY` | `1` |
| `A1A-784a29a612e94f7b` | `7b7c91a5-febf-4999-9cc6-cb94b81ab99c` | `f0f4b839449d3f093fcd40cb` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-33b20081f975a751` | `7c5bbff3-1cfa-4d3e-916f-c89d12ff584a` | `c5f65b256609c21ce0b3d170` | `is_accessible` | `None` | `True` | `READY` | `1` |
| `A1A-0a21d1a5fb98b3e5` | `7c5bbff3-1cfa-4d3e-916f-c89d12ff584a` | `c5f65b256609c21ce0b3d170` | `is_gender_neutral` | `None` | `True` | `READY` | `1` |
| `A1A-4b1851d440f08952` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `72d4de0ff7f5180a8c1ac83d` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-a5eee1368da842f2` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `72d4de0ff7f5180a8c1ac83d` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-4ef92af4fd47ce10` | `88e5418e-2dbd-454e-9c6f-af53c5e45780` | `72d4de0ff7f5180a8c1ac83d` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-89868359bdc93f84` | `8c838ebd-4939-4913-98a5-4f85825bf7d2` | `2af1f5fe27a2e4a6ee9df327` | `has_baby_changing` | `None` | `False` | `READY` | `1` |
| `A1A-fec6519dda44a86f` | `8c838ebd-4939-4913-98a5-4f85825bf7d2` | `2af1f5fe27a2e4a6ee9df327` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-0dae68e673cd6801` | `8c838ebd-4939-4913-98a5-4f85825bf7d2` | `2af1f5fe27a2e4a6ee9df327` | `requires_radar_key` | `None` | `False` | `READY` | `1` |
| `A1A-81b2ea41ab4d0a9c` | `a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23` | `fd83a87fa4acc5f1915ecad9` | `has_baby_changing` | `None` | `False` | `READY` | `1` |
| `A1A-9abc60241199d9a4` | `a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23` | `fd83a87fa4acc5f1915ecad9` | `is_accessible` | `None` | `False` | `READY` | `1` |
| `A1A-f4bf1fe6a37e8455` | `a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23` | `fd83a87fa4acc5f1915ecad9` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-5408da6431ecfb7f` | `a4c31707-e414-454c-addd-e8e4bf34c6b7` | `47931cc3659d98b3ff90623d` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-c32e70aefb22f775` | `a4c31707-e414-454c-addd-e8e4bf34c6b7` | `47931cc3659d98b3ff90623d` | `requires_radar_key` | `None` | `False` | `READY` | `1` |
| `A1A-0985469bdc5f469f` | `b38ccc30-9b2d-4d98-be93-52b7597e7469` | `43119c8c4a6c8435eb0a98c7` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-a5d4c79b305cf825` | `ba77f1fd-b878-4347-beeb-26f5a8a38291` | `2793dd03c8dcacd811e23691` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-14a2f2486797e478` | `ba77f1fd-b878-4347-beeb-26f5a8a38291` | `2793dd03c8dcacd811e23691` | `is_gender_neutral` | `None` | `True` | `READY` | `1` |
| `A1A-1d279953b20c290b` | `cef8cd94-4722-4a0a-af99-d41d89162eaa` | `5577f4ba2cf8063eb3250cce` | `has_baby_changing` | `None` | `False` | `READY` | `1` |
| `A1A-a4d2467049269502` | `cef8cd94-4722-4a0a-af99-d41d89162eaa` | `5577f4ba2cf8063eb3250cce` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-0226ed79286f606a` | `cef8cd94-4722-4a0a-af99-d41d89162eaa` | `5577f4ba2cf8063eb3250cce` | `requires_radar_key` | `None` | `False` | `READY` | `1` |
| `A1A-6102cd8dec46ae07` | `cf385907-c050-44d7-bd14-b5cb4be94a8e` | `2a7ea23fbbb9a8e0c3db5ffd` | `has_baby_changing` | `None` | `False` | `READY` | `1` |
| `A1A-b3406849910b070a` | `cf385907-c050-44d7-bd14-b5cb4be94a8e` | `2a7ea23fbbb9a8e0c3db5ffd` | `is_gender_neutral` | `None` | `False` | `READY` | `1` |
| `A1A-80634f42cbf633b6` | `cf385907-c050-44d7-bd14-b5cb4be94a8e` | `2a7ea23fbbb9a8e0c3db5ffd` | `requires_radar_key` | `None` | `True` | `READY` | `1` |
| `A1A-85ae14976cf23ad3` | `cfa1b9d0-8976-4d41-8cc3-2150a35252a2` | `892d3b2712e46852deb18efa` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-7a4a02b1c593659f` | `cfa1b9d0-8976-4d41-8cc3-2150a35252a2` | `892d3b2712e46852deb18efa` | `is_gender_neutral` | `None` | `True` | `READY` | `1` |
| `A1A-8c50e66d0952205f` | `e268da6e-7717-480b-8e73-cce1829e23c7` | `ce9db1854310c73d5d981099` | `has_baby_changing` | `None` | `True` | `READY` | `1` |
| `A1A-37aa9bedc41681ba` | `e268da6e-7717-480b-8e73-cce1829e23c7` | `ce9db1854310c73d5d981099` | `requires_radar_key` | `None` | `True` | `READY` | `1` |

## Provenance model

- Observed representation: `public.facilities.field_provenance JSONB` with `object keyed by facility field; existing values are per-field objects`.
- Merge strategy: copy the existing object and replace only the approved target field with the same per-field object shape extended with Apply 1A evidence.
- Unrelated provenance preserved in simulation: **True**.
- Schema safe for this simulation: **True**.
- Each hypothetical target-field delta carries the source name, source record ID, source update timestamp, approved source checksum, field, previous/new values, exact-ID basis, Apply 1A policy version, import-run identity when observed, and transaction timestamp placeholder.

## Transaction, rollback, and idempotency

A future execution must revalidate the run and every row inside one atomic transaction, update only the approved scalar, merge only that field's provenance, verify affected-row counts, and commit. Any unexpected failure must roll back the full transaction. This task intentionally implements no live execution path.
- First in-memory run would change: **48** operations.
- Repeating the same manifest adds: **0** changes; explicit idempotent no-ops: **48**.
- Synthetic partial failure rollback: **True**.

## Zero-side-effect verification

- Before snapshot SHA-256: `8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1`
- After snapshot SHA-256: `8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1`
- Persistent data differences: **0**
- All affected fields unchanged: **True**
- Relevant source links unchanged: **True**
- Relevant provenance unchanged: **True**

## Audit design

- Preferred parent: `public.import_runs`.
- Schema gap: import_runs has no dedicated columns for plan hash, manifest hash, policy version, or rollback state; do not overload unrelated columns during a live apply.
- No live audit row was created.

## Safety result

SIMULATED_ONLY
DATABASE_MUTATIONS_COMMITTED = 0
