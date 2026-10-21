import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const labDir = path.resolve(scriptDir, "..");
const rootDir = path.resolve(labDir, "..");
const inputPath = path.join(labDir, "experiment_results.json");
const outputPath = path.join(rootDir, "第七部分实验结果记录表.xlsx");
const previewPath = path.join(labDir, "tools", "第七部分实验结果记录表-preview.png");

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const workbook = Workbook.create();
const sheet = workbook.worksheets.add("第七部分实验结果记录表");
sheet.showGridLines = false;

const headers = ["测试编号", "测试场景", "输入条件", "期望结果", "实际结果", "是否一致", "结果分析"];
const sectionNames = [
  "访问矩阵实验",
  "ACL / DAC 实验",
  "RBAC 实验",
  "MAC 标签控制实验",
  "ABAC 条件策略实验",
  "策略冲突与组合实验",
];
const sectionTitles = [
  "1. 访问矩阵实验",
  "2. ACL / DAC 实验",
  "3. RBAC 实验",
  "4. MAC 标签控制实验",
  "5. ABAC 条件策略实验",
  "6. 策略冲突与组合实验",
];

function a1(row, col) {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  return `${letters[col - 1]}${row}`;
}

function styleTitle(range, color = "#1F4E78") {
  range.format = {
    fill: color,
    font: { bold: true, color: "#FFFFFF", size: 13 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
}

function styleSectionHeader(range) {
  range.format = {
    fill: "#D9EAF7",
    font: { bold: true, color: "#1F2937" },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
}

function styleTableHeader(range) {
  range.format = {
    fill: "#305496",
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
}

function styleBody(range) {
  range.format = {
    verticalAlignment: "center",
    wrapText: true,
  };
}

sheet.getRange("A1:G1").merge();
sheet.getRange("A1").values = [["七、实验结果记录表"]];
styleTitle(sheet.getRange("A1:G1"));
sheet.getRange("A1:G1").format.rowHeightPx = 32;

let row = 3;
let tableIndex = 1;
for (let i = 0; i < sectionNames.length; i += 1) {
  const sectionName = sectionNames[i];
  const rows = payload.results[sectionName];
  sheet.getRange(`A${row}:G${row}`).merge();
  sheet.getRange(`A${row}`).values = [[sectionTitles[i]]];
  styleSectionHeader(sheet.getRange(`A${row}:G${row}`));
  row += 1;

  const values = [
    headers,
    ...rows.map((item) => headers.map((header) => item[header] ?? "")),
  ];
  const rangeAddress = `A${row}:G${row + values.length - 1}`;
  sheet.getRange(rangeAddress).values = values;
  styleTableHeader(sheet.getRange(`A${row}:G${row}`));
  styleBody(sheet.getRange(`A${row + 1}:G${row + values.length - 1}`));
  const table = sheet.tables.add(rangeAddress, true, `ResultTable${tableIndex}`);
  table.style = "TableStyleMedium2";
  table.showFilterButton = false;
  row += values.length + 2;
  tableIndex += 1;
}

sheet.getRange(`A${row}:C${row}`).merge();
sheet.getRange(`A${row}`).values = [["7. 审计日志统计记录"]];
styleSectionHeader(sheet.getRange(`A${row}:C${row}`));
row += 1;

const audit = payload.audit;
const repeatSubjects = Object.entries(audit.repeat_failed_subjects || {})
  .map(([subject, count]) => `${subject}(${count})`)
  .join("、");
const auditRows = [
  ["统计项", "学生填写记录值", "分析说明"],
  ["总请求数", audit.total_requests, "统计所有实验场景产生的访问请求数量。"],
  ["允许请求数", audit.permit_requests, "统计最终结果为 Permit 的请求数量。"],
  ["拒绝请求数", audit.deny_requests, "统计最终结果为 Deny 的请求数量。"],
  ["最常见拒绝原因", audit.most_common_deny_reason, "根据日志中的 reason 字段统计。"],
  ["敏感资源访问次数", audit.sensitive_resource_access_count, "统计 payroll、strategy_doc 等敏感资源相关请求。"],
  ["重复失败主体", repeatSubjects, "统计多次出现拒绝结果的主体。"],
];
const auditRange = `A${row}:C${row + auditRows.length - 1}`;
sheet.getRange(auditRange).values = auditRows;
styleTableHeader(sheet.getRange(`A${row}:C${row}`));
styleBody(sheet.getRange(`A${row + 1}:C${row + auditRows.length - 1}`));
const auditTable = sheet.tables.add(auditRange, true, "AuditSummaryTable");
auditTable.style = "TableStyleMedium2";
auditTable.showFilterButton = false;

sheet.getRange("A1:A120").format.columnWidthPx = 88;
sheet.getRange("B1:B120").format.columnWidthPx = 170;
sheet.getRange("C1:C120").format.columnWidthPx = 330;
sheet.getRange("D1:D120").format.columnWidthPx = 95;
sheet.getRange("E1:E120").format.columnWidthPx = 190;
sheet.getRange("F1:F120").format.columnWidthPx = 76;
sheet.getRange("G1:G120").format.columnWidthPx = 330;
sheet.getRange("A1:G120").format.font = { name: "Microsoft YaHei", size: 10 };
sheet.getRange("A1:G120").format.autofitRows();
sheet.freezePanes.freezeRows(1);

const inspection = await workbook.inspect({
  kind: "table",
  range: "第七部分实验结果记录表!A1:G80",
  include: "values",
  tableMaxRows: 10,
  tableMaxCols: 7,
  maxChars: 5000,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "第七部分实验结果记录表",
  range: "A1:G70",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`Saved ${outputPath}`);
