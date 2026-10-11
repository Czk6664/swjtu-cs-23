# coding=utf-8
import numpy as np
import matplotlib.pyplot as plt
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, log_loss, precision_recall_fscore_support)


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

model = MultinomialNB(
    alpha=1.0  
)

print("开始训练朴素贝叶斯模型")

model.fit(x_train, y_train)

y_train_pred = model.predict(x_train)    
y_train_proba = model.predict_proba(x_train)
y_val_pred = model.predict(x_valid)        
y_val_proba = model.predict_proba(x_valid)   

train_loss = log_loss(y_train, y_train_proba)
train_acc = accuracy_score(y_train, y_train_pred)
train_precision, train_recall, train_f1, _ = precision_recall_fscore_support(y_train, y_train_pred, average='macro')
    
val_loss = log_loss(y_valid, y_val_proba)
val_acc = accuracy_score(y_valid, y_val_pred)
val_precision, val_recall, val_f1, _ = precision_recall_fscore_support(y_valid, y_val_pred, average='macro')

print(f"训练集损失: {train_loss:.4f} 准确率: {train_acc:.4f} 精确率: {train_precision:.4f} 召回率: {train_recall:.4f} F1值: {train_f1:.4f}")
print(f"验证集损失: {val_loss:.4f} 准确率: {val_acc:.4f} 精确率: {val_precision:.4f} 召回率: {val_recall:.4f} F1值: {val_f1:.4f}")
    

y_test_pred = model.predict(test_x)
y_test_proba = model.predict_proba(test_x)
test_loss = log_loss(test_y, y_test_proba)
test_acc = accuracy_score(test_y, y_test_pred)
test_precision, test_recall, test_f1, _ = precision_recall_fscore_support(
    test_y, y_test_pred, average='macro'
)
print("训练结束，以下是测试集结果")
print(f"损失: {test_loss:.4f} 准确率: {test_acc:.4f}")
print(f"精确率: {test_precision:.4f} 召回率: {test_recall:.4f} F1值: {test_f1:.4f}")
