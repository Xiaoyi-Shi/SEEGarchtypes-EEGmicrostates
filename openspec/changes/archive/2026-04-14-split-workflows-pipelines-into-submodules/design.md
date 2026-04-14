## Context

当前 `src/seeg_eegmicrostates/workflows/` 目录只有 `__init__.py` 和一个超大的 `pipelines.py`。该文件同时承载了 branch/path 命名、artifact 发现、核心 staged workflow、exploratory workflow 分发、paper table export，以及历史遗留的旧 stage 和兼容逻辑，导致任何局部修改都需要在同一文件内穿梭多个分析家族与输出层。

本次变更是一次内部架构收口，不打算改变公开 CLI 或主工程保留的 workflow 语义，而是把实现重新组织到更小的模块边界中，降低后续继续删除退休分支、维护 retained analysis surface、以及补测试时的认知负担。

## Goals / Non-Goals

**Goals:**
- 将 `workflows/pipelines.py` 拆成按职责分组的内部模块
- 保持 `seeg_eegmicrostates.workflows` 的公开入口稳定
- 让核心 staged workflow、exploratory workflow、paper export 和共享 helper 分开维护
- 在拆分过程中清理仅为退休分支服务的 workflow 粘连代码

**Non-Goals:**
- 不改变公开 CLI 的命令面或参数语义
- 不重写 retained analyses 的科学计算逻辑
- 不在本次变更中引入新的分析 capability

## Decisions

### 1. 保留 `workflows` 包入口，内部改成子模块

`src/seeg_eegmicrostates/workflows/__init__.py` 继续作为对外兼容层，统一 re-export 主工程仍公开使用的少量入口函数；内部新增子模块承接实现。

原因：
- 公开 API 当前很小，保留兼容层可以避免 CLI 和测试同时大改
- 用户关心的是把单文件拆开，而不是引入新的调用方式

备选方案：
- 直接让 CLI 改为从新子模块导入。放弃，因为会把纯内部重构扩散成不必要的外部接口变更。

### 2. 按职责而不是按函数数量切分模块

优先形成以下边界：
- 共享常量、branch/path/helper
- 核心 staged workflow
- exploratory workflow 及分发
- paper table export

原因：
- 现有文件的问题是职责混杂，不是单纯函数太多
- 按责任边界切分更利于后续继续删除退休分支，而不是把历史包袱平均分散到多个文件

备选方案：
- 机械地按行数拆成多个 `pipelines_part*.py`。放弃，因为不会改善设计，只会制造新的导航成本。

### 3. 先抽基础依赖，再迁移 stage 实现

重构顺序应先抽出不会改变行为的 constants/helper，再迁移 core stage、export、exploratory stage，最后收口 dispatcher 和兼容导出。

原因：
- helper 先独立出来后，后续文件移动更容易避免循环依赖
- exploratory dispatcher 依赖面最广，应最后收口

备选方案：
- 直接先拆 `run_exploratory_coupling_stage`。放弃，因为它依赖太多 helper 和 stage，先动它最容易卡在导入环里。

### 4. 模块边界应围绕 retained workflow，而不是旧分支历史

新的模块结构应以当前保留的 staged workflow、paper-focused exploratory analyses 和 result-table export 为主线，不应为了兼容已退休的 activity/connectivity、direct-state、event/windowed 等旧分支而保留对等一级模块。

原因：
- 前一轮工程收口已经明确主工程边界
- 如果让退休分支继续决定模块划分，只会把单文件历史包袱换一种方式固化下来

## Risks / Trade-offs

- [风险] 拆文件后出现循环导入或初始化顺序问题
  → Mitigation：先抽纯 helper/constant 模块，`__init__.py` 只做轻量 re-export，不承载运行逻辑

- [风险] 测试可能隐式依赖 `pipelines.py` 中的内部函数位置
  → Mitigation：优先让测试改为依赖公开入口，必要时只保留少量稳定的内部 helper 导出

- [风险] 拆分过程中把历史退休分支一起搬迁，导致无效代码继续扩散
  → Mitigation：在迁移时同步删除已不属于 retained workflow 的 stage 和兼容路径

- [风险] paper export 仍混入图形相关遗留逻辑
  → Mitigation：把 export 作为独立模块收口，只保留结果表与 manifest 相关路径

## Migration Plan

1. 新建 `workflows/` 子模块文件并抽出共享 helper
2. 迁移 core staged workflow 到独立模块
3. 迁移 retained exploratory stage 与 dispatcher
4. 迁移 paper table export 逻辑并删除遗留 report/render 粘连代码
5. 更新 `workflows/__init__.py` 和相关测试，确认公开入口不变

回滚方式：
- 若拆分过程中引入难以快速定位的导入问题，可整体回滚本次重构；本次变更不涉及数据迁移或缓存格式切换

## Open Questions

- `pipelines.py` 中剩余的历史 stage 是否在拆分前先彻底删除，还是在迁移过程中边搬边删
- 是否需要引入 `workflows/exploratory/` 子包，而不是只拆成若干平铺模块
