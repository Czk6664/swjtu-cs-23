"""
STAEformer Embedding Layer Visualization - Academic Style
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def blue_cmap():
    return LinearSegmentedColormap.from_list('blue', ['#E3F2FD', '#1565C0', '#0D47A1'])

def draw_tensor(ax, data, x, y, width, height, label='', cmap=None):
    if cmap is None:
        cmap = blue_cmap()
    if len(data.shape) == 1:
        data = data.reshape(1, -1)
    
    rows, cols = data.shape
    im = ax.imshow(data, cmap=cmap, aspect='auto', extent=[x, x+width, y, y+height])
    
    for i in range(rows):
        for j in range(cols):
            val = data[i, j]
            if isinstance(val, (int, float)):
                text = f'{val:.1f}' if abs(val) < 100 else f'{val:.0f}'
            else:
                text = str(val)
            ax.text(x + width*(j+0.5)/cols, y + height*(i+0.5)/rows, text,
                   ha='center', va='center', fontsize=6, color='black')
    
    ax.add_patch(patches.Rectangle((x, y), width, height, 
                   fill=False, edgecolor='#9E9E9E', linewidth=1))
    
    if label:
        ax.text(x + width/2, y + height + 0.15, label, ha='center', va='bottom', 
               fontsize=8, fontweight='bold', color='#424242')
    
    return im

def draw_box(ax, x, y, width, height, text, color='#E3F2FD', text_color='#212121'):
    ax.add_patch(patches.FancyBboxPatch((x, y), width, height,
                   boxstyle="round,pad=0.02,rounding_size=0.1",
                   facecolor=color, edgecolor='#BDBDBD', linewidth=1))
    ax.text(x + width/2, y + height/2, text, ha='center', va='center',
           fontsize=7, color=text_color, fontweight='bold')

fig = plt.figure(figsize=(16, 20))
fig.suptitle('STAEformer Embedding Layer Structure', fontsize=18, fontweight='bold', color='#424242', y=0.98)

ax1 = fig.add_subplot(3, 2, 1)
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 6)
ax1.set_title('1. Input Projection', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax1.axis('off')

ax1.text(0.5, 5.3, 'Purpose: Map raw features from 3D to 24D', fontsize=10, color='#616161')
ax1.text(0.5, 5.0, 'Formula: output = Linear(3, 24)(input)', fontsize=9, color='#757575', family='monospace')

draw_box(ax1, 0.5, 3.5, 2.5, 1.2, 'x: (12, 207, 3)\nflow+TOD+DOW', '#FFF3E0', '#212121')
draw_box(ax1, 0.8, 1.8, 1.9, 1.0, 'Linear(3->24)', '#BBDEFB', '#1565C0')
draw_box(ax1, 0.5, 0.3, 2.5, 1.0, 'h: (12, 207, 24)\n24D features', '#E3F2FD', '#1565C0')

ax1.annotate('', xy=(1.75, 2.8), xytext=(1.75, 3.5), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))
ax1.annotate('', xy=(1.75, 1.8), xytext=(1.75, 2.8), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))

ax1.text(4.0, 5.3, 'Example:', fontsize=10, fontweight='bold', color='#424242')
ax1.text(4.0, 4.8, 'Input: [25.0, 0.04, 3]', fontsize=9, color='#616161', family='monospace')
ax1.text(4.0, 4.4, 'W: (3x24 weight matrix)', fontsize=9, color='#616161', family='monospace')
ax1.text(4.0, 4.0, 'b: (24D bias)', fontsize=9, color='#616161', family='monospace')
ax1.text(4.0, 3.5, '25*W[:,0] + 0.04*W[:,1] + 3*W[:,2] + b', fontsize=8, color='#757575', family='monospace')
ax1.text(4.0, 3.0, '-> [12.6, 8.3, 15.2, ...]', fontsize=9, color='#1565C0', family='monospace')

ax1.text(4.0, 2.2, 'Characteristics:', fontsize=10, fontweight='bold', color='#424242')
ax1.text(4.0, 1.8, '- Linear transformation', fontsize=9, color='#616161')
ax1.text(4.0, 1.4, '- Project to feature space', fontsize=9, color='#616161')
ax1.text(4.0, 1.0, '- Independent weights per feature', fontsize=9, color='#616161')

ax2 = fig.add_subplot(3, 2, 2)
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 6)
ax2.set_title('2. TOD Embedding (Time-of-Day)', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax2.axis('off')

ax2.text(0.5, 5.3, 'Purpose: Encode time of day to 24D vector', fontsize=10, color='#616161')
ax2.text(0.5, 5.0, 'Formula: Embedding(288,24)(floor(TOD*288))', fontsize=9, color='#757575', family='monospace')

draw_box(ax2, 0.5, 3.5, 2.0, 0.8, 'TOD: 0.04\n(~11 min)', '#E8F5E9', '#212121')
draw_box(ax2, 0.5, 2.0, 2.0, 0.8, 'floor(0.04*288)\n= 11', '#C8E6C9', '#2E7D32')
draw_box(ax2, 0.5, 0.5, 2.0, 0.8, 'emb: (24,)\nTime features', '#A5D6A7', '#1B5E20')

ax2.annotate('', xy=(1.5, 2.8), xytext=(1.5, 3.5), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))
ax2.annotate('', xy=(1.5, 1.3), xytext=(1.5, 2.0), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))

tod_table = np.array([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
ax2.text(3.5, 5.3, 'Embedding Table (first rows):', fontsize=10, fontweight='bold', color='#424242')
im2 = ax2.imshow(tod_table, cmap=blue_cmap(), aspect='auto')
ax2.set_xticks([0, 1, 2])
ax2.set_xticklabels(['dim0', 'dim1', 'dim2'], fontsize=8)
ax2.set_yticks([0, 1, 2, 3])
ax2.set_yticklabels(['idx:0', 'idx:72', 'idx:144', 'idx:215'], fontsize=8)
for i in range(4):
    for j in range(3):
        ax2.text(j, i, f'{tod_table[i,j]:.1f}', ha='center', va='center', fontsize=8, color='white' if tod_table[i,j] > 0.5 else 'black')

ax2.text(3.5, 2.5, 'Characteristics:', fontsize=10, fontweight='bold', color='#424242')
ax2.text(3.5, 2.0, '- Lookup operation (no matmul)', fontsize=9, color='#616161')
ax2.text(3.5, 1.6, '- Similar times -> similar repr', fontsize=9, color='#616161')
ax2.text(3.5, 1.2, '- 288 slots, 5-min interval', fontsize=9, color='#616161')

ax3 = fig.add_subplot(3, 2, 3)
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 6)
ax3.set_title('3. DOW Embedding (Day-of-Week)', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax3.axis('off')

ax3.text(0.5, 5.3, 'Purpose: Encode day of week to 24D', fontsize=10, color='#616161')
ax3.text(0.5, 5.0, 'Formula: Embedding(7, 24)(DOW)', fontsize=9, color='#757575', family='monospace')

draw_box(ax3, 0.5, 3.5, 2.0, 0.8, 'DOW: 3\n(Wed)', '#FFF8E1', '#212121')
draw_box(ax3, 0.5, 2.0, 2.0, 0.8, 'index = 3\n(direct)', '#FFE0B2', '#E65100')
draw_box(ax3, 0.5, 0.5, 2.0, 0.8, 'emb: (24,)\nWeekday features', '#FFCC80', '#E65100')

ax3.annotate('', xy=(1.5, 2.8), xytext=(1.5, 3.5), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))
ax3.annotate('', xy=(1.5, 1.3), xytext=(1.5, 2.0), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))

dow_table = np.array([[0.1, 0.2, 0.3], [0.2, 0.1, 0.4], [0.3, 0.2, 0.5], 
                      [0.4, 0.3, 0.6], [0.5, 0.4, 0.7], [0.6, 0.5, 0.8], [0.7, 0.6, 0.9]])
ax3.text(3.5, 5.3, 'Embedding Table (7x3):', fontsize=10, fontweight='bold', color='#424242')
im3 = ax3.imshow(dow_table, cmap=blue_cmap(), aspect='auto')
ax3.set_xticks([0, 1, 2])
ax3.set_xticklabels(['dim0', 'dim1', 'dim2'], fontsize=8)
ax3.set_yticks([0, 1, 2, 3, 4, 5, 6])
ax3.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], fontsize=8)
for i in range(7):
    for j in range(3):
        ax3.text(j, i, f'{dow_table[i,j]:.1f}', ha='center', va='center', fontsize=8, color='white' if dow_table[i,j] > 0.5 else 'black')

ax3.text(3.5, 2.5, 'Characteristics:', fontsize=10, fontweight='bold', color='#424242')
ax3.text(3.5, 2.0, '- Lookup operation, 7 categories', fontsize=9, color='#616161')
ax3.text(3.5, 1.6, '- Weekday/weekend pattern', fontsize=9, color='#616161')
ax3.text(3.5, 1.2, '- Holidays via special encoding', fontsize=9, color='#616161')

ax4 = fig.add_subplot(3, 2, 4)
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 6)
ax4.set_title('4. Adaptive Embedding (Learnable)', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax4.axis('off')

ax4.text(0.5, 5.3, 'Purpose: Learnable position features', fontsize=10, color='#616161')
ax4.text(0.5, 5.0, 'Form: nn.Parameter(In_steps x Num_nodes x 80)', fontsize=9, color='#757575', family='monospace')

draw_box(ax4, 0.5, 3.3, 3.0, 1.0, 'Shape: (12, 207, 80)\nLearnable param matrix', '#F3E5F5', '#7B1FA2')

ax4.text(0.5, 2.2, 'Schematic (simplified):', fontsize=10, fontweight='bold', color='#424242')
adp_vis = np.random.rand(4, 6)
adp_vis = (adp_vis - adp_vis.min()) / (adp_vis.max() - adp_vis.min()) * 0.8 + 0.1
im4 = ax4.imshow(adp_vis, cmap=blue_cmap(), aspect='auto', 
                  extent=[0.5, 3.5, 0.5, 2.0], vmin=0, vmax=1)
ax4.text(2.0, 0.2, 'Row: time step(t=1~12)  Col: node(n=1~207)', ha='center', fontsize=8, color='#616161')
ax4.text(4.2, 1.25, 'Dark=high\nLight=low', ha='left', va='center', fontsize=8, color='#616161')

ax4.text(5.0, 5.3, 'Param scale:', fontsize=10, fontweight='bold', color='#424242')
ax4.text(5.0, 4.9, '12 x 207 x 80 = 198,720', fontsize=11, color='#1565C0', family='monospace')
ax4.text(5.0, 4.4, '~0.2M learnable params', fontsize=9, color='#616161')

ax4.text(5.0, 3.5, 'Characteristics:', fontsize=10, fontweight='bold', color='#424242')
ax4.text(5.0, 3.0, '- Data-driven, no predefined', fontsize=9, color='#616161')
ax4.text(5.0, 2.6, '- Capture implicit patterns', fontsize=9, color='#616161')
ax4.text(5.0, 2.2, '- Xavier init', fontsize=9, color='#616161')
ax4.text(5.0, 1.8, '- Unique vector per (t, node)', fontsize=9, color='#616161')

ax5 = fig.add_subplot(3, 2, 5)
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 7)
ax5.set_title('5. Feature Concatenation', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax5.axis('off')

ax5.text(0.5, 6.5, 'Concatenate 4 embeddings along last dimension', fontsize=10, color='#616161')
ax5.text(0.5, 6.2, 'x_concat = cat([input, tod, dow, adp], dim=-1)', fontsize=9, color='#757575', family='monospace')

draw_box(ax5, 0.5, 5.0, 1.5, 0.8, 'Input\n(12,207,24)', '#BBDEFB', '#1565C0')
draw_box(ax5, 2.2, 5.0, 1.5, 0.8, 'TOD\n(12,207,24)', '#C8E6C9', '#2E7D32')
draw_box(ax5, 3.9, 5.0, 1.5, 0.8, 'DOW\n(12,207,24)', '#FFCC80', '#E65100')
draw_box(ax5, 5.6, 5.0, 1.5, 0.8, 'Adp\n(12,207,80)', '#E1BEE7', '#7B1FA2')

for x in [1.25, 2.95, 4.65, 6.35]:
    ax5.annotate('', xy=(6.8, 5.4), xytext=(x, 5.4), arrowprops=dict(arrowstyle='->', color='#9E9E9E', lw=1))

draw_box(ax5, 6.8, 4.8, 2.5, 1.2, 'Concat\ndim=-1', '#E3F2FD', '#1565C0')
draw_box(ax5, 6.8, 3.3, 2.5, 0.8, '(12, 207, 152)\nmodel_dim=152', '#1565C0', 'white')
ax5.annotate('', xy=(8.05, 4.8), xytext=(8.05, 4.1), arrowprops=dict(arrowstyle='->', color='#757575', lw=1.5))

ax5.text(0.5, 2.8, 'Dimension Calculation:', fontsize=11, fontweight='bold', color='#424242')
dims_text = '''model_dim = 24 + 24 + 24 + 80 = 152

- Input Projection: 24D
- TOD Embedding:    24D  
- DOW Embedding:    24D
- Adaptive Embed:   80D'''
ax5.text(0.5, 2.3, dims_text, fontsize=9, color='#424242', family='monospace')

ax5.text(5.0, 2.8, 'Concat Demo (one t, one node):', fontsize=10, fontweight='bold', color='#424242')
concat_demo = np.array([[0.8], [0.6], [0.7], [0.5], [0.9], [0.3], [0.4], [0.2], 
                        [0.1], [0.2], [0.3], [0.1], [0.2], [0.3], [0.1], [0.2]])
concat_demo = concat_demo.reshape(4, 4)
im5 = ax5.imshow(concat_demo, cmap=blue_cmap(), aspect='auto', extent=[5.0, 6.5, 0.5, 2.0])
ax5.axvline(x=5.42, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
ax5.axvline(x=5.83, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
ax5.axvline(x=6.25, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
ax5.text(5.21, 2.15, '|', ha='center', fontsize=10, color='red')
ax5.text(5.62, 2.15, '|', ha='center', fontsize=10, color='red')
ax5.text(6.04, 2.15, '|', ha='center', fontsize=10, color='red')
ax5.text(5.21, 0.2, 'In', ha='center', fontsize=8, color='#616161')
ax5.text(5.62, 0.2, 'TOD', ha='center', fontsize=8, color='#616161')
ax5.text(6.04, 0.2, 'DOW', ha='center', fontsize=8, color='#616161')
ax5.text(6.46, 0.2, 'Adp', ha='center', fontsize=8, color='#616161')

ax6 = fig.add_subplot(3, 2, 6)
ax6.set_xlim(0, 10)
ax6.set_ylim(0, 7)
ax6.set_title('6. Complete Forward Pass Example', fontsize=14, fontweight='bold', color='#424242', pad=10)
ax6.axis('off')

ax6.text(0.5, 6.5, 'Assume: batch_size=1, in_steps=4, num_nodes=3 (simplified)', fontsize=10, color='#616161')

input_demo = np.array([[[25.0, 0.04, 3]], [[28.0, 0.08, 3]], [[32.0, 0.12, 3]], [[30.0, 0.16, 3]]])
input_demo = input_demo.reshape(4, 3)
ax6.text(0.5, 6.0, 'Input x[0]:', fontsize=10, fontweight='bold', color='#424242')
draw_tensor(ax6, input_demo, 0.5, 5.0, 2.0, 0.9, cmap=blue_cmap())

ax6.text(3.0, 6.0, '-> Proj ->', fontsize=9, color='#616161')

input_proj_out = np.array([[12.5, 8.3, 15.2], [13.1, 9.0, 14.8], [14.2, 10.1, 16.0], [13.8, 9.5, 15.5]])
draw_tensor(ax6, input_proj_out, 3.0, 5.0, 2.0, 0.9, cmap=blue_cmap())

ax6.text(5.3, 6.0, '-> TOD ->', fontsize=9, color='#616161')
tod_out = np.array([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5], [0.4, 0.5, 0.6]])
draw_tensor(ax6, tod_out, 5.3, 5.0, 2.0, 0.9, cmap=blue_cmap())

ax6.text(0.5, 4.3, '-> DOW ->', fontsize=9, color='#616161')
dow_out = np.array([[0.3, 0.2, 0.5], [0.3, 0.2, 0.5], [0.3, 0.2, 0.5], [0.3, 0.2, 0.5]])
draw_tensor(ax6, dow_out, 0.5, 3.4, 2.0, 0.9, cmap=blue_cmap())

ax6.text(3.0, 4.3, '-> Adp ->', fontsize=9, color='#616161')
adp_out = np.array([[0.1, 0.2], [0.2, 0.3], [0.3, 0.4], [0.4, 0.5]])
draw_tensor(ax6, adp_out, 3.0, 3.4, 2.0, 0.9, cmap=blue_cmap())

ax6.text(5.3, 4.0, '-> Concat ->', fontsize=9, color='#616161')

final_out = np.array([[12.9, 8.5, 15.5, 0.1, 0.2, 0.3, 0.3, 0.2, 0.5, 0.1, 0.2],
                       [13.3, 9.2, 15.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.5, 0.2, 0.3],
                       [14.5, 10.4, 16.3, 0.3, 0.4, 0.5, 0.3, 0.2, 0.5, 0.3, 0.4],
                       [14.1, 9.8, 15.8, 0.4, 0.5, 0.6, 0.3, 0.2, 0.5, 0.4, 0.5]])
draw_tensor(ax6, final_out, 5.3, 2.5, 4.5, 1.8, cmap=blue_cmap())

ax6.text(5.3, 1.8, '(4, 3, 11) = (in_steps, num_nodes, model_dim)', fontsize=9, color='#757575', family='monospace')

ax6.text(0.5, 1.2, 'Summary:', fontsize=11, fontweight='bold', color='#424242')
summary = '''1. x: (4, 3, 3) -> Proj -> (4, 3, 24)
2. TOD: (4, 3) -> Embed -> (4, 3, 24)  
3. DOW: (4, 3) -> Embed -> (4, 3, 24)
4. Adaptive: (4, 3, 80) learnable
5. Concat: cat([...], dim=-1) -> (4, 3, 152)'''
ax6.text(0.5, 0.6, summary, fontsize=8, color='#424242', family='monospace')

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(r'D:\大三下\智能交通\STAEformer_Embedding_Layers.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.savefig(r'D:\大三下\智能交通\STAEformer_Embedding_Layers.pdf', bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.show()
print('Saved!')
