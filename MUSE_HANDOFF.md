# Muse handoff

## Distribution boundary

This is an isolated, sanitized improvement candidate produced from the existing Hub source. It does not replace the running installation. The original database, event history, real project seed/registry, reports, screenshots, conversations, business logs and private backup are not in this repository/package. No deployment, credentials, agent launch or other-project change was performed.

The private source baseline had 9 registered projects, 86 streams and 504 events when copied on 2026-10-25; this is an observed local count, not a promise of current totals. [The authorized twelve-candidate read-only catalog](docs/PROJECT_CATALOG_20261025.json) contains the parent-verified repository/README/PR metadata at the stated observation times; these are unconfirmed goal/stage clues, not live execution facts. It is documentation only, never automatically imported into seed or production. README/default-branch observations cannot override more recent working branches or owner approval. The shipped nine projects are synthetic examples.

## Changes to review

1. Delivery/evidence rendering validates identity and shape, respects explicit stream selection and preserves offline/stale badges.
2. Catalog ledger adds owner-only metadata CRUD with reversible project/stream archive and restore. The original event ledger is untouched.
3. Goal confirmation stores source/version/approval evidence and exact definition hash. Existing goals remain unconfirmed; no owner approval was fabricated.
4. History API and UI page bounded rows with stream identity/cursors.
5. Status schema accepts runtime-registered project IDs. Separate catalog/status exchange docs describe portability and privacy.

## Safe migration

1. Review source diff and test evidence. Do not run owner init with synthetic seed against an operator's real database.
2. Create an online SQLite backup with the old owner CLI. Preserve the original installation and full data directory.
3. Copy the backup to a private scratch directory. Set `HUB_DATA_DIR` to that scratch directory for new CLI/server processes. `core.initialize` adds catalog tables/triggers only; it does not rewrite old events or goals.
4. Run migration compatibility tests, integrity_check and compare original event payload hashes before/after. Archive and restore only in the scratch copy first.
5. Start this candidate on a spare loopback port; inspect actual data locally. Never include scratch DB/screenshots in Git.
6. Let the operator decide whether/when to adopt the candidate. Stop the correctly identified old process only after that decision. Preserve old source/data for rollback; no deletion is needed.

This repository contains no migration approval for production. Do not deploy a server, expand network scope or add credentials without separate user instruction. Publishing the private source repository does not authorize contacting Muse or starting agents.

## Review corrections in candidate v2

- Valid same-stream structured evidence wins as a complete source; legacy prefix rows cannot overwrite it with a newer checkedAt. Recognized stale management rows are removed only from new projections, not old events.
- `recorded` never maps to passed. Local/deploy/real pass receipts require explicit passed_verified plus references; no projection changes owner verification or acceptance_claims.
- Evidence IDs are exact: fixture aliases were removed. etf and example-1 remain separate when both are registered; unknown import targets are rejected.
- The catalog document includes only authorized development metadata, no business database, health record, route trace, chat or credential. Its main/PR snapshots have different source times; current_stage/execution_status stay unknown.
