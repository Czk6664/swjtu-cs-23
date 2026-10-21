import numpy as np
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn.metrics import accuracy_score

# -------------------------- 1. 数据加载与预处理 --------------------------
# 读取数据（若文件路径不同，需自行调整）
train_data = np.loadtxt('experiment_09_training_set.csv', delimiter=',')
test_data = np.loadtxt('experiment_09_testing_set.csv', delimiter=',')

num_train = train_data.shape[0]
num_test = test_data.shape[0]

# 特征归一化（除以255），分离特征和标签
train_x = train_data[:, :-1] / 255
train_y = train_data[:, -1].reshape((num_train, 1))  # 标签形状为(n,1)
test_x = test_data[:, :-1] / 255
test_y = test_data[:, -1].reshape((num_test, 1))

# -------------------------- 2. 定义Bagging随机森林函数 --------------------------
def bagging_random_forest(T, train_x, train_y, test_x, test_y):
    """
    构建Bagging随机森林模型
    参数：
        T: 决策树数量
        train_x: 训练集特征
        train_y: 训练集标签
        test_x: 测试集特征
        test_y: 测试集标签
    返回：
        test_acc: 测试集精度
    """
    num_samples = train_x.shape[0]  # 训练集样本数量
    tree_models = []  # 存储基决策树模型
    predictions = []  # 存储每个基模型的测试集预测结果

    # 为每个决策树设置不同的随机种子（可选，增强随机性）
    rng = np.random.default_rng(seed=1)  # 全局随机数生成器，保证可复现

    for _ in range(T):
        # -------------------------- 步骤1：Bootstrap抽样（有放回） --------------------------
        # 生成抽样索引：从0~num_samples-1中随机选num_samples个样本（有放回）
        sample_indices = rng.choice(num_samples, num_samples, replace=True)
        # 根据索引获取抽样后的训练集
        bootstrap_x = train_x[sample_indices]
        bootstrap_y = train_y[sample_indices]

        # -------------------------- 步骤2：训练单棵决策树 --------------------------
        # 决策树参数与原代码一致：熵作为划分准则，最大特征数100，固定随机种子
        dt = tree.DecisionTreeClassifier(
            random_state=rng.integers(0, 1000),  # 每个树用不同的随机种子
            criterion='entropy',
            max_features=100
        )
        dt.fit(bootstrap_x, bootstrap_y.ravel())  # ravel()将(n,1)转为(n,)，适配sklearn输入

        # -------------------------- 步骤3：存储模型与预测结果 --------------------------
        tree_models.append(dt)
        pred = dt.predict(test_x)
        predictions.append(pred)

    # -------------------------- 步骤4：多数投票集成预测 --------------------------
    # predictions形状：(T, num_test)，转置后为(num_test, T)，对每个样本的T个预测结果投票
    predictions = np.array(predictions).T  # 转置后：每行是一个样本的所有模型预测结果
    
    # 核心修正：将预测结果强制转换为整数类型（解决float64无法bincount的问题）
    # 若标签是浮点数（如0.0、1.0），转换为int后不影响投票结果
    predictions = predictions.astype(np.int64)
    
    # 多数投票：对每个样本的T个预测结果，取出现次数最多的标签
    final_pred = np.array([np.bincount(row).argmax() for row in predictions])

    # -------------------------- 步骤5：计算测试集精度 --------------------------
    # 测试标签也转换为整数类型，保证精度计算一致
    test_acc = accuracy_score(test_y.ravel().astype(np.int64), final_pred)

    return test_acc

# -------------------------- 3. 遍历T=1~20，计算精度 --------------------------
T_range = range(1, 21)  # T从1到20
acc_list = []  # 存储每个T对应的测试集精度

for T in T_range:
    acc = bagging_random_forest(T, train_x, train_y, test_x, test_y)
    acc_list.append(acc)
    print(f"决策树数量T={T}时，测试集精度={acc:.2f}")

# -------------------------- 4. 绘制精度变化曲线 --------------------------
plt.figure(figsize=(10, 6))
plt.plot(T_range, acc_list, marker='o', linestyle='-', color='b', label='Test Accuracy')
plt.xlabel('Number of Decision Trees (T)', fontsize=12)
plt.ylabel('Test Accuracy', fontsize=12)
plt.title('Random Forest Test Accuracy vs. Number of Base Models', fontsize=14)
plt.xticks(T_range)  # x轴显示1~20的整数
plt.grid(True, alpha=0.3)
plt.legend()
plt.show()