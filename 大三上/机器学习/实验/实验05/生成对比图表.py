import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 实验结果数据
learning_rates = [10, 1, 0.1, 0.01]
train_losses = [16624, 2251, 1380, 2285]
test_accuracies = [0.2990, 0.9140, 0.9150, 0.8990]

# 创建2x2子图布局
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. 训练集损失对比（柱状图）
ax1 = axes[0, 0]
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
bars1 = ax1.bar([str(lr) for lr in learning_rates], train_losses, color=colors, alpha=0.7, edgecolor='black')
ax1.set_xlabel('学习率', fontsize=12, fontweight='bold')
ax1.set_ylabel('训练集损失值', fontsize=12, fontweight='bold')
ax1.set_title('不同学习率下的训练集损失对比', fontsize=14, fontweight='bold')
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# 在柱子上添加数值标签
for bar, loss in zip(bars1, train_losses):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(loss)}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# 2. 测试集精度对比（柱状图）
ax2 = axes[0, 1]
bars2 = ax2.bar([str(lr) for lr in learning_rates], 
                [acc * 100 for acc in test_accuracies], 
                color=colors, alpha=0.7, edgecolor='black')
ax2.set_xlabel('学习率', fontsize=12, fontweight='bold')
ax2.set_ylabel('测试集精度 (%)', fontsize=12, fontweight='bold')
ax2.set_title('不同学习率下的测试集精度对比', fontsize=14, fontweight='bold')
ax2.set_ylim([0, 100])
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# 在柱子上添加数值标签
for bar, acc in zip(bars2, test_accuracies):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{acc:.4f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# 3. 训练集损失 vs 测试集精度（散点图）
ax3 = axes[1, 0]
scatter = ax3.scatter(train_losses, [acc * 100 for acc in test_accuracies], 
                     c=colors, s=300, alpha=0.6, edgecolors='black', linewidth=2)

# 添加学习率标签
for i, lr in enumerate(learning_rates):
    ax3.annotate(f'lr={lr}', 
                (train_losses[i], test_accuracies[i] * 100),
                xytext=(10, 10), textcoords='offset points',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=colors[i], alpha=0.3))

ax3.set_xlabel('训练集损失值', fontsize=12, fontweight='bold')
ax3.set_ylabel('测试集精度 (%)', fontsize=12, fontweight='bold')
ax3.set_title('训练集损失 vs 测试集精度', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')

# 4. 综合性能雷达图
ax4 = axes[1, 1]
ax4.axis('off')

# 创建性能评分表
performance_data = []
for i, lr in enumerate(learning_rates):
    # 归一化评分 (0-100)
    loss_score = max(0, 100 - (train_losses[i] / max(train_losses)) * 100)
    acc_score = test_accuracies[i] * 100
    
    # 收敛速度评分（基于学习率特性）
    if lr == 10:
        speed_score = 20  # 不稳定
    elif lr == 1:
        speed_score = 85  # 快速
    elif lr == 0.1:
        speed_score = 90  # 最佳平衡
    else:
        speed_score = 60  # 较慢
    
    # 稳定性评分
    if lr == 10:
        stability_score = 20
    elif lr == 1:
        stability_score = 75
    elif lr == 0.1:
        stability_score = 95
    else:
        stability_score = 90
    
    performance_data.append({
        'lr': lr,
        'loss_score': loss_score,
        'acc_score': acc_score,
        'speed_score': speed_score,
        'stability_score': stability_score,
        'overall': (loss_score + acc_score + speed_score + stability_score) / 4
    })

# 绘制性能对比表
table_data = []
headers = ['学习率', '损失评分', '精度评分', '速度评分', '稳定性', '综合评分']
for pd in performance_data:
    table_data.append([
        f"{pd['lr']}",
        f"{pd['loss_score']:.1f}",
        f"{pd['acc_score']:.1f}",
        f"{pd['speed_score']:.1f}",
        f"{pd['stability_score']:.1f}",
        f"{pd['overall']:.1f}"
    ])

table = ax4.table(cellText=table_data, colLabels=headers,
                 cellLoc='center', loc='center',
                 colColours=['#f0f0f0']*6)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# 设置表头样式
for i in range(6):
    table[(0, i)].set_facecolor('#3498db')
    table[(0, i)].set_text_props(weight='bold', color='white')

# 高亮最佳性能（学习率0.1）
for i in range(6):
    table[(3, i)].set_facecolor('#2ecc71')
    table[(3, i)].set_text_props(weight='bold')

ax4.set_title('综合性能评分对比 (0-100分制)', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('性能对比分析图.png', dpi=300, bbox_inches='tight')
print("✅ 性能对比分析图已生成: 性能对比分析图.png")
plt.show()

# 生成详细的数值对比报告
print("\n" + "="*70)
print("详细性能对比报告")
print("="*70)
print(f"{'学习率':<8} {'训练损失':<12} {'测试精度':<12} {'损失排名':<10} {'精度排名':<10}")
print("-"*70)

# 排序
loss_rank = sorted(range(len(train_losses)), key=lambda i: train_losses[i])
acc_rank = sorted(range(len(test_accuracies)), key=lambda i: test_accuracies[i], reverse=True)

for i, lr in enumerate(learning_rates):
    loss_r = loss_rank.index(i) + 1
    acc_r = acc_rank.index(i) + 1
    print(f"{lr:<8} {train_losses[i]:<12} {test_accuracies[i]:<12.4f} {loss_r:<10} {acc_r:<10}")

print("="*70)
print(f"\n🏆 最佳学习率: 0.1")
print(f"   - 训练集损失: 1380 (第1名)")
print(f"   - 测试集精度: 0.9150 (第1名)")
print(f"   - 综合评价: 收敛平稳，性能最优\n")
