# Local Project Hub

A local, deterministic project ledger and graphical dashboard. Python 3.10+ standard library and SQLite; the product requires no model, npm package or hosted service. Refresh and status ingestion do not run Codex.

## Quick start (Windows)

```powershell
cd PATH\TO\codex-project-hub
python owner.py init
python server.py --port 8766
```

Open http://127.0.0.1:8766. Stop the foreground server with Ctrl+C. The bind address is always `127.0.0.1`. Existing local installations may already use 8765; do not stop or overwrite them. `HUB_DATA_DIR` optionally points to a separate operator-chosen data directory before starting CLI/server processes.

`seed.json` registers nine **synthetic examples**, with illustrations retained from the original user-provided design. Nine is not a fixed product limit or the user's confirmed project count. Registration uses INSERT OR IGNORE. No real status or approval data is shipped.

## What is implemented

- Searchable graphical overview and independent details; stages, current work, next steps, blockers, references and history.
- Unknown/stale/offline state remains visible. No overall completion percentage.
- Immutable event history, exact event-id retry, revision CAS, old-report rejection and per-worktree/branch/test isolation.
- Agent claims and owner-recorded verification remain separate; new status requires re-review of prior acceptance.
- Strict rendering of legacy embedded delivery metadata; mismatched/malformed records are ignored.
- Owner-only catalog create/update, reversible project/stream archive/restore and definition provenance confirmation.
- History API paging (50 default, 100 maximum) with optional stream filter. The UI loads earlier records on demand.
- Local backups, standalone HTML snapshots, catalog export and explicit status exchange preview/import.

The browser is read-only. Administrative CRUD uses the owner CLI; status HTTP ingestion cannot invoke it. Archived records remain in SQLite and owner listing/history, and exact retries remain idempotent. This is a local-user boundary, not isolation from another program running as that same Windows user.

## Owner CRUD and provenance

`python owner.py list` includes archived projects/streams and their independent `catalog_revision`.
`python owner.py catalog event.json` applies a catalog operation. See [CATALOG.md](docs/CATALOG.md) and [examples](examples/).

Project identity is stable. Editable metadata includes display name, category, relative root, canonical repository and aliases. Goals/routes/criteria require the existing separate `definition` event through `owner.py apply`. A later `confirm_goal` catalog operation records source, version, approver, time and evidence against the exact definition hash. It does not prove evidence true. Existing/imported goals default to **unconfirmed**. Changed definitions cannot reuse old confirmation.

## Status integration

```powershell
python report.py --url http://127.0.0.1:8766 revision example-1 --worktree example-worktree --branch main
python report.py template example-1 --worktree example-worktree --branch main --agent example-agent --run example-run --revision 0
python report.py --url http://127.0.0.1:8766 send event.json
```

Review the generated JSON before sending. Registry membership is checked at runtime; the JSON schema does not hard-code nine IDs. References are displayed, never executed or read automatically. Automatic adoption by existing agents is not implied. No other project configuration or conversation is modified.

See [TRANSFER.md](docs/TRANSFER.md) for status/catalog import/export contracts. Exports can contain sensitive operator data; they are local and excluded from the source package.

## Backup and recovery

```powershell
python owner.py backup operator-backup.sqlite3
python owner.py export operator-snapshot.html
```

Online backup uses SQLite's backup API; do not copy only the main SQLite file while WAL is active. `backups/` and `exports/` are never published. For recovery, stop only the identified Hub process, preserve the complete current data directory in a new private archive, validate a backup copy with `PRAGMA integrity_check`, and point `HUB_DATA_DIR` to the recovered copy. Keep the old directory for rollback. No permanent cleanup is required.

## Validation

```powershell
python -B -m unittest discover -v
node test_frontend.cjs
node --check web/app.js
python tests/browser_synthetic.py
```

Only the last browser command needs Python Playwright and a Chromium/Edge browser. They are development dependencies, not product runtime dependencies. The test uses temporary synthetic data, a temporary local port and owns only its own server process.

This candidate is separate from the original installation. See [MUSE_HANDOFF.md](MUSE_HANDOFF.md) for exact boundaries, migration and pending operator decisions. No server deployment is configured.

## Authorized private handoff catalog

[PROJECT_CATALOG_20261025.json](docs/PROJECT_CATALOG_20261025.json) preserves the original nine stable IDs and three unconfirmed candidates, with approved repository/goal clues and fixed-SHA/PR observations supplied by the parent. It does not modify seed, live status, goals or permissions. Main is a historical baseline; PRs are candidates; all current execution states remain unknown.
