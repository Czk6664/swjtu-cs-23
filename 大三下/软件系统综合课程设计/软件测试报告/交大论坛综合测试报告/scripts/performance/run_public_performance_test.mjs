import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const root = path.resolve("../../");
const backend = path.join(root, "jiaodaluntan", "backend");
const jar = path.join(backend, "target", "forum-1.0.0.jar");
const port = Number(process.env.PERF_PORT || 18081);
const baseUrl = `http://127.0.0.1:${port}/api`;

const javaArgs = [
  "-jar",
  jar,
  "--spring.profiles.active=demo",
  `--server.port=${port}`,
  "--spring.datasource.url=jdbc:h2:mem:swjtu_perf;MODE=MySQL;DATABASE_TO_LOWER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=TRUE;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE",
  "--demo.seed.enabled=true",
  "--demo.seed.run-on-demo-profile=true",
];

const app = spawn("java", javaArgs, {
  cwd: backend,
  stdio: ["ignore", "ignore", "ignore"],
  windowsHide: true,
});

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function probe() {
  try {
    const response = await fetch(`${baseUrl}/posts?page=0&size=1`, {
      signal: AbortSignal.timeout(2000),
    });
    return response.status < 500;
  } catch {
    return false;
  }
}

function percentile(sorted, p) {
  if (!sorted.length) return 0;
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(sorted.length - 1, index))];
}

function summarize(name, type, endpointLabel, records, durationMs, concurrency, extra = {}) {
  const ok = records.filter((record) => record.ok);
  const errors = records.length - ok.length;
  const times = ok.map((record) => record.ms).sort((a, b) => a - b);
  const avg = times.reduce((sum, value) => sum + value, 0) / (times.length || 1);
  return {
    name,
    type,
    endpointLabel,
    concurrency,
    durationMs,
    total: records.length,
    success: ok.length,
    errors,
    errorRate: records.length ? errors / records.length : 0,
    throughput: records.length / (durationMs / 1000),
    avg,
    p50: percentile(times, 50),
    p90: percentile(times, 90),
    p95: percentile(times, 95),
    p99: percentile(times, 99),
    max: times[times.length - 1] || 0,
    ...extra,
  };
}

async function oneRequest(url) {
  const start = performance.now();
  try {
    const response = await fetch(baseUrl + url, {
      signal: AbortSignal.timeout(5000),
    });
    await response.arrayBuffer();
    return { ok: response.ok, status: response.status, ms: performance.now() - start };
  } catch (error) {
    return { ok: false, status: 0, ms: performance.now() - start, error: String(error.message || error) };
  }
}

async function runFixed(name, type, urls, concurrency, seconds, extra = {}) {
  const endAt = Date.now() + seconds * 1000;
  const records = [];
  let index = 0;
  async function worker() {
    while (Date.now() < endAt) {
      records.push(await oneRequest(urls[index++ % urls.length]));
    }
  }
  const start = Date.now();
  await Promise.all(Array.from({ length: concurrency }, worker));
  return summarize(name, type, urls.join(" | "), records, Date.now() - start, concurrency, extra);
}

async function main() {
  let started = false;
  for (let i = 0; i < 90; i += 1) {
    if (await probe()) {
      started = true;
      break;
    }
    await sleep(1000);
  }
  if (!started) {
    app.kill();
    throw new Error("Backend did not start in 90 seconds");
  }

  const mix = [
    "/posts?page=0&size=20",
    "/posts/hot?page=0&size=20",
    "/posts/search?keyword=测试&page=0&size=20",
    "/sections?page=0&size=20",
  ];

  const results = [];
  results.push(await runFixed("LOAD-01 常规混合浏览负载", "负载测试", mix, 8, 12, { phase: "baseline" }));
  for (const concurrency of [8, 16, 32, 48]) {
    results.push(await runFixed(
      `STRESS-${concurrency} 并发阶梯`,
      "压力测试",
      ["/posts/search?keyword=测试&page=0&size=20", "/posts?page=0&size=20"],
      concurrency,
      6,
      { level: concurrency },
    ));
  }
  for (const pageSize of [10, 20, 50, 100]) {
    results.push(await runFixed(
      `CAP-${pageSize} 分页容量`,
      "容量测试",
      [`/posts?page=0&size=${pageSize}`, `/posts/search?keyword=测试&page=0&size=${pageSize}`],
      12,
      5,
      { pageSize },
    ));
  }
  results.push(await runFixed("STAB-01 短时持续混合访问", "稳定性测试", mix, 10, 20, { phase: "short-soak" }));

  app.kill();

  const payload = {
    meta: {
      generatedAt: new Date().toISOString(),
      baseUrl,
      host: {
        platform: os.platform(),
        release: os.release(),
        cpus: os.cpus().length,
        totalMemGiB: Number((os.totalmem() / 1024 / 1024 / 1024).toFixed(2)),
      },
      serverInfoFromUser: {
        publicIp: "47.108.218.39",
        privateIp: "172.19.41.159",
        os: "Ubuntu 22.04",
        cpu: "2 核",
        memory: "2 GiB",
        disk: "40 GiB",
        bandwidth: "200 Mbps",
        region: "西南1（成都）",
      },
    },
    results,
  };

  fs.writeFileSync("performance_results.json", JSON.stringify(payload, null, 2), "utf8");
  const csv = [
    "name,type,concurrency,total,success,errors,errorRate,throughput,avg,p50,p90,p95,p99,max,endpointLabel",
    ...results.map((r) => [
      r.name,
      r.type,
      r.concurrency,
      r.total,
      r.success,
      r.errors,
      r.errorRate.toFixed(4),
      r.throughput.toFixed(2),
      r.avg.toFixed(2),
      r.p50.toFixed(2),
      r.p90.toFixed(2),
      r.p95.toFixed(2),
      r.p99.toFixed(2),
      r.max.toFixed(2),
      `"${r.endpointLabel.replaceAll('"', '""')}"`,
    ].join(",")),
  ];
  fs.writeFileSync("performance_results.csv", csv.join("\n"), "utf8");
  console.log(`Wrote ${results.length} performance result rows.`);
}

main().catch((error) => {
  app.kill();
  console.error(error);
  process.exitCode = 1;
});
