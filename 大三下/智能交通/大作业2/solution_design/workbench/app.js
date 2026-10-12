const state = {
  config: null,
  detection: null,
  forecast: null,
};

const elements = {
  sampleSelect: document.getElementById("sampleSelect"),
  imageInput: document.getElementById("imageInput"),
  samplePreview: document.getElementById("samplePreview"),
  detectButton: document.getElementById("detectButton"),
  forecastSelect: document.getElementById("forecastSelect"),
  forecastButton: document.getElementById("forecastButton"),
  statusBadge: document.getElementById("statusBadge"),
  statusText: document.getElementById("statusText"),
  serviceState: document.getElementById("serviceState"),
  detectState: document.getElementById("detectState"),
  forecastState: document.getElementById("forecastState"),
  defaultCaseLabel: document.getElementById("defaultCaseLabel"),
  defaultHorizonLabel: document.getElementById("defaultHorizonLabel"),
  detectSummaryPill: document.getElementById("detectSummaryPill"),
  detectResultImage: document.getElementById("detectResultImage"),
  detectClassList: document.getElementById("detectClassList"),
  forecastSummaryPill: document.getElementById("forecastSummaryPill"),
  forecastTableBody: document.getElementById("forecastTableBody"),
  fusionRiskLabel: document.getElementById("fusionRiskLabel"),
  fusionSummary: document.getElementById("fusionSummary"),
  fusionDetectionText: document.getElementById("fusionDetectionText"),
  fusionForecastText: document.getElementById("fusionForecastText"),
  aiStatusBadge: document.getElementById("aiStatusBadge"),
  aiFusionText: document.getElementById("aiFusionText"),
};

function setStatus(level, message) {
  elements.statusBadge.textContent = level;
  elements.statusText.textContent = message;
  elements.statusBadge.dataset.level = level;
}

function setMetricGrid(containerId, values) {
  const container = document.getElementById(containerId);
  container.innerHTML = values
    .map(
      (item) => `
        <div class="metric-box">
          <span>${item.label}</span>
          <strong>${item.value}</strong>
        </div>
      `
    )
    .join("");
}

function createOptions(select, options, labelKey, valueKey) {
  select.innerHTML = options
    .map((item) => `<option value="${item[valueKey]}">${item[labelKey]}</option>`)
    .join("");
}

function updatePreviewFromSample() {
  const selected = state.config?.samples.find(
    (item) => item.key === elements.sampleSelect.value
  );
  if (selected) {
    elements.samplePreview.src = selected.url;
    elements.samplePreview.alt = selected.title;
  }
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      const base64 = String(result).split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderDetection(data) {
  state.detection = data;
  elements.detectState.textContent = "已完成";
  elements.detectSummaryPill.textContent = `${data.total_detections} 个目标`;
  elements.detectResultImage.src = data.annotated_image_url || data.input_image_url;
  setMetricGrid("detectMetrics", [
    { label: "目标数量", value: String(data.total_detections) },
    { label: "最高置信度", value: data.max_confidence.toFixed(3) },
    { label: "限制类标志", value: String(data.restriction_signs) },
  ]);

  if (data.class_summary.length === 0) {
    elements.detectClassList.innerHTML = "<li>未检测到明显交通标志目标。</li>";
  } else {
    elements.detectClassList.innerHTML = data.class_summary
      .map(
        (item) =>
          `<li><span>${item.class_name}</span><strong>${item.count} 个</strong></li>`
      )
      .join("");
  }
}

function renderForecast(data) {
  state.forecast = data;
  elements.forecastState.textContent = "已完成";
  elements.forecastSummaryPill.textContent = `${data.dataset_name} / ${data.model_name}`;
  setMetricGrid("forecastMetrics", [
    { label: "MAE", value: data.test_metrics.mae.toFixed(4) },
    { label: "RMSE", value: data.test_metrics.rmse.toFixed(4) },
    { label: "MAPE", value: `${data.test_metrics.mape.toFixed(4)}%` },
  ]);

  elements.forecastTableBody.innerHTML = data.step_results
    .slice(0, 6)
    .map(
      (item) => `
        <tr>
          <td>${item.step}</td>
          <td>${item.rmse.toFixed(3)}</td>
          <td>${item.mae.toFixed(3)}</td>
          <td>${item.mape.toFixed(3)}%</td>
        </tr>
      `
    )
    .join("");
}

function updateFusion() {
  if (!state.detection && !state.forecast) {
    return;
  }

  const detection = state.detection;
  const forecast = state.forecast;
  let risk = "待补全";
  let summary = "请继续运行两个模块。";
  let detectionText = "尚未获得交通标志识别信息。";
  let forecastText = "尚未获得交通流趋势信息。";

  if (detection) {
    const topClasses = detection.class_summary.slice(0, 3).map((item) => item.class_name);
    detectionText =
      detection.total_detections > 0
        ? `当前图片共识别出 ${detection.total_detections} 个交通标志目标，主要类别为 ${topClasses.join("、")}。`
        : "当前图片未检测到明显交通标志目标，场景规则约束信息较弱。";
  }

  if (forecast) {
    forecastText = `预测案例 ${forecast.dataset_name} 的 ${forecast.horizon_steps} 步结果呈现${forecast.trend_summary}，整体 MAE 为 ${forecast.test_metrics.mae.toFixed(2)}。`;
  }

  if (detection && forecast) {
    console.log("[Fusion] Both results available, calling AI...");
    const strictScene = detection.restriction_signs >= 2 || detection.total_detections >= 5;
    const upwardTraffic = forecast.risk_level === "中高" || forecast.risk_level === "高";

    if (strictScene && upwardTraffic) {
      risk = "中高风险";
    } else if (upwardTraffic) {
      risk = "中等风险";
    } else if (strictScene) {
      risk = "中等风险";
    } else {
      risk = "低风险";
    }

    elements.fusionRiskLabel.textContent = risk;
    elements.fusionSummary.textContent = "AI 正在生成态势研判结论…";
    elements.fusionDetectionText.textContent = detectionText;
    elements.fusionForecastText.textContent = forecastText;

    console.log("[Fusion] aiStatusBadge:", elements.aiStatusBadge);
    console.log("[Fusion] aiFusionText:", elements.aiFusionText);
    generateAIFusion(detection, forecast);
    return;
  } else if (detection) {
    risk = detection.restriction_signs > 0 ? "待补全" : "低风险";
    summary = "已获得识别结果，但尚未叠加交通流预测信息，当前结论仍不完整。";
  } else if (forecast) {
    risk = forecast.risk_level;
    summary = "已获得交通流预测结果，但尚未叠加交通场景识别信息，当前结论偏趋势分析。";
  }

  elements.fusionRiskLabel.textContent = risk;
  elements.fusionSummary.textContent = summary;
  elements.fusionDetectionText.textContent = detectionText;
  elements.fusionForecastText.textContent = forecastText;
}

async function generateAIFusion(detection, forecast) {
  console.log("[AI] generateAIFusion called");
  elements.aiStatusBadge.textContent = "生成中";
  elements.aiStatusBadge.className = "pill";
  elements.aiFusionText.textContent = "AI 正在分析交通态势…";

  try {
    console.log("[AI] Sending request to /api/fusion");
    const response = await fetch("/api/fusion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ detection, forecast }),
    });
    console.log("[AI] Response status:", response.status);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "AI 融合分析调用失败。");
    }
    const data = await response.json();
    console.log("[AI] Got result:", data.analysis?.substring(0, 50));
    elements.aiStatusBadge.textContent = "已生成";
    elements.aiStatusBadge.className = "pill pill-ok";
    elements.aiFusionText.textContent = data.analysis;
  } catch (error) {
    console.error("[AI] Error:", error);
    elements.aiStatusBadge.textContent = "失败";
    elements.aiStatusBadge.className = "pill pill-muted";
    elements.aiFusionText.textContent = `AI 生成失败：${error.message}`;
  }
}

async function loadConfig() {
  setStatus("连接中", "正在连接本地桥接服务并加载双模型配置。");
  const response = await fetch("/api/config");
  if (!response.ok) {
    throw new Error("无法连接本地桥接服务。");
  }
  const config = await response.json();
  state.config = config;
  createOptions(elements.sampleSelect, config.samples, "title", "key");
  createOptions(elements.forecastSelect, config.forecast_cases, "title", "key");
  elements.defaultCaseLabel.textContent = config.default_forecast_case;
  elements.defaultHorizonLabel.textContent = String(config.default_horizon_steps);
  elements.serviceState.textContent = "在线";
  updatePreviewFromSample();
  setStatus("就绪", "桥接服务已连接，可以分别运行识别和预测。");
}

async function runDetection() {
  elements.detectState.textContent = "运行中";
  setStatus("运行中", "正在调用 YOLO11n 执行交通目标识别。");

  const payload = {
    sampleKey: elements.sampleSelect.value,
  };
  const file = elements.imageInput.files[0];
  if (file) {
    payload.filename = file.name;
    payload.imageData = await readFileAsBase64(file);
  }

  const response = await fetch("/api/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "识别接口调用失败。");
  }
  const data = await response.json();
  renderDetection(data);
  updateFusion();
  setStatus("完成", "交通目标识别已完成，结果已回显到工作台。");
}

async function runForecast() {
  elements.forecastState.textContent = "运行中";
  setStatus("运行中", "正在读取 STAEformer 交通流预测结果。");

  const response = await fetch("/api/forecast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caseKey: elements.forecastSelect.value }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "预测接口调用失败。");
  }
  const data = await response.json();
  renderForecast(data);
  updateFusion();
  setStatus("完成", "交通流预测结果已加载，态势分析已更新。");
}

async function bootstrap() {
  try {
    await loadConfig();
  } catch (error) {
    elements.serviceState.textContent = "离线";
    setStatus("失败", error.message);
  }
}

elements.sampleSelect.addEventListener("change", updatePreviewFromSample);
elements.detectButton.addEventListener("click", async () => {
  try {
    await runDetection();
  } catch (error) {
    elements.detectState.textContent = "失败";
    setStatus("失败", error.message);
  }
});

elements.forecastButton.addEventListener("click", async () => {
  try {
    await runForecast();
  } catch (error) {
    elements.forecastState.textContent = "失败";
    setStatus("失败", error.message);
  }
});

bootstrap();
