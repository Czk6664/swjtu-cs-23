import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
train_data = np.loadtxt('experiment_05_training_set.csv', delimiter=',')
test_data = np.loadtxt('experiment_05_testing_set.csv', delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:, :-1] / 255
train_y = train_data[:, -1]
test_x = test_data[:, :-1] / 255
test_y = test_data[:, -1]

# one-hot编码
one_hot_train = np.zeros((num_train, 10))
one_hot_train[np.arange(num_train), train_y.astype(int)] = 1

# Sigmoid激活函数
def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

# 前向传播（单个样本）
def forward_single(x, W, b, V, theta):
    z = W.T @ x.reshape(-1, 1) - b
    a = sigmoid(z)
    t = V.T @ a - theta
    y = sigmoid(t)
    return y, a

# 计算批次梯度
def compute_batch_gradients(X_batch, Y_batch, W, b, V, theta):
    batch_size = X_batch.shape[0]
    
    # 初始化梯度累加器
    grad_W = np.zeros_like(W)
    grad_b = np.zeros_like(b)
    grad_V = np.zeros_like(V)
    grad_theta = np.zeros_like(theta)
    
    for i in range(batch_size):
        x = X_batch[i]
        target = Y_batch[i].reshape(-1, 1)
        
        # 前向传播
        y, a = forward_single(x, W, b, V, theta)
        
        # 计算梯度
        delta_y = (y - target) * y * (1 - y)
        grad_theta += -delta_y
        grad_V += a @ delta_y.T
        
        delta_a = (V @ delta_y) * a * (1 - a)
        grad_b += -delta_a
        grad_W += x.reshape(-1, 1) @ delta_a.T
    
    # 平均梯度
    grad_W /= batch_size
    grad_b /= batch_size
    grad_V /= batch_size
    grad_theta /= batch_size
    
    return grad_W, grad_b, grad_V, grad_theta

# 计算总损失
def compute_total_loss(X, Y_onehot, W, b, V, theta):
    total_loss = 0
    for i in range(X.shape[0]):
        y, _ = forward_single(X[i], W, b, V, theta)
        target = Y_onehot[i].reshape(-1, 1)
        total_loss += 0.5 * np.sum((y - target) ** 2)
    return total_loss

# 计算测试集精度
def compute_accuracy(X, Y, W, b, V, theta):
    correct = 0
    for i in range(X.shape[0]):
        y, _ = forward_single(X[i], W, b, V, theta)
        pred = np.argmax(y)
        if pred == Y[i]:
            correct += 1
    return correct / X.shape[0]

# 小批次梯度下降训练函数
def train_mini_batch(train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
                     learning_rate, epochs, batch_size):
    # 复制初始参数
    W = W_init.copy()
    b = b_init.copy()
    V = V_init.copy()
    theta = theta_init.copy()
    
    loss_history = []
    
    # 计算初始损失(第0次)
    initial_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
    loss_history.append(initial_loss)
    
    num_samples = train_x.shape[0]
    
    for epoch in range(epochs):
        # 随机打乱样本顺序
        indices = np.random.permutation(num_samples)
        
        # 按批次处理
        for start_idx in range(0, num_samples, batch_size):
            end_idx = min(start_idx + batch_size, num_samples)
            batch_indices = indices[start_idx:end_idx]
            
            X_batch = train_x[batch_indices]
            Y_batch = one_hot_train[batch_indices]
            
            # 计算批次梯度
            grad_W, grad_b, grad_V, grad_theta = compute_batch_gradients(
                X_batch, Y_batch, W, b, V, theta
            )
            
            # 更新参数
            W = W - learning_rate * grad_W
            b = b - learning_rate * grad_b
            V = V - learning_rate * grad_V
            theta = theta - learning_rate * grad_theta
        
        # 计算当前epoch的总损失
        total_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        loss_history.append(total_loss)
        
        if (epoch + 1) % 20 == 0:
            print(f"  Epoch {epoch+1}/{epochs}, 总损失: {total_loss:.2f}")
    
    return W, b, V, theta, loss_history

# 加载初始参数
data = np.load('initial_parameters.npz')
theta_init = data['arr_0']
V_init = data['arr_1']
b_init = data['arr_2']
W_init = data['arr_3']

print(f"参数维度: W{W_init.shape}, b{b_init.shape}, V{V_init.shape}, theta{theta_init.shape}")
print(f"训练集样本数: {num_train}, 测试集样本数: {num_test}")
print("\n开始训练...\n")

# 不同的学习率
learning_rates = [10, 1, 0.1, 0.01]
epochs = 100

# 不同的批次大小（1表示SGD）
batch_sizes = [1, 10, 100, 1000]

# 存储所有结果
all_results = {}

# 对每个批次大小进行实验
for batch_size in batch_sizes:
    print(f"\n{'='*70}")
    if batch_size == 1:
        print(f"随机梯度下降 (批次大小 = {batch_size})")
    else:
        print(f"小批次梯度下降 (批次大小 = {batch_size})")
    print(f"{'='*70}")
    
    results = {}
    
    # 对每个学习率进行训练
    for lr in learning_rates:
        print(f"\n学习率: {lr}")
        W, b, V, theta, loss_history = train_mini_batch(
            train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
            lr, epochs, batch_size
        )
        
        # 计算最终训练集损失
        final_train_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        
        # 计算测试集精度
        test_accuracy = compute_accuracy(test_x, test_y, W, b, V, theta)
        
        results[lr] = {
            'loss_history': loss_history,
            'final_train_loss': final_train_loss,
            'test_accuracy': test_accuracy
        }
        
        print(f"  最终训练集损失: {int(final_train_loss)}")
        print(f"  测试集精度: {test_accuracy:.4f}")
    
    all_results[batch_size] = results
    
    # 绘制当前批次大小的损失曲线
    plt.figure(figsize=(10, 6))
    for lr in learning_rates:
        plt.plot(range(0, epochs + 1), results[lr]['loss_history'], 
                 label=f'学习率 = {lr}', linewidth=2, marker='o', markersize=3, markevery=10)
    
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('总损失', fontsize=12)
    if batch_size == 1:
        title = f'随机梯度下降 - 不同学习率的总损失迭代曲线'
        filename = f'sgd_batch_{batch_size}.png'
    else:
        title = f'小批次梯度下降 (批次大小={batch_size}) - 不同学习率的总损失迭代曲线'
        filename = f'mini_batch_{batch_size}.png'
    
    plt.title(title, fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 100)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\n图表已保存: {filename}")
    plt.show()

# 打印最终汇总结果表格
print("\n" + "="*80)
print("不同学习率的模型在迭代100个epoch后的结果")
print("="*80)
print(f"{'学习率':<10} {'训练集损失(整数)':<20} {'测试集精度':<15}")
print("-"*80)

for lr in learning_rates:
    # 使用批次大小为1（SGD）的结果
    train_loss = int(all_results[1][lr]['final_train_loss'])
    test_acc = all_results[1][lr]['test_accuracy']
    print(f"{lr:<10} {train_loss:<20} {test_acc:.4f}")

print("="*80)

# 创建一个综合对比表格
print("\n" + "="*80)
print("所有批次大小和学习率的完整结果对比")
print("="*80)

for batch_size in batch_sizes:
    if batch_size == 1:
        print(f"\n随机梯度下降 (批次大小 = {batch_size}):")
    else:
        print(f"\n小批次梯度下降 (批次大小 = {batch_size}):")
    print(f"{'学习率':<10} {'训练集损失(整数)':<20} {'测试集精度':<15}")
    print("-"*60)
    for lr in learning_rates:
        train_loss = int(all_results[batch_size][lr]['final_train_loss'])
        test_acc = all_results[batch_size][lr]['test_accuracy']
        print(f"{lr:<10} {train_loss:<20} {test_acc:.4f}")

print("\n" + "="*80)
print("实验完成！")
