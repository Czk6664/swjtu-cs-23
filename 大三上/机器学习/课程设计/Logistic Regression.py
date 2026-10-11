# coding=utf-8
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, log_loss, classification_report,precision_recall_fscore_support, confusion_matrix)
from sklearn.preprocessing import LabelEncoder

train_data = np.loadtxt('experiment_05_training_set.csv',delimiter=',')
test_data = np.loadtxt('experiment_05_testing_set.csv',delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:,:-1]/255
train_y = train_data[:,-1]
test_x = test_data[:,:-1]/255
test_y = test_data[:,-1]

x_train,x_valid,y_train,y_valid = train_test_split(
    train_x,train_y,test_size=0.2,
    random_state=42
    )

epochs = 10
iter_per_epoch = 100
iter = 0

model = LogisticRegression(
    multi_class='multinomial',
    max_iter=1000,
    solver='saga',
    random_state=42,
    n_jobs=-1,
    warm_start=True
    )

epoch_train_loss = []
epoch_train_acc = []
epoch_train_precision = []
epoch_train_recall = []
epoch_train_f1 = []
epoch_val_loss = []
epoch_val_acc = []
epoch_val_f1 = []


def evaluate_one_epoch(model, x_train, y_train, x_val, y_val, epoch):
    y_train_pred = model.predict(x_train)    
    y_train_proba = model.predict_proba(x_train)
    y_val_pred = model.predict(x_val)        
    y_val_proba = model.predict_proba(x_val)   

    train_loss = log_loss(y_train, y_train_proba)
    train_acc = accuracy_score(y_train, y_train_pred)
    _, _, train_f1, _ = precision_recall_fscore_support(y_train, y_train_pred, average='macro')
    
    # 计算验证集核心指标
    val_loss = log_loss(y_val, y_val_proba)
    val_acc = accuracy_score(y_val, y_val_pred)
    _, _, val_f1, _ = precision_recall_fscore_support(y_val, y_val_pred, average='macro')
    
    # 输出本轮结果（简洁版）
    print(f"\n===== 第 {epoch+1}/{total_epochs} 轮训练结果 =====")
    print(f"训练集 - 损失: {train_loss:.4f} | 准确率: {train_acc:.4f} | F1值: {train_f1:.4f}")
    print(f"验证集 - 损失: {val_loss:.4f} | 准确率: {val_acc:.4f} | F1值: {val_f1:.4f}")
    
    # 存储指标（用于后续可视化）
    epoch_train_loss.append(train_loss)
    epoch_train_acc.append(train_acc)
    epoch_train_f1.append(train_f1)
    epoch_val_loss.append(val_loss)
    epoch_val_acc.append(val_acc)
    epoch_val_f1.append(val_f1)
    
    return train_loss, val_loss, train_acc, val_acc, train_f1, val_f1
