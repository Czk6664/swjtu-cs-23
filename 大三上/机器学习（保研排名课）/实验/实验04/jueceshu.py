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

def ent(table):
    unique_valy,county = np.unique(table[:,1],return_counts=True)
    ent = 0
    for i in range(len(county)):
        ent = ent - county[i]/np.sum(county) * np.log2(county[i]/np.sum(county))
    return ent


unique_valy,count= np.unique(train_y,return_counts=True)
entnum = 0
for i in range(len(count)):
    entnum = entnum-count[i]/np.sum(count) * np.log2(count[i]/np.sum(count))
print('信息熵:',entnum)

maxgainlist = np.zeros(train_x.shape[1])
jlist = np.zeros(train_x.shape[1])

for i in range(train_x.shape[1]):
    if i == 4:  
        continue
    if i == 12:  
        continue
    tabel = np.hstack((train_x[:,i].reshape([num_train,1]),train_y))
    # print(tabel)
    maxj = 0
    maxgain = 0
    sorted_table = tabel[tabel[:, 0].argsort()]
    for j in range(train_x.shape[0]-1):
        list1 = sorted_table[:j+1]  
        list2 = sorted_table[j+1:]  
        gain = entnum - list1.shape[0]/(list1.shape[0]+list2.shape[0])*ent(list1) - list2.shape[0]/(list1.shape[0]+list2.shape[0])*ent(list2)
        if gain > maxgain:
            maxgain = gain
            maxj = j
    maxgainlist[i] = maxgain
    jlist[i] = maxj
    print('第',i+1,'个特征的最大增益:', round(maxgainlist[i],2))
    print('第',i+1,'个特征的最大增益对应的阈值:', round((sorted_table[maxj,0]+sorted_table[maxj+1,0])/2,2))

# 计算离散特征（第5个特征）的信息增益
def calculate_discrete_entropy(feature_column, labels):
    # 合并特征和标签
    table = np.hstack((feature_column.reshape(-1,1), labels))
    # 获取特征的所有唯一值
    unique_vals, counts = np.unique(table[:,0], return_counts=True)
    
    # 计算条件熵
    cond_entropy = 0
    total_samples = len(labels)
    
    for i in range(len(unique_vals)):
        # 获取该特征值对应的所有样本标签
        subset_labels = table[table[:,0] == unique_vals[i], 1]
        subset_size = len(subset_labels)
        
        # 计算该子集的信息熵
        subset_entropy = 0
        unique_labels, label_counts = np.unique(subset_labels, return_counts=True)
        
        for j in range(len(unique_labels)):
            prob = label_counts[j] / subset_size
            subset_entropy -= prob * np.log2(prob)
        
        # 加权平均到条件熵
        cond_entropy += (subset_size / total_samples) * subset_entropy
    
    return cond_entropy


feature5_cond_entropy = calculate_discrete_entropy(train_x[:,4], train_y)
feature5_gain = entnum - feature5_cond_entropy
print('第5个特征的信息增益:', round(feature5_gain,2))

# 计算第13个特征的信息增益
feature13_cond_entropy = calculate_discrete_entropy(train_x[:,12], train_y)
feature13_gain = entnum - feature13_cond_entropy
print('第13个特征的信息增益:', round(feature13_gain,2))
