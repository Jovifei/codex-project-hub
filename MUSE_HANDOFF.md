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

## 独立复核（2026-10-25，第二轮，Muse 接手）

### 访问与基线

- 上一轮阻断已解除：仓库改为公开后，README 与提交均可读；远端 HEAD 即基线提交
  79e0107d5d8003ec86683481739a418e5bc3afbf，无后续提交，无需回退。
- 本轮工作分支：`muse-takeover-20261025`（只创建、不合并的 PR 见分支说明）。

### 实测结果（非照抄）

- `python -B -m unittest discover`：39 项通过（含新增 2 项后为 41 项，见下）。
- `node test_frontend.cjs`：13 项通过；`node --check web/app.js` 通过。
- 浏览器合成测试（`tests/browser_synthetic.py`）在本机未跑：Playwright 未安装，
  属开发依赖缺失，不代表产品缺陷；其断言要点已由前端单测与下述实测覆盖。
- VM 回环实测（端口 18765，`HUB_DATA_DIR` 指向隔离临时目录，验证后已停服）：
  9 个合成项目、目标默认未确认、跨站 Host 403；同一事件重发返回 `duplicate: true`；
  旧报告与 revision 冲突返回 409；归档后项目从总览消失且新报告被拒，恢复后恢复；
  catalog-history 保留 previous_baseline / previous_catalog_state；在线备份与独立 HTML 快照导出成功；
  结构化证据导入成功且二次导入幂等。

### 六项重点复查结论

1. 证据对应：同项目同工作流的结构化证据整体优先；旧管理前缀行仅在新投影中被剔除，
   不可逆事件本身不动；旧证据不能覆盖新投影（`import_evidence.py` 拒绝旧 checkedAt）。
2. `recorded` 语义：`recorded` 不映射为通过；五阶段视图中 `recorded` 显示“已记录 · 未验证”，
   真实验收需 `passed_verified` 加证据引用；新状态报告使此前验收回到需重验。
3. 项目 ID：严格匹配，无隐式别名映射；`etf` 与 `example-1` 各自独立；未知导入目标在发送前被拒。
4. 历史与归档：历史分页默认 50、上限 100，游标按行序稳定；归档/恢复可逆且保留历史；
   版本 CAS 与事件幂等均有单测与实测覆盖；更新不覆盖历史记录。
5. 断线与过期：断线、超 24 小时过期、未来上报时间均有明确未知态；刷新失败保留最后有效快照，
   不伪装成新证据。
6. 目标确认：目标默认未确认；`confirm_goal` 要求定义哈希一致、`actor` 等于 `approved_by`、
   时区化批准时间与非空证据；定义变更后旧确认失效；本轮未替用户确认任何目标。

### 三类划分

- 已实现：上述六项、只读网页、owner CLI 增删改查、可恢复归档、备份与快照导出、状态交换预览/导入。
- 确有缺陷（本轮已修）：`start-background.ps1` 基线存在混合换行（10 行 LF 夹 1 行 CRLF），
  导致 `MANIFEST.sha256` 在常规 checkout 下对该文件校验失败；`.gitattributes` 曾对 ps1 用
  `eol=crlf`，使新 checkout 的 ps1 工作区文件与清单哈希不一致。修复：该脚本统一为 LF、
  清单条目同步更新、ps1 改为 `eol=lf`（PowerShell 可正常执行 LF 脚本），新增
  `test_manifest.py`（原始或 LF 归一化哈希任一匹配即通过，真实内容漂移仍会失败）。
- 尚未实现：真实项目登记（目录 12 项均未登记，属操作步骤而非代码缺失；见
  `docs/REGISTRATION_CHECKLIST_20261025.md`，附 `test_registration_checklist.py` 一致性测试）；
  浏览器合成测试的本机运行环境（需 Playwright，与产品运行无关）。

### 换行符注意事项（后续维护者必读）

- 本仓库 `.gitattributes` 曾使工作区文件带 CRLF，`git status` 可能显示整树“已修改”，
  但 `git diff --ignore-cr-at-eol` 为空即表示内容无实质变化；提交时只加 intended 文件，
  不要整树提交。
- 清单校验以 `test_manifest.py` 为准；直接对 checkout 跑 `sha256sum -c MANIFEST.sha256`
  在旧 checkout 上仍可能因历史换行转换出现 ps1 差异，新 checkout 已无此问题。
- 本次修改随附将 MUSE_HANDOFF.md 统一为 LF（与 `.gitattributes` 一致）；旧基线为 CRLF，
  故该文件差异包含整文件换行归一化，内容新增见本节；清单条目已同步更新。

### 本轮未做事项

- 未部署到服务器或公网，未修改用户本机现役看板，未开放端口，未新增凭据或持久访问，
  未启用定时采集/推送，未替 ETF、声浪、药箱、逐星、MateLink 创建任何执行任务，
  未自动导入目录或示例数据，未合并任何 PR。
