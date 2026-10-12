import { FormEvent, useEffect, useMemo, useState } from "react";

type Workflow = "prediction-only" | "detection-only" | "full-decision";

type AnalyzeResponse = {
  result_id: string;
  workflow: Workflow;
  status: string;
  forecast?: {
    source_dir: string;
    headline: string;
    datasets: string[];
    baseline?: {
      mae?: string;
      rmse?: string;
      mape?: string;
    };
    dgl?: {
      rmse?: string;
      mape?: string;
      inference_time?: number;
    };
  } | null;
  detection?: {
    dataset_config: string;
    run_dir: string;
    classes: string[];
    num_classes: number;
    latest_metrics?: {
      precision?: string;
      recall?: string;
      mAP50?: string;
      mAP50_95?: string;
    };
    preview_assets?: {
      prediction_grid?: string;
      confusion_matrix_normalized?: string;
      training_curve?: string;
    };
  } | null;
  decision?: {
    facts: string[];
    risk_level: string;
    recommendation: string;
    explanation: string;
  } | null;
  spawned_tasks: string[];
};

type TaskRecord = {
  task_id: string;
  title: string;
  task_type: string;
  state: string;
  created_at: string;
  result?: {
    provider?: string;
    artifact_path?: string;
    wsl_distribution?: string;
    exit_code?: number;
    message?: string;
    stderr?: string;
    [key: string]: unknown;
  } | null;
  error?: string | null;
};

type StageKey = "perception" | "prediction" | "assessment" | "warning" | "guidance";
type SceneKey = "commute" | "incident" | "campus";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const apiCards = [
  {
    title: "场景分析",
    path: "POST /api/analyze-scene",
    description: "触发预测、识别或完整决策流。",
  },
  {
    title: "分析结果",
    path: "GET /api/results/{result_id}",
    description: "查看最近一次结构化分析结果。",
  },
  {
    title: "任务中心",
    path: "GET /api/tasks/{task_id}",
    description: "跟踪报表、语音、日报等后台任务。",
  },
];

const stageContent: Record<
  StageKey,
  {
    title: string;
    owner: string;
    description: string;
    input: string;
    output: string;
    impact: string;
  }
> = {
  perception: {
    title: "场景感知：识别复杂交通参与者与关键异常目标",
    owner: "小模型主导",
    description: "使用轻量视觉模型实时识别车辆、行人、非机动车和异常行为，为后续态势分析提供结构化输入。",
    input: "路口视频流 / 路侧传感器",
    output: "目标类别、位置、冲突风险",
    impact: "支撑异常目标快速发现",
  },
  prediction: {
    title: "流量预测：判断未来时段的路网压力变化",
    owner: "小模型主导",
    description: "基于多尺度历史时序和路网关联关系输出短时与中时段流量趋势，为预警提前量提供支撑。",
    input: "历史流量序列 / 时段特征",
    output: "未来负荷、拥堵长度、波动趋势",
    impact: "支撑预警提前发布",
  },
  assessment: {
    title: "态势研判：把检测结果翻译成管理者可理解的风险解释",
    owner: "大模型主导",
    description: "融合感知结果、预测趋势和规则知识，将多源信息总结为可解释的态势结论和原因归纳。",
    input: "目标事件 + 流量趋势 + 规则知识",
    output: "风险原因、影响范围、事件摘要",
    impact: "支撑值守人员快速判断",
  },
  warning: {
    title: "分级预警：根据态势级别输出对应响应优先级",
    owner: "大模型主导",
    description: "结合研判结果和交通管理预案，生成不同级别的预警建议，帮助明确资源投入强度。",
    input: "态势结论 / 响应预案 / 历史经验",
    output: "预警级别、触发条件、提醒对象",
    impact: "支撑分级响应决策",
  },
  guidance: {
    title: "诱导管控：把决策建议转成面向现场的处置动作",
    owner: "大模型 + 执行端协同",
    description: "将预警结果转化为路侧诱导语句、警力部署建议和后续机器狗执勤任务接口。",
    input: "预警级别 / 处置资源 / 场景约束",
    output: "诱导文案、调度建议、执勤指令",
    impact: "支撑策略落地执行",
  },
};

const sceneContent: Record<
  SceneKey,
  {
    title: string;
    badge: string;
    load: string;
    queue: string;
    targets: string;
    action: string;
  }
> = {
  commute: {
    title: "早高峰主干道拥堵预警",
    badge: "Level II 预警",
    load: "86%",
    queue: "1.8 km",
    targets: "24",
    action: "分级诱导",
  },
  incident: {
    title: "快速路事故扰动处置",
    badge: "Level I 预警",
    load: "92%",
    queue: "2.6 km",
    targets: "11",
    action: "事故分流 + 路警联动",
  },
  campus: {
    title: "校园路口人车冲突提醒",
    badge: "Level III 预警",
    load: "61%",
    queue: "0.7 km",
    targets: "37",
    action: "慢行优先诱导",
  },
};

const demoSteps = [
  {
    title: "观测输入",
    body: "汇聚视频流、流量序列与事件线索，让小模型先产出结构化观察结果。",
  },
  {
    title: "协同研判",
    body: "把预测结果、目标识别和规则库信息整合为面向管理者的态势结论。",
  },
  {
    title: "输出策略",
    body: "输出分级预警、路侧诱导文案和执勤建议，形成完整决策闭环。",
  },
];

const chartBase = "/experiment-charts/";

const improvementRows = [
  {
    method: "Baseline",
    type: "强基线",
    precision: "0.7963",
    recall: "0.6732",
    map50: "0.7580",
    map5095: "0.5313",
    verdict: "当前综合精度最高，作为所有改进的对照组。",
  },
  {
    method: "CBAM",
    type: "注意力结构",
    precision: "0.4681",
    recall: "0.6042",
    map50: "0.5294",
    map5095: "0.3785",
    verdict: "没有超过强基线，说明小数据集上直接加注意力会带来收敛压力。",
  },
  {
    method: "P2 + CBAM",
    type: "小目标检测头 + 注意力",
    precision: "0.4830",
    recall: "0.6444",
    map50: "0.5908",
    map5095: "0.4303",
    verdict: "优于单独 CBAM，但仍低于强基线；P2 对召回有帮助，训练策略仍需优化。",
  },
  {
    method: "Focaler-IoU",
    type: "损失函数",
    precision: "0.6979",
    recall: "0.6594",
    map50: "0.7187",
    map5095: "0.5343",
    verdict: "唯一在 mAP50-95 上超过基线的方法，更适合强调定位精度的场景。",
  },
  {
    method: "Gold-YOLO GD",
    type: "架构改进",
    precision: "0.3641",
    recall: "0.5258",
    map50: "0.3927",
    map5095: "0.2709",
    verdict: "从零训练与复杂模块叠加导致收敛不足，不适合当前小数据集直接替换。",
  },
  {
    method: "SAHI",
    type: "推理策略",
    precision: "-",
    recall: "-",
    map50: "-",
    map5095: "-",
    verdict: "不改模型，Focaler-IoU + SAHI 检测数达到 5526，是 Baseline + SAHI 的 2.3 倍。",
  },
];

const experimentInsights = [
  {
    title: "两个早期结构改进的结论",
    body: "CBAM 和 P2+CBAM 都没有超过 704/50epoch 强基线；但 P2+CBAM 相比 CBAM 的 Recall 从 0.6042 提升到 0.6444，说明新增小目标检测头确实更关注远距离小标志。",
  },
  {
    title: "三组新改进实验的结论",
    body: "Focaler-IoU 是最稳的训练阶段改进，mAP50-95 从 0.5313 提升到 0.5343；Gold-YOLO GD 理论更强但当前数据量和训练轮数不足；SAHI 在推理阶段显著提升小目标检出数。",
  },
  {
    title: "最终推荐方案",
    body: "报告中推荐 Focaler-IoU + SAHI：前者提高定位质量，后者通过切片放大小目标，整体实现成本低，也更适合课程 demo 落地。",
  },
];

const experimentCharts = [
  {
    title: "综合指标对比",
    src: "chart1_grouped_bar.png",
    caption: "多方法 Precision、Recall、mAP50、mAP50-95 的横向对比。",
  },
  {
    title: "综合能力雷达图",
    src: "chart3_radar.png",
    caption: "用于解释不同改进在精度、召回、定位质量、部署成本之间的取舍。",
  },
  {
    title: "Focaler-IoU 指标变化",
    src: "focaler_chart1_comparison.png",
    caption: "mAP50-95 小幅反超，说明定位精度改善更明显。",
  },
  {
    title: "Focaler-IoU 训练曲线",
    src: "focaler_chart2_training_curve.png",
    caption: "观察训练后期收敛状态，辅助解释 mAP50 与 mAP50-95 的分化。",
  },
  {
    title: "Gold-YOLO GD 对比",
    src: "gold_chart1_comparison.png",
    caption: "复杂结构在当前小数据集与从零训练设置下全面落后。",
  },
  {
    title: "Gold-YOLO 架构示意",
    src: "gold_chart4_architecture.png",
    caption: "展示 A2C2f、SCDown、C2PSA 前移等近似 GD 机制的改动。",
  },
  {
    title: "SAHI 检测数量总览",
    src: "sahi_compare1_summary.png",
    caption: "Focaler-IoU + SAHI 的总检测数为 Baseline + SAHI 的 2.3 倍。",
  },
  {
    title: "SAHI 类别增益",
    src: "sahi_compare2_class.png",
    caption: "限速类和小尺寸标志增幅最明显，符合切片推理对小目标友好的预期。",
  },
  {
    title: "CBAM 训练曲线",
    src: "results_cbam.png",
    caption: "单独加入注意力后整体指标未超过基线，体现预训练不匹配与小数据约束。",
  },
  {
    title: "P2+CBAM 训练曲线",
    src: "results_p2_cbam.png",
    caption: "相比 CBAM，P2 小目标头提升 Recall，但综合 mAP 仍需更长训练和分阶段策略。",
  },
];

function assetUrl(name?: string) {
  return name ? `${API_BASE_URL}/api/assets/detection/${name}` : "";
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function App() {
  const [sceneName, setSceneName] = useState("早高峰快速路");
  const [notes, setNotes] = useState("关注主干道拥堵传播风险");
  const [workflow, setWorkflow] = useState<Workflow>("full-decision");
  const [includeReport, setIncludeReport] = useState(true);
  const [includeVoice, setIncludeVoice] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [activeStage, setActiveStage] = useState<StageKey>("perception");
  const [activeScene, setActiveScene] = useState<SceneKey>("commute");
  const [speechState, setSpeechState] = useState<"idle" | "speaking">("idle");

  const currentStage = stageContent[activeStage];
  const currentScene = sceneContent[activeScene];

  const speechText = useMemo(() => {
    if (!analysis?.decision) {
      return "";
    }

    return [
      `当前场景为${sceneName}。`,
      `风险等级${analysis.decision.risk_level}。`,
      `建议：${analysis.decision.recommendation}`,
      `说明：${analysis.decision.explanation}`,
    ].join("");
  }, [analysis, sceneName]);

  async function fetchTasks() {
    const response = await fetch(`${API_BASE_URL}/api/tasks`);
    if (!response.ok) {
      throw new Error("任务状态获取失败");
    }
    const data = (await response.json()) as TaskRecord[];
    setTasks(data);
  }

  useEffect(() => {
    fetchTasks().catch(() => undefined);
    const timer = window.setInterval(() => {
      fetchTasks().catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze-scene`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_name: sceneName,
          workflow,
          include_report: includeReport,
          include_voice: includeVoice,
          notes,
        }),
      });

      if (!response.ok) {
        throw new Error("分析请求失败");
      }

      const data = (await response.json()) as AnalyzeResponse;
      setAnalysis(data);
      await fetchTasks();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "未知错误");
    } finally {
      setLoading(false);
    }
  }

  function exportJson() {
    if (!analysis) {
      return;
    }
    downloadText(
      `traffic-analysis-${analysis.result_id}.json`,
      JSON.stringify(analysis, null, 2),
      "application/json;charset=utf-8",
    );
  }

  function exportMarkdown() {
    if (!analysis?.decision) {
      return;
    }

    const markdown = [
      `# 智能交通分析结果`,
      ``,
      `- 场景名称: ${sceneName}`,
      `- 工作流: ${analysis.workflow}`,
      `- 结果 ID: ${analysis.result_id}`,
      `- 风险等级: ${analysis.decision.risk_level}`,
      ``,
      `## 决策建议`,
      analysis.decision.recommendation,
      ``,
      `## 说明`,
      analysis.decision.explanation,
      ``,
      `## 事实依据`,
      ...analysis.decision.facts.map((fact) => `- ${fact}`),
      ``,
      `## 检测摘要`,
      `- Precision: ${analysis.detection?.latest_metrics?.precision ?? "-"}`,
      `- Recall: ${analysis.detection?.latest_metrics?.recall ?? "-"}`,
      `- mAP50: ${analysis.detection?.latest_metrics?.mAP50 ?? "-"}`,
      `- mAP50-95: ${analysis.detection?.latest_metrics?.mAP50_95 ?? "-"}`,
    ].join("\n");

    downloadText(`traffic-analysis-${analysis.result_id}.md`, markdown, "text/markdown;charset=utf-8");
  }

  function toggleSpeech() {
    if (!speechText) {
      return;
    }

    if (speechState === "speaking") {
      window.speechSynthesis.cancel();
      setSpeechState("idle");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = "zh-CN";
    utterance.rate = 1;
    utterance.onend = () => setSpeechState("idle");
    utterance.onerror = () => setSpeechState("idle");
    setSpeechState("speaking");
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  return (
    <main className="page">
      <section className="hero hero-upgraded">
        <div className="hero-copy">
          <p className="eyebrow">Intelligent Traffic Management / Demo Version</p>
          <h1>用小模型做感知与预测，用大模型做研判与决策</h1>
          <p className="summary">
            当前 React 前端已经承接课程报告原型结构，并能真实调用 FastAPI 后端、展示实验结果、导出分析结论、进行浏览器语音播报。
          </p>
          <div className="hero-metrics">
            <article className="metric-tile">
              <span>已完成模块</span>
              <strong>2 / 3</strong>
              <p>交通流预测、复杂场景识别</p>
            </article>
            <article className="metric-tile">
              <span>决策闭环</span>
              <strong>5 阶段</strong>
              <p>感知、预测、研判、预警、诱导</p>
            </article>
            <article className="metric-tile">
              <span>检测实验</span>
              <strong>mAP50 0.758</strong>
              <p>exp_C_704_b8_w0_e50 已接入系统</p>
            </article>
          </div>
        </div>

        <aside className="hero-board">
          <div className="board-head">
            <div>
              <p className="eyebrow">Scene Board</p>
              <h2>{currentScene.title}</h2>
            </div>
            <span className="status-pill">{currentScene.badge}</span>
          </div>
          <div className="scene-chips">
            {(Object.keys(sceneContent) as SceneKey[]).map((sceneKey) => (
              <button
                key={sceneKey}
                className={sceneKey === activeScene ? "chip chip-active" : "chip"}
                onClick={() => setActiveScene(sceneKey)}
                type="button"
              >
                {sceneKey === "commute" ? "通勤高峰" : sceneKey === "incident" ? "事故扰动" : "校园路口"}
              </button>
            ))}
          </div>
          <div className="signal-grid">
            <article className="signal-card">
              <span>路网负荷</span>
              <strong>{currentScene.load}</strong>
            </article>
            <article className="signal-card">
              <span>预测拥堵长度</span>
              <strong>{currentScene.queue}</strong>
            </article>
            <article className="signal-card">
              <span>重点目标数量</span>
              <strong>{currentScene.targets}</strong>
            </article>
            <article className="signal-card">
              <span>建议处置</span>
              <strong>{currentScene.action}</strong>
            </article>
          </div>
        </aside>
      </section>

      <section className="grid">
        {apiCards.map((card) => (
          <article key={card.path} className="card">
            <p className="card-path">{card.path}</p>
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </article>
        ))}
      </section>

      <section className="panel narrative-panel">
        <p className="eyebrow">System Narrative</p>
        <h2>课程报告想讲清楚的，不只是模型准确率，而是完整的管理决策闭环</h2>
        <div className="grid narrative-grid">
          <article className="card">
            <p className="card-path">WHY</p>
            <h2>面向管理者的智能交通</h2>
            <p>让预测和识别真正服务于分级预警、诱导发布与辅助管控，而不是停留在算法结果展示。</p>
          </article>
          <article className="card">
            <p className="card-path">HOW</p>
            <h2>大小模型分工协作</h2>
            <p>小模型负责高速、稳定、结构化输出，大模型负责规则理解、态势总结与策略生成。</p>
          </article>
          <article className="card">
            <p className="card-path">VALUE</p>
            <h2>课程项目可演示、可扩展</h2>
            <p>当前先打通分析、展示、导出和播报，后续可以继续接入仿真视频、真实模型和机器狗执行层。</p>
          </article>
        </div>
      </section>

      <section className="panel architecture-panel">
        <p className="eyebrow">Collaborative Architecture</p>
        <h2>从感知到决策的五段式协同架构</h2>
        <div className="stage-grid">
          {(Object.keys(stageContent) as StageKey[]).map((stageKey, index) => (
            <button
              key={stageKey}
              className={stageKey === activeStage ? "stage-card stage-active" : "stage-card"}
              onClick={() => setActiveStage(stageKey)}
              type="button"
            >
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{stageContent[stageKey].title.split("：")[0]}</strong>
              <p>{stageContent[stageKey].owner}</p>
            </button>
          ))}
        </div>
        <div className="result-box stage-detail">
          <strong>{currentStage.title}</strong>
          <p>{currentStage.description}</p>
          <div className="metric-grid">
            <article>
              <span>输入</span>
              <p>{currentStage.input}</p>
            </article>
            <article>
              <span>输出</span>
              <p>{currentStage.output}</p>
            </article>
            <article>
              <span>对管理的意义</span>
              <p>{currentStage.impact}</p>
            </article>
          </div>
        </div>
      </section>

      <section className="panel experiment-panel">
        <p className="eyebrow">Experiment Upgrade</p>
        <h2>实验改进与结果分析：从“提高模型”到“选择可部署策略”</h2>
        <p className="section-lead">
          结合《YOLO11n 改进方法实验总结报告》和网页端演示流程，本模块把改进实验解释成三条可讲述的线：
          结构改进是否有效、损失函数是否提升定位、推理策略是否真正帮助小目标。
        </p>

        <div className="insight-grid">
          {experimentInsights.map((item) => (
            <article key={item.title} className="result-box insight-card">
              <strong>{item.title}</strong>
              <p>{item.body}</p>
            </article>
          ))}
        </div>

        <div className="table-wrap">
          <table className="experiment-table">
            <thead>
              <tr>
                <th>方法</th>
                <th>类型</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>mAP50</th>
                <th>mAP50-95</th>
                <th>网页端讲述结论</th>
              </tr>
            </thead>
            <tbody>
              {improvementRows.map((row) => (
                <tr key={row.method}>
                  <td>
                    <strong>{row.method}</strong>
                  </td>
                  <td>{row.type}</td>
                  <td>{row.precision}</td>
                  <td>{row.recall}</td>
                  <td>{row.map50}</td>
                  <td>{row.map5095}</td>
                  <td>{row.verdict}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="analysis-flow">
          <article className="flow-step">
            <span>01</span>
            <strong>先给强基线</strong>
            <p>YOLO11n 704/50epoch 的 mAP50 为 0.7580，是后续所有改进必须对齐的基准。</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>再讲失败改进</strong>
            <p>CBAM、P2+CBAM、Gold-YOLO GD 没有超过基线，原因集中在预训练不匹配、数据量小和训练不足。</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>最后给推荐组合</strong>
            <p>Focaler-IoU 提升定位质量，SAHI 放大小目标，两者更适合网页 demo 的“真实可用”目标。</p>
          </article>
        </div>

        <div className="chart-gallery">
          {experimentCharts.map((chart) => (
            <figure key={chart.src} className="chart-card">
              <img src={`${chartBase}${chart.src}`} alt={chart.title} />
              <figcaption>
                <strong>{chart.title}</strong>
                <span>{chart.caption}</span>
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="dashboard">
        <article className="panel">
          <p className="eyebrow">Analysis Entry</p>
          <h2>发起一次真实分析请求</h2>
          <form className="form" onSubmit={handleSubmit}>
            <label>
              <span>场景名称</span>
              <input value={sceneName} onChange={(event) => setSceneName(event.target.value)} />
            </label>
            <label>
              <span>工作流</span>
              <select value={workflow} onChange={(event) => setWorkflow(event.target.value as Workflow)}>
                <option value="full-decision">完整决策流</option>
                <option value="prediction-only">仅预测</option>
                <option value="detection-only">仅识别</option>
              </select>
            </label>
            <label className="wide">
              <span>备注</span>
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={includeReport} onChange={() => setIncludeReport((value) => !value)} />
              <span>生成报表任务</span>
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={includeVoice} onChange={() => setIncludeVoice((value) => !value)} />
              <span>生成语音播报任务</span>
            </label>
            <button className="submit" type="submit" disabled={loading}>
              {loading ? "分析中..." : "开始分析"}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </article>

        <article className="panel">
          <p className="eyebrow">Decision Output</p>
          <h2>结构化分析结果</h2>
          {analysis ? (
            <div className="result-stack">
              <p className="badge">result_id: {analysis.result_id}</p>
              <div className="toolbar">
                <button className="secondary-button" onClick={exportJson} type="button">
                  导出 JSON
                </button>
                <button className="secondary-button" onClick={exportMarkdown} type="button">
                  导出 Markdown
                </button>
                <button className="secondary-button" onClick={toggleSpeech} type="button">
                  {speechState === "speaking" ? "停止播报" : "语音播报"}
                </button>
              </div>
              <div className="result-box">
                <strong>风险等级</strong>
                <p>{analysis.decision?.risk_level ?? "暂无"}</p>
              </div>
              <div className="result-box">
                <strong>诱导建议</strong>
                <p>{analysis.decision?.recommendation ?? "暂无"}</p>
              </div>
              <div className="result-box">
                <strong>解释说明</strong>
                <p>{analysis.decision?.explanation ?? "暂无"}</p>
              </div>
              <div className="result-box">
                <strong>事实依据</strong>
                <ul>
                  {analysis.decision?.facts.map((fact) => (
                    <li key={fact}>{fact}</li>
                  )) ?? <li>暂无</li>}
                </ul>
              </div>
              {analysis.forecast ? (
                <div className="result-box">
                  <strong>预测模块摘要</strong>
                  <div className="metric-grid">
                    <article>
                      <span>Baseline MAE</span>
                      <p>{analysis.forecast.baseline?.mae ?? "-"}</p>
                    </article>
                    <article>
                      <span>Baseline RMSE</span>
                      <p>{analysis.forecast.baseline?.rmse ?? "-"}</p>
                    </article>
                    <article>
                      <span>DGL RMSE</span>
                      <p>{analysis.forecast.dgl?.rmse ?? "-"}</p>
                    </article>
                    <article>
                      <span>DGL 推理时间</span>
                      <p>
                        {analysis.forecast.dgl?.inference_time
                          ? `${analysis.forecast.dgl.inference_time.toFixed(2)} s`
                          : "-"}
                      </p>
                    </article>
                  </div>
                </div>
              ) : null}
              {analysis.detection ? (
                <div className="result-box">
                  <strong>识别模块摘要</strong>
                  <div className="metric-grid">
                    <article>
                      <span>类别数</span>
                      <p>{analysis.detection.num_classes}</p>
                    </article>
                    <article>
                      <span>Precision</span>
                      <p>{analysis.detection.latest_metrics?.precision ?? "-"}</p>
                    </article>
                    <article>
                      <span>Recall</span>
                      <p>{analysis.detection.latest_metrics?.recall ?? "-"}</p>
                    </article>
                    <article>
                      <span>mAP50 / mAP50-95</span>
                      <p>
                        {analysis.detection.latest_metrics?.mAP50 ?? "-"} /{" "}
                        {analysis.detection.latest_metrics?.mAP50_95 ?? "-"}
                      </p>
                    </article>
                  </div>
                  <div className="class-list">
                    {analysis.detection.classes.map((name) => (
                      <span key={name} className="class-chip">
                        {name}
                      </span>
                    ))}
                  </div>
                  <div className="asset-grid">
                    <figure className="asset-card">
                      <img src={assetUrl(analysis.detection.preview_assets?.prediction_grid)} alt="检测样例图" />
                      <figcaption>检测样例</figcaption>
                    </figure>
                    <figure className="asset-card">
                      <img
                        src={assetUrl(analysis.detection.preview_assets?.confusion_matrix_normalized)}
                        alt="归一化混淆矩阵"
                      />
                      <figcaption>归一化混淆矩阵</figcaption>
                    </figure>
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="empty">提交分析后，这里会展示结构化决策结果，并支持导出与语音播报。</p>
          )}
        </article>
      </section>

      <section className="panel">
        <p className="eyebrow">Demo Flow</p>
        <h2>课堂演示时，可以按这条线快速讲完整个系统</h2>
        <div className="demo-grid">
          {demoSteps.map((step, index) => (
            <article key={step.title} className="result-box">
              <strong>
                {index + 1}. {step.title}
              </strong>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="task-panel panel">
        <p className="eyebrow">Task Status</p>
        <h2>Hermes / 后台任务状态</h2>
        {tasks.length ? (
          <div className="task-list">
            {tasks
              .slice()
              .reverse()
              .map((task) => (
                <article key={task.task_id} className="task-card">
                  <div className="task-row">
                    <strong>{task.title}</strong>
                    <span className={`state state-${task.state}`}>{task.state}</span>
                  </div>
                  <p>{task.task_type}</p>
                  <p className="task-id">{task.task_id}</p>
                  {task.result?.provider ? <p>provider: {task.result.provider}</p> : null}
                  {task.result?.wsl_distribution ? <p>wsl: {task.result.wsl_distribution}</p> : null}
                  {task.result?.artifact_path ? <p>artifact: {String(task.result.artifact_path)}</p> : null}
                  {typeof task.result?.exit_code === "number" ? <p>exit_code: {task.result.exit_code}</p> : null}
                  {task.result?.message ? <p>{task.result.message}</p> : null}
                  {task.result?.stderr ? <p className="error">{String(task.result.stderr)}</p> : null}
                  {task.result ? <pre>{JSON.stringify(task.result, null, 2)}</pre> : null}
                  {task.error ? <p className="error">{task.error}</p> : null}
                </article>
              ))}
          </div>
        ) : (
          <p className="empty">还没有后台任务，触发报表或语音生成后这里会出现记录。</p>
        )}
      </section>

      <section className="panel">
        <p className="eyebrow">Roadmap</p>
        <h2>下一步继续补齐执行层、导出能力与部署文档</h2>
        <div className="demo-grid">
          <article className="result-box">
            <strong>Now</strong>
            <p>课程原型已迁入 React，分析、导出、播报和任务展示都已进入同一前端。</p>
          </article>
          <article className="result-box">
            <strong>Next</strong>
            <p>继续补充结果导出流程、基础联调测试和最小部署说明。</p>
          </article>
          <article className="result-box">
            <strong>Later</strong>
            <p>接入真实大模型接口、机器狗执行层和 Isaac 仿真验证页面。</p>
          </article>
        </div>
      </section>
    </main>
  );
}
