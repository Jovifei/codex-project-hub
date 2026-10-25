# Hub handoff boundaries

This repository is a sanitized source distribution. `seed.json` is synthetic.
Never infer project progress or owner approval from the example data.

- Keep status events immutable, idempotent and revision-scoped to project/worktree/branch/test.
- Status cannot change goals, archive records or approve acceptance. Owner catalog and verification commands are local CLI only.
- Archive/restore is reversible; never delete original ledger rows or business files.
- Do not read chats, credentials, business databases or unrelated project files to populate this demo.
- Do not start other agents, tests in business repositories, deployments, tunnels or network access changes.
- Keep data/, backups/, exports/, reports/, raw status exchanges and private migration evidence out of Git.
- Before applying this candidate to a real installation: online SQLite backup, test a copy, verify event hashes, then obtain the operator's migration decision.
- Run `python -B -m unittest discover -v`, `node test_frontend.cjs`, `node --check web/app.js` and synthetic browser tests before handoff.
- Never relabel README clues or agent test claims as owner-confirmed goals or real acceptance.
