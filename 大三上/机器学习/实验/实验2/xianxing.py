import numpy as np
import matplotlib.pyplot as plt
# read data from files
load_data1 = np.loadtxt('experiment_02_training_set.csv',delimiter=',')
load_data2 = np.loadtxt('experiment_02_testing_set.csv',delimiter=',')
num_train = load_data1.shape[0]
num_test = load_data2.shape[0]
# split the data
train_x = load_data1[:,0].reshape((num_train,1))
train_y = load_data1[:,1].reshape((num_train,1))
test_x = load_data2[:,0].reshape((num_test,1))
test_y = load_data2[:,1].reshape((num_test,1))

one_col = np.ones(train_x.shape[0]).reshape((train_x.shape[0],1))
x = train_x
x = np.hstack((x,one_col))
xt = x
xt = xt.T
y = train_y 

w = np.linalg.inv(xt@x)@xt@y
print(w)
y_pred = np.zeros(test_x.shape[0]).reshape((test_x.shape[0],1))
total_err = 0

one_coltest = np.ones(test_x.shape[0]).reshape((test_x.shape[0],1))

test_x = np.hstack((test_x,one_coltest))
for i in range(test_x.shape[0]):
    y_pred[i] = test_x[i]@w
    total_err +=(y_pred[i]-test_y[i])**2
mse = total_err/test_x.shape[0]
print(mse)

y_pred_train = np.zeros(train_x.shape[0]).reshape((train_x.shape[0],1))
for i in range(train_x.shape[0]):
    y_pred_train[i] = x[i]@w

plt.scatter(train_x, train_y, label='train data', color='green' )
plt.scatter(test_x[:,0], test_y, label='test data', color='red' )
plt.plot(train_x, y_pred_train, label='fitting line',color='blue') 
plt.xlabel('X')
plt.ylabel('Y')
plt.title('result')
plt.legend()
plt.show()
    