Validation on Windows, 2026-10-25.

- Unit tests: Ran 39 tests; OK.
- Frontend assertions: 13 passed.
- Synthetic browser, migration-copy and CLI/export smoke checks passed; see JSON files.
- The initial new tests failed before fixes. A Windows SQLite preview connection leak and a Playwright CSP string-expression harness error were found during expanded tests and corrected. Product CSP was not weakened.
- Screenshots contain only synthetic data. No production runtime adoption or deployment was performed.
- Administrative CRUD is local owner CLI only. History expansion may reset on a refresh/navigation. The twelve optional candidates are not a confirmed live project count.
