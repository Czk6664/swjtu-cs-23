"""
STAEformer 嵌入层详解 - 多页PPT
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def blue_cmap():
    return LinearSegmentedColormap.from_list('blue', ['#E3F2FD', '#1565C0', '#0D47A1'])

def save_multi_page_pdf():
    pages = []
    
    # ========== Page 1: 总览 ==========
    fig1, ax1 = plt.subplots(figsize=(11, 8.5))
    ax1.set_xlim(0, 11)
    ax1.set_ylim(0, 8.5)
    ax1.axis('off')
    fig1.patch.set_facecolor('white')
    
    ax1.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#2F5496', edgecolor='none'))
    ax1.text(5.5, 7.85, 'STAEformer 嵌入层结构总览', fontsize=22, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax1.text(0.8, 6.8, '输入数据', fontsize=14, fontweight='bold', color='#424242')
    ax1.add_patch(patches.Rectangle((0.8, 5.8), 3.5, 0.8, facecolor='#FFF3E0', edgecolor='#BDBDBD', linewidth=1))
    ax1.text(2.55, 6.2, 'x: (batch, 12, 207, 3)', fontsize=11, ha='center', va='center', color='#212121')
    ax1.text(0.8, 5.5, 'Traffic Flow + TOD + DOW', fontsize=9, color='#757575')
    
    ax1.annotate('', xy=(2.55, 5.3), xytext=(2.55, 5.8), 
                arrowprops=dict(arrowstyle='->', color='#757575', lw=2))
    
    branch_y = 4.0
    branch_info = [
        ('Input Projection', 'Linear(3→24)', '#FFC000', 0.8),
        ('TOD Embedding', 'Embedding(288→24)', '#70AD47', 3.1),
        ('DOW Embedding', 'Embedding(7→24)', '#7030A0', 5.4),
        ('Adaptive Embedding', 'nn.Parameter', '#C55A11', 7.7),
    ]
    
    for name, detail, color, x in branch_info:
        ax1.add_patch(patches.FancyBboxPatch((x, branch_y), 2.0, 1.2,
                       boxstyle="round,pad=0.05", facecolor=color, edgecolor='none'))
        ax1.text(x+1.0, branch_y+0.8, name, fontsize=10, fontweight='bold', 
                color='white', ha='center', va='center')
        ax1.text(x+1.0, branch_y+0.35, detail, fontsize=8, 
                color='white', ha='center', va='center')
        ax1.annotate('', xy=(x+1.0, 4.0), xytext=(x+1.0, 5.3),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    ax1.annotate('', xy=(5.5, 2.8), xytext=(2.55, 4.0),
                arrowprops=dict(arrowstyle='->', color='#757575', lw=2))
    
    ax1.add_patch(patches.Rectangle((3.5, 2.3), 4.0, 0.8, facecolor='#2F5496', edgecolor='none'))
    ax1.text(5.5, 2.7, 'Concat + 维度变换', fontsize=12, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax1.annotate('', xy=(5.5, 1.8), xytext=(5.5, 2.3),
                arrowprops=dict(arrowstyle='->', color='#2F5496', lw=2))
    
    ax1.add_patch(patches.Rectangle((3.0, 0.8), 5.0, 0.8, facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2))
    ax1.text(5.5, 1.2, '输出: (batch, 12, 207, 152)', fontsize=12, 
            color='#1565C0', ha='center', va='center', fontweight='bold')
    
    ax1.text(0.8, 1.2, 'model_dim = 24 + 24 + 24 + 80 = 152', fontsize=10, color='#616161')
    
    pages.append(fig1)
    
    # ========== Page 2: Input Projection ==========
    fig2, ax2 = plt.subplots(figsize=(11, 8.5))
    ax2.set_xlim(0, 11)
    ax2.set_ylim(0, 8.5)
    ax2.axis('off')
    fig2.patch.set_facecolor('white')
    
    ax2.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#FFC000', edgecolor='none'))
    ax2.text(5.5, 7.85, '1. Input Projection（输入投影）', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax2.text(0.8, 6.8, '作用', fontsize=14, fontweight='bold', color='#424242')
    ax2.text(0.8, 6.4, '将原始流量特征从3维映射到24维空间', fontsize=11, color='#616161')
    ax2.text(0.8, 5.9, '公式: output = Linear(3, 24)(input)', fontsize=11, color='#757575', family='monospace')
    
    ax2.add_patch(patches.Rectangle((0.8, 4.5), 3.5, 1.2, facecolor='#FFF3E0', edgecolor='#BDBDBD', linewidth=1))
    ax2.text(2.55, 5.2, '输入: (12, 207, 3)', fontsize=11, ha='center', va='center', color='#212121')
    ax2.text(2.55, 4.75, 'flow=25.0, TOD=0.04, DOW=3', fontsize=9, ha='center', va='center', color='#757575')
    
    ax2.annotate('', xy=(2.55, 4.0), xytext=(2.55, 4.5),
                arrowprops=dict(arrowstyle='->', color='#FFC000', lw=2))
    
    ax2.add_patch(patches.Rectangle((1.3, 2.3), 2.5, 1.5, facecolor='#FFC000', edgecolor='none'))
    ax2.text(2.55, 3.3, 'Linear(3→24)', fontsize=14, fontweight='bold', color='white', ha='center', va='center')
    ax2.text(2.55, 2.7, '矩阵乘法+偏置', fontsize=10, color='white', ha='center', va='center')
    
    ax2.annotate('', xy=(2.55, 1.8), xytext=(2.55, 2.3),
                arrowprops=dict(arrowstyle='->', color='#FFC000', lw=2))
    
    ax2.add_patch(patches.Rectangle((0.8, 0.8), 3.5, 0.8, facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=1))
    ax2.text(2.55, 1.2, '输出: (12, 207, 24)', fontsize=11, ha='center', va='center', color='#1565C0', fontweight='bold')
    
    # 示例计算
    ax2.add_patch(patches.Rectangle((5.5, 4.0), 5.0, 3.5, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax2.text(6.0, 7.0, '示例计算', fontsize=14, fontweight='bold', color='#424242')
    ax2.text(6.0, 6.3, '输入: [25.0, 0.04, 3]', fontsize=10, color='#616161', family='monospace')
    ax2.text(6.0, 5.7, 'W: (3×24) 权重矩阵', fontsize=10, color='#616161', family='monospace')
    ax2.text(6.0, 5.1, 'b: (24,) 偏置向量', fontsize=10, color='#616161', family='monospace')
    ax2.text(6.0, 4.5, '计算: input×W + b', fontsize=10, color='#757575', family='monospace')
    ax2.text(6.0, 4.0, '     = [25.0, 0.04, 3] × W + b', fontsize=9, color='#757575', family='monospace')
    
    pages.append(fig2)
    
    # ========== Page 3: TOD Embedding ==========
    fig3, ax3 = plt.subplots(figsize=(11, 8.5))
    ax3.set_xlim(0, 11)
    ax3.set_ylim(0, 8.5)
    ax3.axis('off')
    fig3.patch.set_facecolor('white')
    
    ax3.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#70AD47', edgecolor='none'))
    ax3.text(5.5, 7.85, '2. TOD Embedding（时间 embedding）', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax3.text(0.8, 6.8, '作用', fontsize=14, fontweight='bold', color='#424242')
    ax3.text(0.8, 6.4, '将一天内的时间位置编码为24维向量', fontsize=11, color='#616161')
    ax3.text(0.8, 5.9, '公式: Embedding(288, 24)(floor(TOD×288))', fontsize=11, color='#757575', family='monospace')
    
    # 左侧流程
    ax3.add_patch(patches.Rectangle((0.8, 5.0), 2.5, 0.8, facecolor='#E8F5E9', edgecolor='#BDBDBD', linewidth=1))
    ax3.text(2.05, 5.4, 'TOD: 0.04', fontsize=11, ha='center', va='center', color='#212121')
    ax3.text(2.05, 5.0, '(凌晨约11分钟)', fontsize=9, ha='center', va='center', color='#757575')
    
    ax3.annotate('', xy=(2.05, 4.3), xytext=(2.05, 5.0),
                arrowprops=dict(arrowstyle='->', color='#70AD47', lw=2))
    
    ax3.add_patch(patches.Rectangle((0.8, 3.5), 2.5, 0.7, facecolor='#C8E6C9', edgecolor='#BDBDBD', linewidth=1))
    ax3.text(2.05, 3.9, 'floor(0.04×288) = 11', fontsize=10, ha='center', va='center', color='#2E7D32')
    
    ax3.annotate('', xy=(2.05, 2.8), xytext=(2.05, 3.5),
                arrowprops=dict(arrowstyle='->', color='#70AD47', lw=2))
    
    ax3.add_patch(patches.Rectangle((0.8, 1.8), 2.5, 0.8, facecolor='#A5D6A7', edgecolor='#BDBDBD', linewidth=1))
    ax3.text(2.05, 2.2, 'Embedding查表', fontsize=11, ha='center', va='center', color='#1B5E20')
    
    ax3.annotate('', xy=(2.05, 1.3), xytext=(2.05, 1.8),
                arrowprops=dict(arrowstyle='->', color='#70AD47', lw=2))
    
    ax3.add_patch(patches.Rectangle((0.8, 0.5), 2.5, 0.7, facecolor='#81C784', edgecolor='#BDBDBD', linewidth=1))
    ax3.text(2.05, 0.85, '输出: (24,) 向量', fontsize=11, ha='center', va='center', color='#1B5E20', fontweight='bold')
    
    # Embedding表
    ax3.text(4.5, 6.8, 'Embedding 表 (前几行)', fontsize=14, fontweight='bold', color='#424242')
    tod_table = np.array([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5], [0.4, 0.5, 0.6], [0.5, 0.6, 0.7]])
    im3 = ax3.imshow(tod_table, cmap=blue_cmap(), aspect='auto', extent=[4.5, 7.5, 4.5, 6.5])
    ax3.set_xticks([0, 1, 2])
    ax3.set_xticklabels(['dim0', 'dim1', 'dim2'], fontsize=9)
    ax3.set_yticks([0, 1, 2, 3, 4])
    ax3.set_yticklabels(['0:00', '~2h', '~4h', '~6h', '~8h'], fontsize=9)
    for i in range(5):
        for j in range(3):
            ax3.text(j+4.5, i+4.5, f'{tod_table[i,j]:.1f}', ha='center', va='center', 
                    fontsize=9, color='white' if tod_table[i,j] > 0.4 else 'black')
    
    # 特点
    ax3.add_patch(patches.Rectangle((8.0, 4.0), 2.5, 3.5, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax3.text(8.5, 7.0, '特点', fontsize=14, fontweight='bold', color='#424242')
    ax3.text(8.2, 6.3, '• 查表操作', fontsize=10, color='#616161')
    ax3.text(8.2, 5.7, '  无需矩阵乘法', fontsize=9, color='#757575')
    ax3.text(8.2, 5.1, '• 相近时间有', fontsize=10, color='#616161')
    ax3.text(8.2, 4.7, '  相似的表示', fontsize=9, color='#757575')
    ax3.text(8.2, 4.1, '• 288个时间槽', fontsize=10, color='#616161')
    ax3.text(8.2, 3.7, '  每5分钟一槽', fontsize=9, color='#757575')
    
    pages.append(fig3)
    
    # ========== Page 4: DOW Embedding ==========
    fig4, ax4 = plt.subplots(figsize=(11, 8.5))
    ax4.set_xlim(0, 11)
    ax4.set_ylim(0, 8.5)
    ax4.axis('off')
    fig4.patch.set_facecolor('white')
    
    ax4.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#7030A0', edgecolor='none'))
    ax4.text(5.5, 7.85, '3. DOW Embedding（星期 embedding）', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax4.text(0.8, 6.8, '作用', fontsize=14, fontweight='bold', color='#424242')
    ax4.text(0.8, 6.4, '将星期几编码为24维向量，区分工作日与周末', fontsize=11, color='#616161')
    ax4.text(0.8, 5.9, '公式: Embedding(7, 24)(DOW)', fontsize=11, color='#757575', family='monospace')
    
    # 左侧流程
    ax4.add_patch(patches.Rectangle((0.8, 5.0), 2.5, 0.8, facecolor='#F3E5F5', edgecolor='#BDBDBD', linewidth=1))
    ax4.text(2.05, 5.4, 'DOW: 3', fontsize=11, ha='center', va='center', color='#212121')
    ax4.text(2.05, 5.0, '(周三)', fontsize=9, ha='center', va='center', color='#757575')
    
    ax4.annotate('', xy=(2.05, 4.3), xytext=(2.05, 5.0),
                arrowprops=dict(arrowstyle='->', color='#7030A0', lw=2))
    
    ax4.add_patch(patches.Rectangle((0.8, 3.5), 2.5, 0.7, facecolor='#E1BEE7', edgecolor='#BDBDBD', linewidth=1))
    ax4.text(2.05, 3.9, 'index = 3 (直接使用)', fontsize=10, ha='center', va='center', color='#7B1FA2')
    
    ax4.annotate('', xy=(2.05, 2.8), xytext=(2.05, 3.5),
                arrowprops=dict(arrowstyle='->', color='#7030A0', lw=2))
    
    ax4.add_patch(patches.Rectangle((0.8, 1.8), 2.5, 0.8, facecolor='#CE93D8', edgecolor='#BDBDBD', linewidth=1))
    ax4.text(2.05, 2.2, 'Embedding查表', fontsize=11, ha='center', va='center', color='white')
    
    ax4.annotate('', xy=(2.05, 1.3), xytext=(2.05, 1.8),
                arrowprops=dict(arrowstyle='->', color='#7030A0', lw=2))
    
    ax4.add_patch(patches.Rectangle((0.8, 0.5), 2.5, 0.7, facecolor='#AB47BC', edgecolor='#BDBDBD', linewidth=1))
    ax4.text(2.05, 0.85, '输出: (24,) 向量', fontsize=11, ha='center', va='center', color='white', fontweight='bold')
    
    # Embedding表
    ax4.text(4.5, 6.8, 'Embedding 表 (7×3)', fontsize=14, fontweight='bold', color='#424242')
    dow_table = np.array([[0.1, 0.2, 0.3], [0.2, 0.1, 0.4], [0.3, 0.2, 0.5], 
                          [0.4, 0.3, 0.6], [0.5, 0.4, 0.7], [0.6, 0.5, 0.8], [0.7, 0.6, 0.9]])
    im4 = ax4.imshow(dow_table, cmap=blue_cmap(), aspect='auto', extent=[4.5, 7.5, 4.0, 6.5])
    ax4.set_xticks([0, 1, 2])
    ax4.set_xticklabels(['dim0', 'dim1', 'dim2'], fontsize=9)
    ax4.set_yticks([0, 1, 2, 3, 4, 5, 6])
    ax4.set_yticklabels(['周一', '周二', '周三', '周四', '周五', '周六', '周日'], fontsize=9)
    for i in range(7):
        for j in range(3):
            ax4.text(j+4.5, i+4.0, f'{dow_table[i,j]:.1f}', ha='center', va='center', 
                    fontsize=9, color='white' if dow_table[i,j] > 0.4 else 'black')
    
    # 特点
    ax4.add_patch(patches.Rectangle((8.0, 4.0), 2.5, 3.5, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax4.text(8.5, 7.0, '特点', fontsize=14, fontweight='bold', color='#424242')
    ax4.text(8.2, 6.3, '• 查表操作', fontsize=10, color='#616161')
    ax4.text(8.2, 5.7, '  7个类别', fontsize=9, color='#757575')
    ax4.text(8.2, 5.1, '• 工作日/周末', fontsize=10, color='#616161')
    ax4.text(8.2, 4.7, '  模式可区分', fontsize=9, color='#757575')
    ax4.text(8.2, 4.1, '• 节假日可通过', fontsize=10, color='#616161')
    ax4.text(8.2, 3.7, '  特殊编码处理', fontsize=9, color='#757575')
    
    pages.append(fig4)
    
    # ========== Page 5: Adaptive Embedding ==========
    fig5, ax5 = plt.subplots(figsize=(11, 8.5))
    ax5.set_xlim(0, 11)
    ax5.set_ylim(0, 8.5)
    ax5.axis('off')
    fig5.patch.set_facecolor('white')
    
    ax5.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#C55A11', edgecolor='none'))
    ax5.text(5.5, 7.85, '4. Adaptive Embedding（可学习嵌入）', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax5.text(0.8, 6.8, '作用', fontsize=14, fontweight='bold', color='#424242')
    ax5.text(0.8, 6.4, '可学习的位置特征，捕获数据特有的时空模式', fontsize=11, color='#616161')
    ax5.text(0.8, 5.9, '形式: nn.Parameter(in_steps × num_nodes × 80)', fontsize=11, color='#757575', family='monospace')
    
    # 参数规模
    ax5.add_patch(patches.Rectangle((0.8, 4.8), 4.0, 1.5, facecolor='#FBE9E7', edgecolor='#BDBDBD', linewidth=1))
    ax5.text(2.8, 5.9, '参数规模', fontsize=14, fontweight='bold', color='#424242')
    ax5.text(2.8, 5.3, '12 × 207 × 80 = 198,720', fontsize=12, color='#C55A11', family='monospace', fontweight='bold')
    ax5.text(2.8, 4.9, '≈ 0.2M 可学习参数', fontsize=10, color='#757575')
    
    # 可视化
    ax5.text(0.8, 4.3, '参数矩阵示意（简化）', fontsize=12, fontweight='bold', color='#424242')
    adp_vis = np.random.rand(6, 8)
    im5 = ax5.imshow(adp_vis, cmap=blue_cmap(), aspect='auto', extent=[0.8, 4.0, 1.5, 3.8], vmin=0, vmax=1)
    ax5.text(2.4, 1.2, '行: 时间步(t=1~12)  列: 节点(n=1~207)', fontsize=8, ha='center', color='#757575')
    ax5.text(4.5, 2.65, '深色=大值\n浅色=小值', fontsize=9, ha='left', va='center', color='#616161')
    
    # 特点
    ax5.add_patch(patches.Rectangle((5.5, 4.0), 5.0, 3.5, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax5.text(8.0, 7.0, '特点', fontsize=14, fontweight='bold', color='#424242')
    ax5.text(5.8, 6.3, '• 无需预定义，完全数据驱动', fontsize=10, color='#616161')
    ax5.text(5.8, 5.7, '• 自动捕获隐式时空模式', fontsize=10, color='#616161')
    ax5.text(5.8, 5.1, '• Xavier均匀分布初始化', fontsize=10, color='#616161')
    ax5.text(5.8, 4.5, '• 每个(时间步, 节点)对', fontsize=10, color='#616161')
    ax5.text(5.8, 4.1, '  都有独特的特征向量', fontsize=9, color='#757575')
    
    pages.append(fig5)
    
    # ========== Page 6: 特征拼接 ==========
    fig6, ax6 = plt.subplots(figsize=(11, 8.5))
    ax6.set_xlim(0, 11)
    ax6.set_ylim(0, 8.5)
    ax6.axis('off')
    fig6.patch.set_facecolor('white')
    
    ax6.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#2F5496', edgecolor='none'))
    ax6.text(5.5, 7.85, '5. 特征拼接（Concatenation）', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax6.text(0.8, 6.8, '作用', fontsize=14, fontweight='bold', color='#424242')
    ax6.text(0.8, 6.4, '将四个嵌入层输出在最后一维拼接', fontsize=11, color='#616161')
    ax6.text(0.8, 5.9, '公式: x_concat = cat([input, tod, dow, adp], dim=-1)', fontsize=11, color='#757575', family='monospace')
    
    # 四个输入
    boxes = [
        ('Input\n(12,207,24)', '#FFC000', 0.8),
        ('TOD\n(12,207,24)', '#70AD47', 2.6),
        ('DOW\n(12,207,24)', '#7030A0', 4.4),
        ('Adaptive\n(12,207,80)', '#C55A11', 6.2),
    ]
    
    for text, color, x in boxes:
        ax6.add_patch(patches.FancyBboxPatch((x, 4.5), 1.5, 1.2,
                       boxstyle="round,pad=0.05", facecolor=color, edgecolor='none'))
        ax6.text(x+0.75, 5.1, text, fontsize=10, fontweight='bold', 
                color='white', ha='center', va='center')
        ax6.annotate('', xy=(5.5, 4.5), xytext=(x+0.75, 4.5),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    ax6.add_patch(patches.Rectangle((4.0, 3.3), 3.0, 1.0, facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2))
    ax6.text(5.5, 3.9, 'Concat (dim=-1)', fontsize=12, fontweight='bold', color='#1565C0', ha='center', va='center')
    ax6.annotate('', xy=(5.5, 3.3), xytext=(5.5, 4.5),
                arrowprops=dict(arrowstyle='->', color='#2F5496', lw=2))
    
    ax6.add_patch(patches.Rectangle((3.5, 2.0), 4.0, 1.0, facecolor='#2F5496', edgecolor='none'))
    ax6.text(5.5, 2.6, '(batch, 12, 207, 152)', fontsize=13, fontweight='bold', 
            color='white', ha='center', va='center')
    ax6.text(5.5, 2.15, 'model_dim = 152', fontsize=11, color='white', ha='center', va='center')
    
    # 维度分解
    ax6.add_patch(patches.Rectangle((8.0, 3.0), 2.5, 3.0, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax6.text(8.5, 5.5, '维度分解', fontsize=14, fontweight='bold', color='#424242')
    ax6.text(8.2, 4.9, 'model_dim', fontsize=10, color='#616161')
    ax6.text(8.2, 4.4, '= 24 + 24 + 24 + 80', fontsize=10, color='#757575', family='monospace')
    ax6.text(8.2, 3.9, '= 152', fontsize=11, color='#1565C0', family='monospace', fontweight='bold')
    
    pages.append(fig6)
    
    # ========== Page 7: 完整示例 ==========
    fig7, ax7 = plt.subplots(figsize=(11, 8.5))
    ax7.set_xlim(0, 11)
    ax7.set_ylim(0, 8.5)
    ax7.axis('off')
    fig7.patch.set_facecolor('white')
    
    ax7.add_patch(patches.Rectangle((0.5, 7.5), 10, 0.7, facecolor='#2F5496', edgecolor='none'))
    ax7.text(5.5, 7.85, '6. 完整前向传播示例', fontsize=20, fontweight='bold', 
            color='white', ha='center', va='center')
    
    ax7.text(0.5, 6.9, '假设: batch_size=1, in_steps=4, num_nodes=3（简化示例）', fontsize=11, color='#616161')
    
    # 数据流图
    steps = [
        ('输入\n(4,3,3)', '#FFF3E0', 0.8, 5.5),
        ('Proj\n(4,3,24)', '#FFC000', 0.8, 4.3),
        ('TOD Emb\n(4,3,24)', '#70AD47', 2.6, 4.3),
        ('DOW Emb\n(4,3,24)', '#7030A0', 4.4, 4.3),
        ('Adp Emb\n(4,3,80)', '#C55A11', 6.2, 4.3),
        ('Concat\n(4,3,152)', '#E3F2FD', 3.5, 2.5),
    ]
    
    for text, color, x, y in steps:
        ax7.add_patch(patches.FancyBboxPatch((x, y), 1.5, 0.9,
                       boxstyle="round,pad=0.05", facecolor=color, edgecolor='#BDBDBD', linewidth=1))
        ax7.text(x+0.75, y+0.45, text, fontsize=8, fontweight='bold', 
                color='#212121' if color != '#E3F2FD' else '#1565C0', 
                ha='center', va='center')
    
    # 箭头
    ax7.annotate('', xy=(1.55, 4.3), xytext=(1.55, 5.5), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))
    
    for x in [1.55, 3.35, 5.15, 6.95]:
        ax7.annotate('', xy=(5.5, 4.5), xytext=(x, 4.3),
                    arrowprops=dict(arrowstyle='->', color='#757575', lw=1))
    
    ax7.annotate('', xy=(5.5, 2.5), xytext=(5.5, 4.3),
                arrowprops=dict(arrowstyle='->', color='#2F5496', lw=2))
    
    # 计算总结
    ax7.add_patch(patches.Rectangle((0.5, 0.5), 10.0, 1.7, facecolor='#F5F5F5', edgecolor='#BDBDBD', linewidth=1))
    ax7.text(0.8, 1.9, '计算流程总结', fontsize=14, fontweight='bold', color='#424242')
    ax7.text(0.8, 1.4, '1. x: (4,3,3) → Input Projection → (4,3,24)', fontsize=10, color='#616161', family='monospace')
    ax7.text(0.8, 1.0, '2. TOD: (4,3) → Embedding → (4,3,24)', fontsize=10, color='#616161', family='monospace')
    ax7.text(0.8, 0.6, '3. DOW: (4,3) → Embedding → (4,3,24)', fontsize=10, color='#616161', family='monospace')
    ax7.text(5.5, 1.4, '4. Adaptive: (4,3,80) 直接可学习参数', fontsize=10, color='#616161', family='monospace')
    ax7.text(5.5, 1.0, '5. Concat: cat([...], dim=-1) → (4,3,152)', fontsize=10, color='#1565C0', family='monospace', fontweight='bold')
    ax7.text(5.5, 0.6, '6. 进入 Transformer 层进行时空建模', fontsize=10, color='#616161', family='monospace')
    
    pages.append(fig7)
    
    # 保存PDF
    with PdfPages(r'D:\大三下\智能交通\STAEformer_嵌入层详解.pdf') as pdf:
        for fig in pages:
            pdf.savefig(fig, bbox_inches='tight', facecolor='white')
            plt.close(fig)
    
    print('PDF已保存: D:\\大三下\\智能交通\\STAEformer_嵌入层详解.pdf')
    print(f'共 {len(pages)} 页')

if __name__ == '__main__':
    save_multi_page_pdf()
