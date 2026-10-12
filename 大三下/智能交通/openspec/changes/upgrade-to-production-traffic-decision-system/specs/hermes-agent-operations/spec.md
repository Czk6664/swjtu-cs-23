## ADDED Requirements

### Requirement: Hermes 处理运营辅助任务
系统必须集成 Hermes Agent 来处理非核心运营任务，包括表格生成、语音播报生成和每日总结。

#### Scenario: 用户请求生成报表
- **WHEN** 后端向 Hermes 下发报表生成任务
- **THEN** Hermes 产出可追踪的结构化文件或失败结果，供后端记录和展示

### Requirement: 主系统可观察 Hermes 任务
系统必须通过主应用展示 Hermes 任务状态和输出结果，使用户无需单独进入 Hermes 也能查看常规任务执行情况。

#### Scenario: Hermes 任务结束
- **WHEN** 一个 Hermes 任务进入终态
- **THEN** 后端记录最终状态，并将结果展示给前端

### Requirement: Hermes 集成对主链路保持可选
当 Hermes 不可用时，系统必须优雅降级，保证核心预测、识别和决策接口仍可继续运行。

#### Scenario: Hermes 离线
- **WHEN** Hermes 不可用时用户请求一个依赖 Hermes 的任务
- **THEN** 系统报告任务失败或不可用状态，但不影响其他核心分析流程
