## Why

`src/seeg_eegmicrostates/workflows/pipelines.py` 目前承载了路径命名、artifact 发现、核心 stage、exploratory 分发、paper export，以及一批历史遗留分支，文件规模已经明显超出可维护范围。继续在单文件内演化会放大重构成本，也会让后续删除退休分支或新增保留分析时更容易引入回归。

## What Changes

- 将 `workflows/pipelines.py` 拆分为 `workflows/` 下按职责组织的子模块，而不是继续将所有 workflow 逻辑堆在单文件中。
- 保留当前公开 workflow 入口和 CLI 行为不变，对外仍由 `seeg_eegmicrostates.workflows` 导出主工程使用的少量入口函数。
- 把 branch/path helper、核心 staged workflow、exploratory workflow、paper table export 分离到独立模块，降低耦合度。
- 清理只服务于历史已退休分支的 workflow 粘连代码，避免新的模块结构继续继承单文件历史包袱。
- 为后续继续收缩或演进保留分析面提供更清晰的模块边界和测试落点。

## Capabilities

### New Capabilities
- `workflow-module-organization`: `workflows` 包应按职责拆分内部模块，同时保持公开 workflow 入口稳定。

### Modified Capabilities

## Impact

- 受影响代码：`src/seeg_eegmicrostates/workflows/`、`src/seeg_eegmicrostates/cli.py`、相关测试文件
- 对外 API 影响：无预期行为变更，公开 workflow 入口保持兼容
- 风险点：导入路径重组、循环依赖、测试夹具对旧单文件内部函数的隐式耦合
