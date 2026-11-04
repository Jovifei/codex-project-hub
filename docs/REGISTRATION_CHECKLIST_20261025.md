# 真实项目注册核对清单（2026-10-25）

> 定位：本文件是逐项操作清单，不是自动导入任务。`docs/PROJECT_CATALOG_20261025.json`
> 仍是只读参考（`auto_import: false`）；本清单不自动导入、不改变 seed、不改变实时状态、
> 不改变目标、不改变权限、不批准任何事项。本清单不自动导入任何项目。

## 通用规则

- 逐项、逐个 owner 操作登记；不要批量导入、不要改写已有稳定 ID、不要用仓库 slug 替换稳定 ID。
- 目录里的 `head_sha` / `head_committed_at` 是 2026-10-25 约 05:54（UTC）的冻结观察，
  不是当前 HEAD；登记前必须重新核对远端当前 HEAD 与 README，不得照抄。
- 所有目标在用户本人 `confirm_goal` 之前一律是“待用户确认”；`goal_status`、README 叙述、
  PR 草稿、CI 状态都不能算确认，更不能算验收通过。
- `seed.json` 的 example-1 至 example-9 是合成示例，与下表无关；不要把任何真实项目映射到示例项目。
- 下表之外的项目不要擅自并入：2026-10-25 15:30 快照里的 Automation_Seal、
  Jovi-embedded-work-skill 未列入本目录，需用户另行确认是否纳入。
- codex-project-hub 本身是看板工具，不是被监控项目；不登记为监控项目（除非用户另行说明）。
- 网页只读；增删改查走本地 owner CLI；不要为登记开放无鉴权写接口；删除优先用可恢复归档。

## 登记步骤（每个项目重复一次）

1. 重新读取远端当前 HEAD 与 README 首段，记录核对时间；与目录冻结值不一致时以重核结果为准。
2. 用 `owner.py catalog` 提交 `create` 操作（参考 `examples/new-candidates.template.json`，
   把 REPLACE 占位符换成已核对的值；`number` 以原安装为准，不要编造；
   `aliases` 保留原稳定 ID 的旧称；`canonical_repository` 填下表仓库）。
3. 用 `owner.py apply` 提交 `definition` 事件（目标、验收、路线）。
4. 用户本人 `confirm_goal`：`actor` 必须等于 `approved_by`，带 `source_ref`、`version`、
   `evidence_refs`，`definition_hash` 必须等于当前定义哈希；定义变更后旧确认自动失效，需重新确认。
5. 状态上报走 `report.py` / `import_evidence.py` 协调流；上报不能修改目标、不能批准验收；
   拿不到证据的字段一律显示“未知／待确认”，不填进度百分比。

## 12 项核对表

| 稳定 ID | 仓库 | 目录目标（待用户确认） | 目录冻结 HEAD（UTC） | 目录 README 叙述 | 开放 PR 抽样（目录记录，非全部） | 登记注意 |
|---|---|---|---|---|---|---|
| jovi-automation | Jovifei/Automation_Jovi（目录记为 private） | 中文数字产品工作台 | 072d137e9462f2cb6366218aad47d1869f97f886，2026-10-07T07:59:43Z | 离线合成交易验收入口 | #6 草稿 | 旧称 automation-jovi |
| ai-photography-director-app | Jovifei/ai-photography-director-app（public） | Android优先AI摄影现场导演App | 5901a06defb67369035de7cb64cd5ca2d94c638c，2026-10-07T06:33:05Z | README候选叙述早于HEAD，需精确状态复核 | #21、#20 草稿 | 旧称 ai-photography-director |
| nightly-photo-intelligence-pipeline | Jovifei/nightly-photo-intelligence-pipeline（public） | 摄影收藏到结构化知识的离线生产流水线 | fd9ded5698a6521aef5ff0c26f211bdbd7d4b1e3，2026-10-04T16:13:43Z | N2B1P待外部审查，N2B2 LOCKED | 抽样无开放 PR | 旧称 nightly-photo-intelligence |
| openclaw-videofactory | Jovifei/OpenClaw_VideoFactory（public） | 工程知识及产品演示视频工厂 | 40dc9aca04d407116781889ec099bd5e9e6d1fff，2026-10-25T04:40:24Z | Phase 1 / in_progress / 正式Gate未通过 | #2 草稿 | 旧称 openclaw-video-factory |
| star-photo-addr | Jovifei/Star_photo_addr（public） | 星空摄影与天气条件选址决策 | ba73851c08e8566f756f8dbf6e6382e00fed3faf，2026-10-24T04:59:00Z | README列功能与Beta，不构成完整验收 | #55、#52 草稿 | 旧称与稳定 ID 同名 |
| matelink | Jovifei/tesla-master-mimo（public） | Tesla MateLink双端监控应用 | 427de74e273cd86527aca4b8fd1386e38c1336e8，2026-10-24T05:44:12Z | 双端工程存在，设备与发布未验 | #27、#28 草稿 | 稳定 ID matelink ≠ 仓库 slug，用 canonical_repository 字段，不要改 ID；旧称 tesla-master-mimo |
| etf-fund-analysis | Jovifei/ETF-Fund-Analysis（public） | 本地计算与有界展示的ETF/LOF研究工作台 | 1f24632a6618a53b4ec2f13c6c667dfeac5d9f15，2026-10-25T05:49:34Z | 网页已有、独立手机App未交付；research_only | #53、#50 草稿 | 旧称与稳定 ID 同名 |
| tesla-speed | Jovifei/Tesla_Simulate_vico（public） | 车辆虚拟引擎音色与Android实时声浪 | 6e4cf1437972caf383baab3f987de0ebf2db373d，2026-10-03T14:29:55Z | S12 → 人类听审Gate → Android实时声浪 | #41、#39 草稿 | 稳定 ID tesla-speed ≠ 仓库 slug，用 canonical_repository 字段，不要改 ID；旧称 tesla-simulate-vico |
| medcial-box | Jovifei/Medcial-box（public） | 家庭共享药箱与照护记录 | 07dad9864aadf224bf8657df35041a53e76a6be7，2026-10-25T05:17:08Z | PARTIAL / 1.0.6候选 / Android build 10 | #7 草稿 | 旧称与稳定 ID 同名 |
| ai-short-vidio-claw | Jovifei/AI-short-vidio-claw（public） | 角色一致、可追溯9:16 AI短剧生产线 | e3f74281fc14d6bcd05e6c1f2657a07c77dc0f34，2026-10-11T07:33:45Z | 源图库交付、试拍候选；不等于T1或30镜完成 | #12（非草稿） | 旧称与稳定 ID 同名；新增候选模板编号 10 |
| embedded-system-designer-coach | Jovifei/embedded-system-designer-coach（目录记为 private） | 嵌入式系统设计师陪伴学习闭环 | 97412eb1561d9c2ac47c3e4d3782822a716ff570，2026-08-20T12:47:05Z | PHASE_0_SCAFFOLD_READY_LOCAL_ONLY | #3、#2 草稿 | 旧称与稳定 ID 同名；新增候选模板编号 11 |
| personal-health-hub | Jovifei/personal-health-hub（目录记为 private） | 本地优先健康资料、睡眠运动与保险条款整理 | bdb347041de45f8ca0d17d09d733b67838fc8636，2026-10-20T15:21:32Z | 本地合成资料Alpha候选；真实资料迁入未批准 | #11、#10 草稿 | 旧称与稳定 ID 同名；新增候选模板编号 12；真实资料迁入需用户另行批准，本清单不批准 |

## 统一缺项（登记前必须补齐）

- 各项目当前远端 HEAD（需重核，目录冻结值不得直接当作当前值）。
- 各项目 `number`（以原安装为准，不要编造；模板编号 10/11/12 仅对应 3 个新增候选）。
- 各项目 `definition` 事件内容（目标、验收、路线）。
- 用户本人的 `confirm_goal` 记录（来源、版本、批准人、时间、证据）。
- 本机数据库、事件历史与备份（未上传，不在本仓库；登记不等于已接入实时监控）。

## 完成标准

12 项全部登记且目标确认状态如实记录；未完成项保留“未知／待确认”，不填进度百分比；
任何一项的确认都必须能追溯到来源、版本与用户本人的确认依据。
