const scenes = {
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

const stages = {
  perception: {
    owner: "小模型主导",
    title: "场景感知：识别复杂交通参与者与关键异常目标",
    description: "使用轻量视觉模型实时识别车辆、行人、非机动车和异常行为，为后续态势分析提供结构化输入。",
    input: "路口视频流 / 路侧传感器",
    output: "目标类别、位置、冲突风险",
    impact: "支撑异常目标快速发现",
  },
  prediction: {
    owner: "小模型主导",
    title: "流量预测：判断未来时段的路网压力变化",
    description: "基于多尺度历史时序和路网关联关系输出短时与中时段流量趋势，为预警提前量提供支撑。",
    input: "历史流量序列 / 天气与时段特征",
    output: "未来负荷、拥堵长度、波动趋势",
    impact: "支撑预警提前发布",
  },
  assessment: {
    owner: "大模型主导",
    title: "态势研判：把检测结果翻译成管理者可理解的风险解释",
    description: "融合感知结果、预测趋势和业务规则，将多源信息总结为可解释的态势结论和原因归纳。",
    input: "目标事件 + 流量趋势 + 规则知识",
    output: "风险原因、影响范围、事件摘要",
    impact: "支撑值守人员快速判断",
  },
  warning: {
    owner: "大模型主导",
    title: "分级预警：根据态势级别输出对应响应优先级",
    description: "结合研判结果和交通管理预案，生成不同级别的预警建议，帮助明确资源投入强度。",
    input: "态势结论 / 响应预案 / 历史经验",
    output: "预警级别、触发条件、提醒对象",
    impact: "支撑分级响应决策",
  },
  guidance: {
    owner: "大模型 + 执行端协同",
    title: "诱导管控：把决策建议转成面向现场的处置动作",
    description: "将预警结果转化为路侧诱导语句、警力部署建议和后续机器狗执勤任务接口。",
    input: "预警级别 / 处置资源 / 场景约束",
    output: "诱导文案、调度建议、执勤指令",
    impact: "支撑策略落地执行",
  },
};

const demos = {
  observe: {
    kicker: "Step 1",
    title: "观测输入：汇聚视频流、流量序列与事件线索",
    description: "以路口视频、历史流量、突发事件信息为输入，让小模型先产出结构化观察结果，作为大模型推理的事实基础。",
    input: "视频帧、车流时序、事件标签",
    action: "抽取目标、统计流量、筛出异常",
    output: "显示检测框、流量曲线、异常摘要",
  },
  reason: {
    kicker: "Step 2",
    title: "协同研判：大模型把分散信号整合为风险判断",
    description: "把流量预测、目标识别和规则库信息进行汇总，形成面向管理者的可解释态势分析和原因说明。",
    input: "预测结果、识别标签、管理规则",
    action: "归纳风险级别、分析影响范围",
    output: "显示态势摘要、原因解释、建议等级",
  },
  respond: {
    kicker: "Step 3",
    title: "输出策略：给出预警与诱导管控建议",
    description: "根据态势级别输出提示屏文案、调度建议和后续执行入口，形成可展示的课程系统闭环。",
    input: "风险级别、路段状态、处置资源",
    action: "生成诱导文案与辅助调度动作",
    output: "显示路侧提示、人工值守建议、执行端接口",
  },
};

function updateScene(sceneKey) {
  const scene = scenes[sceneKey];
  if (!scene) return;

  document.getElementById("scene-title").textContent = scene.title;
  document.getElementById("scene-badge").textContent = scene.badge;
  document.getElementById("metric-load").textContent = scene.load;
  document.getElementById("metric-queue").textContent = scene.queue;
  document.getElementById("metric-targets").textContent = scene.targets;
  document.getElementById("metric-action").textContent = scene.action;
}

function updateStage(stageKey) {
  const stage = stages[stageKey];
  if (!stage) return;

  document.getElementById("stage-owner").textContent = stage.owner;
  document.getElementById("stage-title").textContent = stage.title;
  document.getElementById("stage-description").textContent = stage.description;
  document.getElementById("stage-input").textContent = stage.input;
  document.getElementById("stage-output").textContent = stage.output;
  document.getElementById("stage-impact").textContent = stage.impact;
}

function updateDemo(demoKey) {
  const demo = demos[demoKey];
  if (!demo) return;

  document.getElementById("demo-kicker").textContent = demo.kicker;
  document.getElementById("demo-title").textContent = demo.title;
  document.getElementById("demo-description").textContent = demo.description;
  document.getElementById("demo-input").textContent = demo.input;
  document.getElementById("demo-action").textContent = demo.action;
  document.getElementById("demo-output").textContent = demo.output;
}

document.querySelectorAll(".scenario-chip").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".scenario-chip").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    updateScene(button.dataset.scene);
  });
});

document.querySelectorAll(".stage-card").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".stage-card").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    updateStage(button.dataset.stage);
  });
});

document.querySelectorAll(".demo-tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".demo-tab").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    updateDemo(button.dataset.demo);
  });
});
