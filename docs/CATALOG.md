# Owner catalog v1

Envelope: `schema_version:1`, unique `event_id`, `action`, stable `project_id`, `scope`, independent `expected_revision`, `actor`, `reason`, `data`. Catalog revision is independent of status-stream revision. Repeating the same ID and payload is idempotent; collisions/conflicts return errors. All operations append `catalog_events`; no deletion is offered.

Actions:

| Action | Scope | Data |
|---|---|---|
| create | project | Complete baseline: project_id, number, name, category, root, art, goal, acceptance, route; optional canonical_repository, aliases, goal_status |
| update | project | Only name, category, root, bundled art, canonical_repository, aliases, goal_status |
| archive / restore | project or stream | Empty object; stream scope also needs exact worktree_id, branch, is_test |
| confirm_goal | project or stream | definition_hash, source_ref, version, approved_by, approved_at, evidence_refs |

For stream operations the stream must already exist. Restoring a project does not silently restore individually archived streams. Archived streams/projects reject new reports; restore explicitly. Exact already-recorded status retries remain duplicates.

`confirm_goal` must use the current definition hash shown by `owner.py list`, an actor equal to approved_by, timezone-aware approval time and nonempty source/version/evidence. It is an audit record of an operator's approval, not automatic verification. Confirming a project baseline does not approve a different stream definition. Status reporters cannot invoke catalog operations over HTTP.

`goal_source_ref` and `goal_source_version` can record a proposed/historical source while the definition remains unconfirmed. `goal_status` is descriptive metadata and cannot grant approval. `owner.py catalog-history ID --limit 50 --before CURSOR` reads the append-only owner audit, including previous catalog state and previous baseline metadata for recovery/review. Nothing is permanently removed.

The candidate files under examples/ are review templates, not an auto-import task. Replace IDs/actor/source revision placeholders, inspect current revisions, and apply one explicit operation at a time. The alias template preserves original stable IDs. Three new entries are optional candidates with unconfirmed goals and no status reports.

Candidate aliases must preserve existing IDs. Known legacy IDs include `jovi-automation`, `matelink`, `tesla-speed` and the original other six IDs. Do not replace them with repository slugs. Use aliases/canonical_repository metadata instead. Candidate count is not a confirmed total.
