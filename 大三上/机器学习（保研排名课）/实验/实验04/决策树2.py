import numpy as np
import matplotlib.pyplot as plt
from sklearn import tree

# read data from files
load_data1 = np.loadtxt('experiment_04_training_set.csv',delimiter=',')
load_data2 = np.loadtxt('experiment_04_testing_set.csv',delimiter=',')
num_train = load_data1.shape[0]
num_test = load_data2.shape[0]
train_x = load_data1[:,:-1]
train_y = load_data1[:,-1].reshape([num_train,1])
test_x = load_data2[:,:-1]
test_y = load_data2[:,-1].reshape([num_test,1])

print('特征矩阵形状:')
print('train_x.shape:', train_x.shape)
print('train_y.shape:', train_y.shape)
print('test_x.shape:', test_x.shape)
print('test_y.shape:', test_y.shape)
print('代码执行完成！')

def split_array(arr, num):
    # 小于等于num的元素
    less_or_equal = arr[arr[:,0] <= num]
    greater = arr[arr[:,0] > num]
    return less_or_equal, greater

def gini(table):
    unique_valy,county = np.unique(table[:,1],return_counts=True)
    gini=1
    for i in range(len(county)):
        gini = gini - (county[i]/np.sum(county))**2
    return gini

def gini_index(table,num):
    less, greater = split_array(table, num)
    gini1 = gini(less)
    gini2 = gini(greater)
    giniIndex = less.shape[0]/(less.shape[0]+greater.shape[0])*gini1+greater.shape[0]/(less.shape[0]+greater.shape[0])*gini2
    return giniIndex

for i in range(train_x.shape[1]):
    tabel = np.hstack((train_x[:,i].reshape([num_train,1]),train_y))
    sorted_tabel  = tabel[tabel[:,0].argsort()]
    min_giniIndex = 1
    min_num = 0
    for j in range(train_x.shape[0]-1):
        num = (sorted_tabel[j,0]+sorted_tabel[j+1,0])/2
        giniIndex = gini_index(sorted_tabel,num)
        if giniIndex < min_giniIndex:
            min_giniIndex = giniIndex
            min_num = num
    print('the',i,'giniIndex is',round(min_giniIndex,2),'split by',round(min_num,2))

def calculate_discrete_gini(feature_column, train_y, feature_index=None):

    # 重塑特征列为二维数组并与标签合并
    feature_2d = feature_column.reshape(-1, 1)
    tabel = np.hstack((feature_2d, train_y))
    
    # 获取特征的所有唯一值
    unique_values = np.unique(tabel[:, 0])
    total_samples = tabel.shape[0]
    
    # 计算条件基尼指数（加权平均）
    giniIndex = 0
    for val in unique_values:
        # 获取该特征值对应的所有样本
        subset = tabel[tabel[:, 0] == val]
        subset_size = subset.shape[0]
        
        # 计算该子集的基尼指数
        subset_gini = gini(subset)
        
        # 加权累加到总基尼指数
        giniIndex += (subset_size / total_samples) * subset_gini
    
    return giniIndex, unique_values, feature_index

print("\n第5个特征（索引4）的离散基尼指数分析结果:")
discrete_result = calculate_discrete_gini(train_x[:,4], train_y, 4)
print(f"离散特征基尼指数: {round(discrete_result[0],2)}")
print(f"特征唯一值: {discrete_result[1]}")
print(f"特征索引: {discrete_result[2]}")

print("\n第13个特征（索引12）的离散基尼指数分析结果:")
discrete_result = calculate_discrete_gini(train_x[:,12], train_y, 12)
print(f"离散特征基尼指数: {round(discrete_result[0],2)}")
print(f"特征唯一值: {discrete_result[1]}")
print(f"特征索引: {discrete_result[2]}")
