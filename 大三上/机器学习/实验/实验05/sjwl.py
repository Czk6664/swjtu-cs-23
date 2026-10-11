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

# 反向传播（单个样本）
def backward_single(x, y, target, a, W, b, V, theta, learning_rate):
    # 计算梯度
    delta_y = (y - target) * y * (1 - y)
    grad_theta = -delta_y
    grad_V = a @ delta_y.T
    
    delta_a = (V @ delta_y) * a * (1 - a)
    grad_b = -delta_a
    grad_W = x.reshape(-1, 1) @ delta_a.T
    
    # 更新参数
    theta = theta - learning_rate * grad_theta
    V = V - learning_rate * grad_V
    b = b - learning_rate * grad_b
    W = W - learning_rate * grad_W
    
    return W, b, V, theta

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

# 训练函数
def train_sgd(train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
              learning_rate, epochs):
    # 复制初始参数
    W = W_init.copy()
    b = b_init.copy()
    V = V_init.copy()
    theta = theta_init.copy()
    
    loss_history = []
    
    # 计算初始损失(第0次)
    initial_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
    loss_history.append(initial_loss)
    
    for epoch in range(epochs):
        # 随机打乱样本顺序
        indices = np.random.permutation(num_train)
        
        # 对每个样本进行SGD更新
        for idx in indices:
            x = train_x[idx]
            target = one_hot_train[idx].reshape(-1, 1)
            
            # 前向传播
            y, a = forward_single(x, W, b, V, theta)
            
            # 反向传播并更新参数
            W, b, V, theta = backward_single(x, y, target, a, W, b, V, theta, learning_rate)
        
        # 计算当前epoch的总损失
        total_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        loss_history.append(total_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"学习率 {learning_rate}, Epoch {epoch+1}/{epochs}, 总损失: {total_loss:.2f}")
    
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

# 存储结果
results = {}

# 对每个学习率进行训练
for lr in learning_rates:
    print(f"\n========== 学习率: {lr} ==========")
    W, b, V, theta, loss_history = train_sgd(
        train_x, one_hot_train, W_init, b_init, V_init, theta_init, lr, epochs
    )
    
    # 计算最终训练集损失
    final_train_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
    
    # 计算测试集精度
    test_accuracy = compute_accuracy(test_x, test_y, W, b, V, theta)
    
    results[lr] = {
        'loss_history': loss_history,
        'final_train_loss': final_train_loss,
        'test_accuracy': test_accuracy,
        'W': W, 'b': b, 'V': V, 'theta': theta
    }
    
    print(f"\n最终训练集损失: {int(final_train_loss)}")
    print(f"测试集精度: {test_accuracy:.4f}")

# 绘制损失曲线
plt.figure(figsize=(10, 6))
for lr in learning_rates:
    plt.plot(range(0, epochs + 1), results[lr]['loss_history'], 
             label=f'学习率 = {lr}', linewidth=2)

plt.xlabel('轮次 (Epoch)', fontsize=12)
plt.ylabel('总损失值', fontsize=12)
plt.title('不同学习率下的损失函数迭代曲线', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('loss_curves.png', dpi=300, bbox_inches='tight')
plt.show()

# 打印汇总结果
print("\n" + "="*60)
print("最终结果汇总")
print("="*60)
print(f"{'学习率':<10} {'训练集损失(整数)':<20} {'测试集精度':<15}")
print("-"*60)
for lr in learning_rates:
    train_loss = int(results[lr]['final_train_loss'])
    test_acc = results[lr]['test_accuracy']
    print(f"{lr:<10} {train_loss:<20} {test_acc:.4f}")
print("="*60)
