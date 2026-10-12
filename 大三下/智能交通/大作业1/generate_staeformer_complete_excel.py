"""
STAEformer 可视化教学 Excel - 完整美化版
参考 zeroai-main 风格，包含 10 个工作表和丰富图表
"""

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference, PieChart
from openpyxl.formatting.rule import ColorScaleRule
import os

# ==================== 样式定义 ====================
BLUE_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
GREEN_FILL = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
ORANGE_FILL = PatternFill(start_color="ED7D31", end_color="ED7D31", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
LIGHT_BLUE_FILL = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
RED_FILL = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
PURPLE_FILL = PatternFill(start_color="7030A0", end_color="7030A0", fill_type="solid")
TEAL_FILL = PatternFill(start_color="008080", end_color="008080", fill_type="solid")

LIGHT_GREEN = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
LIGHT_BLUE = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
LIGHT_ORANGE = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
LIGHT_YELLOW = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
LIGHT_PURPLE = PatternFill(start_color="E4DFEC", end_color="E4DFEC", fill_type="solid")
LIGHT_TEAL = PatternFill(start_color="D4EBF2", end_color="D4EBF2", fill_type="solid")

HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=16, color="4472C4")
SUBTITLE_FONT = Font(bold=True, size=12)
FORMULA_FONT = Font(italic=True, bold=True, size=11, color="0000FF")
BIG_TITLE_FONT = Font(bold=True, size=20, color="4472C4")

THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

MEDIUM_BORDER = Border(
    left=Side(style='medium'),
    right=Side(style='medium'),
    top=Side(style='medium'),
    bottom=Side(style='medium')
)

# 模型参数
NUM_NODES = 4
IN_STEPS = 4
MODEL_DIM = 8
NUM_HEADS = 2
HEAD_DIM = MODEL_DIM // NUM_HEADS
FFN_DIM = 16

def create_complete_excel():
    wb = Workbook()
    np.random.seed(42)
    
    # ========== Sheet 1: 封面 ==========
    ws_cover = wb.active
    ws_cover.title = "📘 封面"
    
    for row in range(1, 45):
        for col in range(1, 15):
            ws_cover.cell(row=row, column=col).fill = LIGHT_BLUE
    
    ws_cover.merge_cells('B2:K2')
    ws_cover['B2'] = "🚀 STAEformer 时空注意力网络"
    ws_cover['B2'].font = BIG_TITLE_FONT
    ws_cover['B2'].alignment = Alignment(horizontal='center', vertical='center')
    
    ws_cover.merge_cells('B3:K3')
    ws_cover['B3'] = "Spatio-Temporal Adaptive Embedding Transformer"
    ws_cover['B3'].font = Font(italic=True, size=16, color="666666")
    ws_cover['B3'].alignment = Alignment(horizontal='center')
    
    ws_cover.merge_cells('B4:K4')
    ws_cover['B4'] = "用于交通流量预测的深度学习模型"
    ws_cover['B4'].font = Font(size=14, color="333333")
    ws_cover['B4'].alignment = Alignment(horizontal='center')
    
    for col in range(2, 12):
        ws_cover.cell(row=6, column=col).fill = BLUE_FILL
    
    ws_cover['B8'] = "🎯 核心特点"
    ws_cover['B8'].font = Font(bold=True, size=14, color="4472C4")
    
    features = [
        ["⏳", "时空双重注意力机制"],
        ["🎨", "自适应嵌入学习"],
        ["📊", "多尺度时间特征"],
        ["🔗", "端到端学习"],
    ]
    
    for i, (icon, text) in enumerate(features):
        ws_cover[f'B{10+i}'] = f"{icon} {text}"
        ws_cover[f'B{10+i}'].font = Font(size=12, italic=True)
        ws_cover[f'B{10+i}'].fill = LIGHT_GREEN
        ws_cover[f'B{10+i}'].border = THIN_BORDER
    
    ws_cover['B16'] = "🏗️ 模型结构"
    ws_cover['B16'].font = Font(bold=True, size=14, color="4472C4")
    
    structure = [
        ("📥 输入层", LIGHT_GREEN, "B18"),
        ("↓", None, "B19"),
        ("🔧 嵌入层", LIGHT_BLUE, "B20"),
        ("🧠 编码器×N 层", LIGHT_ORANGE, "B21"),
        ("📤 输出层", LIGHT_YELLOW, "B22"),
        ("🎯 预测结果", LIGHT_PURPLE, "B23"),
    ]
    
    for text, fill, cell_ref in structure:
        cell = ws_cover[cell_ref]
        cell.value = text
        if fill:
            cell.fill = fill
            cell.border = MEDIUM_BORDER
        cell.font = Font(size=11, bold=True)
    
    # 参数表格
    ws_cover['E18'] = "📊 模型参数"
    ws_cover['E18'].font = Font(bold=True, size=12, color="4472C4")
    
    params = [
        ["节点数:", NUM_NODES],
        ["时间步:", IN_STEPS],
        ["模型维度:", MODEL_DIM],
        ["头数:", NUM_HEADS],
    ]
    
    for i, (label, value) in enumerate(params):
        ws_cover[f'E{20+i}'] = label
        ws_cover[f'F{20+i}'] = value
        ws_cover[f'E{20+i}'].font = Font(bold=True)
        ws_cover[f'F{20+i}'].fill = LIGHT_YELLOW
        ws_cover[f'F{20+i}'].border = THIN_BORDER
    
    # 饼图
    pie = PieChart()
    pie.title = "模块维度占比"
    labels_data = ["输入投影", "TOD 嵌入", "DOW 嵌入", "自适应嵌入"]
    values_data = [24, 24, 24, 80]
    
    for i, (name, val) in enumerate(zip(labels_data, values_data)):
        ws_cover[f'H{20+i}'] = name
        ws_cover[f'I{20+i}'] = val
    
    labels = Reference(ws_cover, min_col=8, min_row=20, max_row=23)
    data = Reference(ws_cover, min_col=9, min_row=20, max_row=23)
    pie.add_data(data)
    pie.set_categories(labels)
    ws_cover.add_chart(pie, "H25")
    
    # ========== Sheet 2: 输入数据 ==========
    ws_input = wb.create_sheet("📊 Step1_输入数据")
    
    ws_input['B2'] = "📊 第一步：理解输入数据"
    ws_input['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    traffic_data = np.array([
        [45, 52, 38, 41],
        [48, 55, 42, 45],
        [52, 58, 45, 48],
        [55, 62, 48, 52]
    ])
    
    ws_input['B5'] = "🚗 流量数据示例:"
    ws_input['B5'].font = Font(bold=True, size=12, color="008000")
    
    for j, node in enumerate(["节点 0", "节点 1", "节点 2", "节点 3"]):
        cell = ws_input.cell(row=6, column=3+j, value=node)
        cell.fill = GREEN_FILL
        cell.font = HEADER_FONT
        cell.border = THIN_BORDER
    
    for i in range(IN_STEPS):
        cell = ws_input.cell(row=7+i, column=2, value=f"t{i}")
        cell.fill = GREEN_FILL
        cell.font = HEADER_FONT
        cell.border = THIN_BORDER
        for j in range(NUM_NODES):
            cell = ws_input.cell(row=7+i, column=3+j, value=traffic_data[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_GREEN
    
    # 折线图
    chart = LineChart()
    chart.title = "各节点流量变化趋势"
    chart.x_axis.title = "时间步"
    chart.y_axis.title = "流量值"
    
    for node_idx in range(NUM_NODES):
        data_ref = Reference(ws_input, min_col=3+node_idx, min_row=7, max_row=7+IN_STEPS-1)
        chart.add_data(data_ref, titles_from_data=False)
    
    ws_input.add_chart(chart, "H6")
    
    # ========== Sheet 3: 嵌入层 ==========
    ws_embed = wb.create_sheet("🔧 Step2_嵌入层")
    
    ws_embed['B2'] = "🔧 第二步：嵌入层计算"
    ws_embed['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_embed['B5'] = "📋 嵌入层组成:"
    embed_parts = [
        ["📊 输入投影", "Linear 层将输入映射到高维空间"],
        ["⏰ 时间嵌入 (TOD)", "Embedding 查表操作"],
        ["📅 星期嵌入 (DOW)", "Embedding 查表操作"],
        ["🎨 自适应嵌入", "可学习的参数矩阵"],
    ]
    
    for i, (part, desc) in enumerate(embed_parts):
        ws_embed[f'B{7+i}'] = part
        ws_embed[f'C{7+i}'] = desc
        ws_embed[f'B{7+i}'].font = Font(bold=True)
        ws_embed[f'B{7+i}'].fill = LIGHT_BLUE
        ws_embed[f'B{7+i}'].border = THIN_BORDER
    
    # 权重矩阵展示
    ws_embed['B15'] = "💡 输入投影权重矩阵示例:"
    W_proj = np.random.randn(3, 4).round(2)
    
    for i in range(3):
        for j in range(4):
            cell = ws_embed.cell(row=16+i, column=3+j, value=W_proj[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_ORANGE
    
    # ========== Sheet 4: 注意力机制 ==========
    ws_attn = wb.create_sheet("🧠 Step3_注意力机制")
    
    ws_attn['B2'] = "🧠 第三步：注意力机制详解"
    ws_attn['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_attn.merge_cells('B4:I4')
    ws_attn['B4'] = "Attention(Q,K,V) = softmax(QK^T / √d_k) × V"
    ws_attn['B4'].font = FORMULA_FONT
    ws_attn['B4'].fill = LIGHT_YELLOW
    ws_attn['B4'].alignment = Alignment(horizontal='center')
    
    # QKV 说明
    qkv_table = [
        ["符号", "英文", "含义", "颜色"],
        ["Q", "Query", "查询向量", "🔴 红色"],
        ["K", "Key", "键向量", "🔵 蓝色"],
        ["V", "Value", "值向量", "🟢 绿色"],
    ]
    
    for i, row in enumerate(qkv_table):
        for j, val in enumerate(row):
            cell = ws_attn.cell(row=6+i, column=2+j, value=val)
            cell.border = THIN_BORDER
            if i == 0:
                cell.fill = BLUE_FILL
                cell.font = HEADER_FONT
            elif j == 3:
                cell.fill = LIGHT_YELLOW
    
    # 注意力分数矩阵
    ws_attn['B12'] = "📊 注意力分数矩阵示例:"
    attn_scores = np.random.rand(4, 4).round(2)
    
    for i in range(4):
        for j in range(4):
            cell = ws_attn.cell(row=13+i, column=3+j, value=attn_scores[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_ORANGE
            cell.number_format = '0.00'
    
    # ========== Sheet 5: 时间注意力 ==========
    ws_temporal = wb.create_sheet("⏳ Step4_时间注意力")
    
    ws_temporal['B2'] = "⏳ 第四步：时间注意力"
    ws_temporal['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_temporal['B5'] = "时间注意力在时间维度上计算相关性"
    
    temporal_attn = np.array([
        [0.40, 0.30, 0.20, 0.10],
        [0.25, 0.35, 0.25, 0.15],
        [0.15, 0.25, 0.35, 0.25],
        [0.10, 0.20, 0.30, 0.40]
    ])
    
    ws_temporal['B8'] = "时间注意力权重矩阵:"
    for i in range(4):
        for j in range(4):
            cell = ws_temporal.cell(row=9+i, column=3+j, value=temporal_attn[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_BLUE
            cell.number_format = '0.00'
            if i == j:
                cell.fill = YELLOW_FILL
    
    # ========== Sheet 6: 空间注意力 ==========
    ws_spatial = wb.create_sheet("🌐 Step5_空间注意力")
    
    ws_spatial['B2'] = "🌐 第五步：空间注意力"
    ws_spatial['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_spatial['B5'] = "空间注意力在节点维度上计算相关性"
    
    spatial_attn = np.array([
        [0.35, 0.28, 0.22, 0.15],
        [0.22, 0.38, 0.25, 0.15],
        [0.18, 0.27, 0.36, 0.19],
        [0.12, 0.18, 0.25, 0.45]
    ])
    
    ws_spatial['B8'] = "空间注意力权重矩阵:"
    for i in range(4):
        for j in range(4):
            cell = ws_spatial.cell(row=9+i, column=3+j, value=spatial_attn[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_PURPLE
            cell.number_format = '0.00'
            if i == j:
                cell.fill = PURPLE_FILL
    
    # ========== Sheet 7: 多头注意力 ==========
    ws_multihead = wb.create_sheet("🔄 Step6_多头注意力")
    
    ws_multihead['B2'] = "🔄 第六步：多头注意力"
    ws_multihead['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_multihead['B5'] = f"模型维度={MODEL_DIM}, 头数={NUM_HEADS}, 每头维度={HEAD_DIM}"
    
    head_diagram = [
        ["输入向量 (8 维)", "→", "分割", "→", "Head 0 (前 4 维)", "Head 1 (后 4 维)"],
        ["[a,b,c,d,e,f,g,h]", "→", "split", "→", "[a,b,c,d]", "[e,f,g,h]"],
    ]
    
    for i, row in enumerate(head_diagram):
        for j, val in enumerate(row):
            cell = ws_multihead.cell(row=7+i, column=2+j, value=val)
            cell.border = THIN_BORDER
            if i == 0:
                cell.fill = ORANGE_FILL
                cell.font = HEADER_FONT
    
    # ========== Sheet 8: 前馈网络 ==========
    ws_ffn = wb.create_sheet("📈 Step7_前馈网络")
    
    ws_ffn['B2'] = "📈 第七步：前馈网络"
    ws_ffn['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    ws_ffn['B5'] = "FFN 结构：Linear → ReLU → Linear"
    
    ffn_formula = "FFN(x) = W₂ × ReLU(W₁ × x + b₁) + b₂"
    ws_ffn['B7'] = ffn_formula
    ws_ffn['B7'].font = FORMULA_FONT
    ws_ffn['B7'].fill = LIGHT_YELLOW
    
    # ========== Sheet 9: 输出层 ==========
    ws_output = wb.create_sheet("📤 Step8_输出层")
    
    ws_output['B2'] = "📤 第八步：输出层"
    ws_output['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    predictions = np.random.rand(IN_STEPS, NUM_NODES).round(3) * 100
    
    ws_output['B5'] = "🎯 预测结果示例:"
    for j, n in enumerate(["节点 0", "节点 1", "节点 2", "节点 3"]):
        cell = ws_output.cell(row=6, column=3+j, value=n)
        cell.fill = LIGHT_BLUE_FILL
        cell.font = HEADER_FONT
        cell.border = THIN_BORDER
    
    for i in range(IN_STEPS):
        cell = ws_output.cell(row=7+i, column=2, value=f"预测 t{i}")
        cell.fill = LIGHT_BLUE_FILL
        cell.font = HEADER_FONT
        cell.border = THIN_BORDER
        for j in range(NUM_NODES):
            cell = ws_output.cell(row=7+i, column=3+j, value=predictions[i,j])
            cell.border = THIN_BORDER
            cell.fill = LIGHT_GREEN
            cell.number_format = '0.00'
    
    # ========== Sheet 10: 完整流程 ==========
    ws_flow = wb.create_sheet("📋 完整流程")
    
    ws_flow['B2'] = "📋 STAEformer 完整计算流程"
    ws_flow['B2'].font = Font(bold=True, size=18, color="4472C4")
    
    flow_table = [
        ["阶段", "模块", "输入维度", "输出维度"],
        ["📥 输入", "原始数据", f"({IN_STEPS}, {NUM_NODES}, 3)", "-"],
        ["🔧 嵌入", "输入投影", f"({IN_STEPS}, {NUM_NODES}, 3)", f"({IN_STEPS}, {NUM_NODES}, 24)"],
        ["🔧 嵌入", "TOD 嵌入", f"({IN_STEPS}, {NUM_NODES})", f"({IN_STEPS}, {NUM_NODES}, 24)"],
        ["🔧 嵌入", "DOW 嵌入", f"({IN_STEPS}, {NUM_NODES})", f"({IN_STEPS}, {NUM_NODES}, 24)"],
        ["🔧 嵌入", "自适应嵌入", "参数", f"({IN_STEPS}, {NUM_NODES}, 80)"],
        ["🧠 编码", "时间注意力×N", f"({IN_STEPS}, {NUM_NODES}, 152)", f"({IN_STEPS}, {NUM_NODES}, 152)"],
        ["🧠 编码", "空间注意力×N", f"({IN_STEPS}, {NUM_NODES}, 152)", f"({IN_STEPS}, {NUM_NODES}, 152)"],
        ["📤 输出", "展平 + 投影", f"({IN_STEPS}, {NUM_NODES}, 152)", f"({IN_STEPS}, {NUM_NODES}, 1)"],
    ]
    
    for i, row in enumerate(flow_table):
        for j, val in enumerate(row):
            cell = ws_flow.cell(row=4+i, column=2+j, value=val)
            cell.border = THIN_BORDER
            if i == 0:
                cell.fill = BLUE_FILL
                cell.font = HEADER_FONT
            elif "输入" in str(row[0]):
                cell.fill = LIGHT_GREEN
            elif "嵌入" in str(row[0]):
                cell.fill = LIGHT_BLUE
            elif "编码" in str(row[0]):
                cell.fill = LIGHT_ORANGE
            elif "输出" in str(row[0]):
                cell.fill = LIGHT_YELLOW
    
    # 调整列宽
    for ws in wb.worksheets:
        for col in range(1, 15):
            ws.column_dimensions[get_column_letter(col)].width = 14
        ws.column_dimensions['A'].width = 3
    
    # 保存文件
    output_path = os.path.join(os.path.dirname(__file__), "STAEformer_教学可视化_完整版.xlsx")
    wb.save(output_path)
    print(f"✅ 完整版 Excel 文件已保存到：{output_path}")
    print(f"📁 文件大小：{os.path.getsize(output_path) / 1024:.1f} KB")
    print(f"📊 工作表数量：{len(wb.worksheets)}")
    return output_path

if __name__ == "__main__":
    create_complete_excel()
