import numpy as np
import matplotlib.pyplot as plt
import os
import pickle

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

# 保存训练进度
def save_checkpoint(lr, epoch, W, b, V, theta, loss_history, checkpoint_dir='checkpoints'):
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    
    checkpoint = {
        'epoch': epoch,
        'W': W,
        'b': b,
        'V': V,
        'theta': theta,
        'loss_history': loss_history,
        'learning_rate': lr
    }
    
    filename = os.path.join(checkpoint_dir, f'checkpoint_lr_{lr}_epoch_{epoch}.pkl')
    with open(filename, 'wb') as f:
        pickle.dump(checkpoint, f)
    print(f"  已保存检查点: {filename}")

# 加载训练进度
def load_checkpoint(lr, checkpoint_dir='checkpoints'):
    if not os.path.exists(checkpoint_dir):
        return None
    
    # 查找该学习率的所有检查点
    checkpoints = [f for f in os.listdir(checkpoint_dir) 
                   if f.startswith(f'checkpoint_lr_{lr}_') and f.endswith('.pkl')]
    
    if not checkpoints:
        return None
    
    # 找到最新的检查点(epoch最大的)
    latest_checkpoint = max(checkpoints, 
                           key=lambda x: int(x.split('_epoch_')[1].split('.pkl')[0]))
    
    filepath = os.path.join(checkpoint_dir, latest_checkpoint)
    with open(filepath, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"  加载检查点: {filepath}")
    print(f"  从第 {checkpoint['epoch']} 轮继续训练")
    return checkpoint

# 训练函数(支持断点续训)
def train_sgd(train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
              learning_rate, epochs, test_x=None, test_y=None, 
              checkpoint=None, save_interval=10):
    # 如果有检查点,从检查点恢复
    if checkpoint is not None:
        W = checkpoint['W'].copy()
        b = checkpoint['b'].copy()
        V = checkpoint['V'].copy()
        theta = checkpoint['theta'].copy()
        loss_history = checkpoint['loss_history'].copy()
        start_epoch = checkpoint['epoch']
    else:
        # 从初始参数开始
        W = W_init.copy()
        b = b_init.copy()
        V = V_init.copy()
        theta = theta_init.copy()
        loss_history = []
        start_epoch = 0
        
        # 计算初始损失(第0次)
        initial_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        loss_history.append(initial_loss)
    
    for epoch in range(start_epoch, epochs):
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
        
        # 定期保存检查点
        if (epoch + 1) % save_interval == 0:
            save_checkpoint(learning_rate, epoch + 1, W, b, V, theta, loss_history)
    
    return W, b, V, theta, loss_history

# 小批次梯度下降训练函数
def train_minibatch(train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
                    learning_rate, epochs, batch_size, test_x=None, test_y=None, 
                    checkpoint=None, save_interval=10):
    # 如果有检查点,从检查点恢复
    if checkpoint is not None:
        W = checkpoint['W'].copy()
        b = checkpoint['b'].copy()
        V = checkpoint['V'].copy()
        theta = checkpoint['theta'].copy()
        loss_history = checkpoint['loss_history'].copy()
        start_epoch = checkpoint['epoch']
    else:
        # 从初始参数开始
        W = W_init.copy()
        b = b_init.copy()
        V = V_init.copy()
        theta = theta_init.copy()
        loss_history = []
        start_epoch = 0
        
        # 计算初始损失(第0次)
        initial_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        loss_history.append(initial_loss)
    
    num_samples = train_x.shape[0]
    
    for epoch in range(start_epoch, epochs):
        # 随机打乱样本顺序
        indices = np.random.permutation(num_samples)
        
        # 按批次处理
        for i in range(0, num_samples, batch_size):
            batch_indices = indices[i:i+batch_size]
            
            # 初始化批次梯度累加器
            grad_W = np.zeros_like(W)
            grad_b = np.zeros_like(b)
            grad_V = np.zeros_like(V)
            grad_theta = np.zeros_like(theta)
            
            # 对批次中的每个样本计算梯度
            for idx in batch_indices:
                x = train_x[idx]
                target = one_hot_train[idx].reshape(-1, 1)
                
                # 前向传播
                y, a = forward_single(x, W, b, V, theta)
                
                # 计算梯度
                delta_y = (y - target) * y * (1 - y)
                grad_theta += -delta_y
                grad_V += a @ delta_y.T
                
                delta_a = (V @ delta_y) * a * (1 - a)
                grad_b += -delta_a
                grad_W += x.reshape(-1, 1) @ delta_a.T
            
            # 使用批次平均梯度更新参数
            batch_len = len(batch_indices)
            W = W - learning_rate * grad_W / batch_len
            b = b - learning_rate * grad_b / batch_len
            V = V - learning_rate * grad_V / batch_len
            theta = theta - learning_rate * grad_theta / batch_len
        
        # 计算当前epoch的总损失
        total_loss = compute_total_loss(train_x, one_hot_train, W, b, V, theta)
        loss_history.append(total_loss)
        
        # 定期保存检查点
        if (epoch + 1) % save_interval == 0:
            save_checkpoint(f"{learning_rate}_batch{batch_size}", epoch + 1, W, b, V, theta, loss_history)
    
    return W, b, V, theta, loss_history

# 加载初始参数
data = np.load('initial_parameters.npz')
theta_init = data['arr_0']
V_init = data['arr_1']
b_init = data['arr_2']
W_init = data['arr_3']

print(f"参数维度: W{W_init.shape}, b{b_init.shape}, V{V_init.shape}, theta{theta_init.shape}")
print(f"训练集样本数: {num_train}, 测试集样本数: {num_test}")
print("\n开始小批次梯度下降训练...\n")

# 不同的学习率和批次大小
learning_rates = [10, 1, 0.1, 0.01]
batch_sizes = [1, 10, 100, 1000]
epochs = 100

# 存储所有结果
all_results = {}

# 对每个批次大小进行实验
for batch_size in batch_sizes:
    print(f"\n{'='*70}")
    print(f"批次大小: {batch_size}")
    print(f"{'='*70}")
    
    results = {}
    
    # 对每个学习率进行训练
    for lr in learning_rates:
        print(f"训练中: 批次大小={batch_size}, 学习率={lr}...")
        
        # 训练(不使用检查点,每次重新训练)
        W, b, V, theta, loss_history = train_minibatch(
            train_x, one_hot_train, W_init, b_init, V_init, theta_init, 
            lr, epochs, batch_size, test_x=test_x, test_y=test_y,
            checkpoint=None, save_interval=50
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
        
        print(f"完成: 批次大小={batch_size}, 学习率={lr}, 训练集损失={int(final_train_loss)}, 测试集精度={test_accuracy:.4f}")
    
    all_results[batch_size] = results
    
    # 绘制当前批次大小的损失曲线
    plt.figure(figsize=(10, 6))
    for lr in learning_rates:
        plt.plot(range(0, epochs + 1), results[lr]['loss_history'], 
                 label=f'学习率 = {lr}', linewidth=2)
    
    plt.xlabel('轮次 (Epoch)', fontsize=12)
    plt.ylabel('总损失值', fontsize=12)
    plt.title(f'小批次梯度下降 (批次大小={batch_size}) - 不同学习率的损失迭代曲线', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'loss_curves_batch{batch_size}.png', dpi=300, bbox_inches='tight')
    plt.show()
    print(f"\n已保存图片: loss_curves_batch{batch_size}.png")

# 打印完整的结果汇总表格
print("\n" + "="*80)
print("最终结果汇总 - 所有批次大小和学习率")
print("="*80)
print(f"{'批次大小':<10} {'学习率':<10} {'训练集损失(整数)':<20} {'测试集精度':<15}")
print("-"*80)
for batch_size in batch_sizes:
    for lr in learning_rates:
        train_loss = int(all_results[batch_size][lr]['final_train_loss'])
        test_acc = all_results[batch_size][lr]['test_accuracy']
        print(f"{batch_size:<10} {lr:<10} {train_loss:<20} {test_acc:.4f}")
print("="*80)

# 保存所有结果到文件
print("\n正在保存结果...")
with open('training_results.pkl', 'wb') as f:
    pickle.dump(all_results, f)
print("所有结果已保存到: training_results.pkl")

# 同时保存为易读的文本文件
with open('training_results.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("训练结果汇总 - 所有批次大小和学习率\n")
    f.write("="*80 + "\n")
    f.write(f"{'批次大小':<10} {'学习率':<10} {'训练集损失':<20} {'测试集精度':<15}\n")
    f.write("-"*80 + "\n")
    for batch_size in batch_sizes:
        for lr in learning_rates:
            train_loss = int(all_results[batch_size][lr]['final_train_loss'])
            test_acc = all_results[batch_size][lr]['test_accuracy']
            f.write(f"{batch_size:<10} {lr:<10} {train_loss:<20} {test_acc:.4f}\n")
    f.write("="*80 + "\n")
print("结果摘要已保存到: training_results.txt\n")
