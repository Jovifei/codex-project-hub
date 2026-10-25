# Transfer contracts

## Status events

`contract.json` describes each immutable v1 event. `project_id` accepts a syntactically valid ID but must be registered in the target catalog. `expected_revision` is scoped to the exact worktree/branch/test stream. `reported_at` is source time; `received_at` is assigned by the receiving ledger. Do not substitute import time for actual engineering progress or `verified_at`.

The exchange envelope is `{ "schema": "hub-status-exchange-v1", "events": [ ... ] }`, at most 1000 status events and 32 MiB. Definition/verification/catalog changes are deliberately excluded and use separate owner review.

```powershell
python transfer.py export example-1 LOCAL-STATUS.json
python transfer.py import LOCAL-STATUS.json
python transfer.py import LOCAL-STATUS.json --apply
```

Export refuses an existing destination. Import previews against a SQLite backup copy by default and never rewrites expected revisions, identities or evidence. Apply can still meet a concurrent CAS conflict; stop, inspect the error and retry the exact file for idempotent continuation. An import is not a multi-event atomic transaction; successfully applied events remain appended. Streams with intervening definition/verification events may need explicit manual reconciliation, not automatic revision rewriting.

These files can contain real paths, notes and evidence. They are local operator artifacts, excluded from Git and never automatically uploaded. The source distribution contains only synthetic examples.

## Catalog

`owner.py catalog-export NAME.json` exports registered metadata without status history; it can still contain private project details. Import is intentionally explicit: review each candidate and create an owner catalog operation, using the existing stable ID and current catalog revision. No bulk overwrite, renaming or automatic approval is provided. Read [CATALOG.md](CATALOG.md).

## Structured management evidence precedence

A valid `hub_evidence_v1` object for the exact same project/stream is authoritative as one complete snapshot, including its checkedAt and project fields. Legacy Chinese prefix rows are fallback only when no valid structured object exists. They cannot override current/next/goal while borrowing the new structured timestamp. Both the management summary and current/next panels use that same source; original payload fields remain accessible in the immutable event history. Importing a new snapshot drops only recognized old management-prefix lines from the latest projection; immutable ledger events and free-form user notes remain intact.

Evidence import uses the exact supplied project ID. There is no implicit repository/fixture alias remapping. The target must already be registered and have the selected coordination stream; unknown targets are rejected before sending.

Compatibility five-phase bars distinguish `recorded` from `passed`. Recorded stages never become pass receipts. Local/deploy/real acceptance require an explicit `passed_verified` stage with evidence references even to display a pass receipt; code/CI can also display a sourced `passed_record` receipt. References are still claims, not automatic truth, and no projection sets acceptance_claims or owner verification. Final verified counts remain driven solely by owner verification events.

## History API

`GET /api/history/ID?limit=50&before=ROW_CURSOR&stream=[WORKTREE,BRANCH,IS_TEST]` returns `{events,next_cursor}`. Encode the stream JSON as a URL query value. Cursor ordering is stable SQLite row order; concurrent new events do not duplicate older pages. Default legacy no-query response is a bounded list (50). A cursor is local to one database, not portable evidence.
