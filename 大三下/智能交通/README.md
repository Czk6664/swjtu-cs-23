# 智能交通管理决策系统

本项目正在从课程展示原型升级为可运行的智能交通管理决策系统 Demo。

## 目录

- `apps/web`：React 前端应用
- `services/api`：FastAPI 后端、模型编排和任务基础设施
- `课程设计`：早期静态原型与设计参考
- `大作业1`：交通流预测实验资产
- `大作业2`：目标识别实验资产
- `openspec`：需求、设计、任务和变更文档

## 当前进度

- 已完成前后端基础骨架
- 已打通分析接口、结果查询和任务状态接口
- 已接入大作业 1 和大作业 2 的实验结果读取
- 已支持基础导出、任务轮询和浏览器端语音播报
- 正在接入 “Windows 项目 + WSL Hermes” 任务执行方案

## 快速启动

### 一键启动

在仓库根目录运行：

```powershell
.\start-demo.ps1
```

然后在浏览器打开：

```text
http://127.0.0.1:5173
```

### 单独启动后端

```powershell
cd services/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload
```

### 单独启动前端

```powershell
cd apps/web
npm install
npm run dev
```

## WSL Hermes 接入说明

Hermes Agent 官方不支持原生 Windows 运行，因此本项目采用：

- Windows 继续运行前端和 FastAPI 后端
- WSL2 中安装并运行 Hermes
- Windows 后端通过 `wsl.exe` 调用 WSL 里的 Hermes
- Hermes 的工作目录固定到当前项目在 WSL 中的映射路径

### 已支持的配置项

在根目录 `.env` 中可配置：

- `HERMES_ENABLED`
- `HERMES_COMMAND`
- `HERMES_TIMEOUT_SECONDS`
- `HERMES_WORKSPACE_ROOT`
- `HERMES_WSL_ENABLED`
- `HERMES_WSL_COMMAND`
- `HERMES_WSL_DISTRIBUTION`
- `HERMES_WSL_WORKSPACE_ROOT`
- `HERMES_TEMPLATES_DIR`
- `HERMES_PAYLOAD_DIR`
- `HERMES_LOGS_DIR`

### 前置条件

1. 已安装 WSL2
2. 已安装目标发行版，例如 `Ubuntu-22.04`
3. 已在 WSL 发行版中完成 Hermes 安装和模型配置
4. 当前项目目录可在 WSL 中访问，例如：

```text
D:\大三下\智能交通
-> /mnt/d/大三下/智能交通
```

### 启用方式

将 `.env` 中至少配置为：

```env
HERMES_ENABLED=true
HERMES_WSL_ENABLED=true
HERMES_WSL_COMMAND=wsl.exe
HERMES_WSL_DISTRIBUTION=Ubuntu-22.04
HERMES_WSL_WORKSPACE_ROOT=/mnt/d/大三下/智能交通
```

启动后端时，如果 WSL、发行版、路径映射或 WSL 内 Hermes 不可用，应用会在启动阶段直接报错。

### 当前行为

- `report` 任务：通过 WSL Hermes 生成 Markdown 报告
- `voice` 任务：通过 WSL Hermes 生成文本播报稿
- `daily-summary` 任务：通过 WSL Hermes 生成 Markdown 总结
- 如果 `HERMES_ENABLED=false`，系统会回退到本地 stub 逻辑

### 常见排查

- 检查 WSL 发行版：

```powershell
wsl.exe -l -q
```

- 检查 WSL 中 Hermes 是否可执行：

```powershell
wsl.exe -d Ubuntu-22.04 --cd /mnt/d/大三下/智能交通 bash -lc "command -v hermes"
```

- 如果路径映射错误，优先核对 `HERMES_WORKSPACE_ROOT` 和 `HERMES_WSL_WORKSPACE_ROOT`

## 后续计划

- 接入真实大模型决策 API
- 完善 WSL Hermes 任务验证和端到端测试
- 增加部署说明和最小演示流程

## 课程学习资料声明

本目录整理的是 2023 级（23 届）课程学习资料。目录导航与本次整理范围详见 [学习资料说明](学习资料说明.md)。

## 使用说明与免责声明

1. **资料背景**  
   本仓库记录一名 2023 级同学的个人课程学习与作业情况，仅反映其当时的学习记录，并非学校、学院或任课教师发布的官方资料，也不代表 2023 级全体同学的作业水平。课程安排、题目与评分标准可能因年份和任课教师不同而变化，请以当前课堂要求为准。

2. **学术诚信**  
   请勿直接复制、原样抄袭、代交或冒用本仓库中的作业、报告和代码。可以参考其中的思路与实现方法，但应在独立理解的基础上独立完成自己的任务，遵守课程关于引用、合作与 AI 使用的规定，并在引用时注明来源。

3. **AI 参与**  
   部分资料、代码、报告或解答由 AI 生成或辅助整理，且未逐项标注 AI 参与程度。AI 输出可能存在事实错误、逻辑漏洞、引用不当或代码无法运行等问题，请自行核验。

4. **成绩与准确性**  
   部分作业未必获得满分，也可能保留错误、不完整内容或过时做法。本仓库不保证资料的正确性、完整性、适用性或可复现性，也不保证获得任何分数或学习效果，相关内容仅供参考。

5. **版权与第三方内容**  
   课件、教材摘录、图片及第三方代码等内容的版权归原作者或权利人所有。收录这些内容不代表获得再次分发、商业使用或其他授权；使用或转载前请自行核实相关权利和原项目许可。本仓库不对全部资料统一授予开源许可。

6. **运行与使用**  
   示例代码可能依赖特定环境，运行前请先阅读相关说明并自行检查。使用者应遵守法律法规、学校制度和学术规范。因误用、抄袭或未经验证地采用资料而产生的问题，由使用者自行承担相应责任；本声明不排除法律规定不可免除的责任。

7. **纠错与移除**  
   如发现内容错误、个人信息或权利问题，请通过仓库 Issue 提供具体文件路径与说明。涉及个人信息时，请勿在公开 Issue 中进一步披露敏感内容；维护者将核实并尽快更正或移除。
