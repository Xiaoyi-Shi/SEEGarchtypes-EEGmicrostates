## Context

仓库当前有两个并存的问题：

1. 公共命令面与 `docs/科研路线与论文大纲_改进.md` 的论文主线不一致，仍暴露区域 activity/connectivity 与若干历史 exploratory 分支。
2. Python 包虽然已经不再真正渲染 manuscript figures，但 `pipelines.py` 仍保留了大量历史 report/plot 路径和无效的图形分支发现代码，影响边界清晰度。

本次变更不引入新的分析能力，而是收缩工程边界，让主工程成为“分析与结果导出核心”，并把图形与特殊工具职责固定到 `scripts/`。

## Goals / Non-Goals

**Goals:**
- 让公共 CLI 严格对齐论文主线分析框架
- 删除已退休的 activity/connectivity 与非主线 exploratory 分支
- 让主工程只输出缓存结果、结果表和 manifest
- 清理仅为旧分支服务的配置、workflow 导出和测试
- 在文档中明确 `scripts/` 的职责边界

**Non-Goals:**
- 不在本次变更中新增论文补充分析能力
- 不重写 retained field-state / GFP-global 分析算法
- 不重构为多模块 workflow 架构，只做边界收缩和死代码清理

## Decisions

### 1. 收缩 CLI，而不是继续隐藏旧分支

直接从 CLI 和 workflow 导出面删除 `run-activity-effects`、`run-connectivity-effects` 和未纳入论文框架的分析选项，而不是继续只在帮助信息中隐藏它们。

原因：
- 用户请求是“删除所有多余分支”，不是“继续内部保留”
- CLI 是工程边界的最强信号，必须先收口

备选方案：
- 仅隐藏帮助信息，保留旧命令实现。放弃，因为仍然保留维护面和歧义。

### 2. 保留 `run-seeg-regions`，但收缩其职责

`run-seeg-regions` 继续作为论文主线的数据分期命令存在，用于 same-region bipolar 映射、覆盖统计和可复用 SEEG 区域结果数据输出；但不再承诺主工程内置区域 activity/connectivity downstream。

原因：
- 论文方法部分仍需要 same-region 筛选与覆盖统计
- GFP/global supplementary 也仍依赖统一的 SEEG 分期数据

备选方案：
- 完全删除 `run-seeg-regions`。放弃，因为会削弱主线数据准备与结果输出能力。

### 3. 主工程只保留表和 manifest 导出

`export-paper-tables` 继续保留，但只负责写出结果表和 manifest。包内历史 report/plot 发现逻辑、无效 figure hooks 和 `render_reports` 兼容层一并删除。

原因：
- 用户要求将绘图和特殊工具移到 `scripts/`
- 这也与当前 R Markdown 工作流方向一致

备选方案：
- 继续保留 no-op figure hooks。放弃，因为仍然制造“包内负责图”的错觉。

### 4. 删除只服务于退休分支的实现与测试

对 direct-state、event/windowed coupling、区域 activity/connectivity、历史 report 分支发现相关实现进行删除或至少停止导出，并同步清理测试。

原因：
- 这些代码直接支撑已退休需求
- 若只删除入口、不清理测试与导出，工程仍会继续对旧行为作出承诺

## Risks / Trade-offs

- [风险] 旧缓存和旧脚本仍可能引用已删除命令或分析标签
  → Mitigation：更新 README / `scripts/README.md`，并在 spec 中明确迁移方向。

- [风险] `pipelines.py` 仍然较大，单次清理无法完全达到理想结构
  → Mitigation：本次优先删除多余分支和无效 report 路径，后续如需要再做模块拆分。

- [风险] 某些内部 helper 可能仍残留历史命名
  → Mitigation：优先删除公共承诺与运行路径，必要时保留不再导出的内部兼容实现。

## Migration Plan

1. 更新 OpenSpec proposal/spec/design/tasks，固定新的边界
2. 精简 CLI、workflow 导出和 config 参数
3. 删除已退休分支实现与 dead report/plot 路径
4. 更新 README、`scripts/README.md` 和测试
5. 运行 `uv run pytest`

回滚方式：
- 若收缩范围过大，可按 git 变更整体回滚；本次不涉及数据格式迁移或外部状态变更

## Open Questions

- 是否还需要进一步收缩 supplementary 分支，只保留文稿明确出现的那几条
- `docs/数据处理流程文档.md` 是否在本次一并全面改写，还是后续单独整理
