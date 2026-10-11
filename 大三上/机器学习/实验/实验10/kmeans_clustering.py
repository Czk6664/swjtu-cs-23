import numpy as np
import matplotlib.pyplot as plt
train_x = np.loadtxt('experiment_10_training_set.csv', delimiter=',', comments='#')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def kmeans(data, k, initial_indices, max_iter=10):
    n_samples = data.shape[0]
    centers = data[initial_indices].copy()
    loss_history = []
    for iteration in range(max_iter):
        # 步骤1: 计算距离并分配簇标签
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.sum((data - centers[i]) ** 2, axis=1)
        labels = np.argmin(distances, axis=1)

        # 步骤2: 分配完标签后立即计算loss
        loss = 0
        for i in range(n_samples):
            loss += distances[i, labels[i]]
        loss_history.append(loss)
        print(f"迭代 {iteration + 1}: Loss = {loss:.4f}")
        
        # 步骤3: 计算完loss后再更新聚类中心
        new_centers = np.zeros_like(centers)
        for i in range(k):
            cluster_points = data[labels == i]
            if len(cluster_points) > 0:
                new_centers[i] = cluster_points.mean(axis=0)
            else:
                new_centers[i] = centers[i]
        
        centers = new_centers
    
    return labels, centers, loss_history

k = 5
initial_indices = [21, 38, 53, 287, 350]
max_iter = 10

print("初始聚类中心索引:", initial_indices)
print("初始聚类中心坐标:")
for i, idx in enumerate(initial_indices):
    print(f"  中心{i+1} (索引{idx}): {train_x[idx]}")
print()

labels, centers, loss_history = kmeans(train_x, k, initial_indices, max_iter)

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
colors = ['red', 'blue', 'green', 'orange', 'purple']
for i in range(k):
    cluster_points = train_x[labels == i]
    plt.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                c=colors[i], label=f'类别 {i+1}', alpha=0.6, s=30)

plt.xlabel('X')
plt.ylabel('Y')
plt.title('K均值聚类结果 (k=5)')
plt.legend()
plt.grid(True, alpha=0.3)

# 子图2: Loss变化曲线
plt.subplot(1, 2, 2)
plt.plot(range(1, max_iter + 1), loss_history, 'b-o', linewidth=2, markersize=8)
plt.xlabel('迭代次数')
plt.ylabel('Loss值')
plt.title('Loss随迭代次数变化曲线')
plt.grid(True, alpha=0.3)
plt.xticks(range(1, max_iter + 1))

plt.tight_layout()
plt.savefig('kmeans_result.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n最终聚类中心:")
for i in range(k):
    count = np.sum(labels == i)
    print(f"  类别{i+1}: 中心={centers[i]}, 样本数={count}")

print(f"\n最终Loss值: {loss_history[-1]:.4f}")
print("\n结果图已保存为 kmeans_result.png")
