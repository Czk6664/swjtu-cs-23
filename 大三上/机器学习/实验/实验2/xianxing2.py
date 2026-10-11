import numpy as np
import matplotlib.pyplot as plt

# 1. 读取并分割数据
load_data1 = np.loadtxt('experiment_02_training_set.csv', delimiter=',')
load_data2 = np.loadtxt('experiment_02_testing_set.csv', delimiter=',')

num_train = load_data1.shape[0]
num_test = load_data2.shape[0]


train_x_raw = load_data1[:, 0].reshape((num_train, 1))
train_y = load_data1[:, 1].reshape((num_train, 1))
test_x_raw = load_data2[:, 0].reshape((num_test, 1))
test_y = load_data2[:, 1].reshape((num_test, 1))

train_x_sq = train_x_raw ** 2  
one_col_train = np.ones(num_train).reshape((num_train, 1))  
x_train = np.hstack((train_x_sq, train_x_raw, one_col_train)) 


xt = x_train.T
w = np.linalg.inv(xt @ x_train) @ xt @ train_y
print("二次多项式回归参数 w (w2, w1, w0):")
print(w)


test_x_sq = test_x_raw ** 2 
one_col_test = np.ones(num_test).reshape((num_test, 1)) 
x_test = np.hstack((test_x_sq, test_x_raw, one_col_test))  


y_pred_test = np.zeros(num_test).reshape((num_test, 1))
total_err = 0
for i in range(num_test):
    y_pred_test[i] = x_test[i] @ w
    total_err += (y_pred_test[i] - test_y[i]) ** 2
mse = total_err / num_test
print("测试集 MSE:", mse)


y_pred_train = np.zeros(num_train).reshape((num_train, 1))
for i in range(num_train):
    y_pred_train[i] = x_train[i] @ w


sorted_idx = np.argsort(train_x_raw.flatten())  
sorted_train_x = train_x_raw[sorted_idx]
sorted_train_y_pred = y_pred_train[sorted_idx]

plt.figure(figsize=(10, 6))
plt.scatter(train_x_raw, train_y, label='Train Data', color='green', alpha=0.6)
plt.scatter(test_x_raw, test_y, label='Test Data', color='red', alpha=0.6)
plt.plot(sorted_train_x, sorted_train_y_pred, label='Fitting Curve (x²)', color='blue', linewidth=2)  # 平滑曲线

plt.xlabel('X (Original Feature)')
plt.ylabel('Y')
plt.title('Quadratic Polynomial Regression Result')
plt.legend()
plt.grid(alpha=0.3)
plt.show()