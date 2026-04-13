## Why

当前仓库仍然保留了多条历史分析分支、与论文主线无关的公共命令，以及包内残留的 report/plot 路径。这些能力已经偏离 `docs/科研路线与论文大纲_改进.md` 所定义的论文主线，增加了维护成本，也模糊了“主工程负责分析与结果数据输出，`scripts/` 负责图和一次性工具”的边界。

## What Changes

- **BREAKING** 收缩公共 CLI，只保留论文主线需要的索引、EEG 状态、SEEG 区域数据、paper-focused exploratory 分析和结果表导出命令。
- **BREAKING** 删除 `run-activity-effects`、`run-connectivity-effects` 及其对应的主工程实现与测试。
- **BREAKING** 删除与论文主线无关的 exploratory 分支，包括区域事件/窗口分支、直接 EEG-SEEG state 分支，以及未纳入论文框架的 supplementary 分支。
- 精简主工程实现，使 Python 包只负责分析、缓存结果和导出结果表/manifest，不再承担包内绘图或历史 report 分支发现。
- 明确 `scripts/` 目录承担图形渲染和其他特殊工具脚本，文档与测试同步收口到这一职责边界。

## Capabilities

### New Capabilities
- `scripts-owned-paper-tooling`: 非核心图形与特殊工具脚本统一放在 `scripts/`，并消费主工程导出的结果数据。

### Modified Capabilities
- `analysis-cli-orchestration`: 公共 CLI 收缩到论文主线分析与结果导出。
- `exploratory-cross-modal-coupling`: exploratory 分析面收缩到论文主线与明确保留的 supplementary 分支。
- `manuscript-ready-report-export`: 主工程仅导出结果表和 manifest，不再保留包内图形/report 路径。
- `seeg-aal3-coupling-analysis`: `run-seeg-regions` 仅保留论文主线所需的数据分期与结果输出职责，不再承诺区域 activity/connectivity downstream。

## Impact

- 受影响代码：`src/seeg_eegmicrostates/cli.py`、`src/seeg_eegmicrostates/workflows/`、`src/seeg_eegmicrostates/coupling/`、`src/seeg_eegmicrostates/config/`
- 受影响测试：CLI、workflow、paper export 以及已退休分支相关测试
- 受影响文档：`README.md`、`scripts/README.md` 以及与旧命令面直接冲突的说明文档
