import numpy as np
import matplotlib.pyplot as plt
import scipy
from scipy.optimize import LinearConstraint, minimize
train_data = np.loadtxt('experiment_06_training_set.csv',delimiter=',')
test_data = np.loadtxt('experiment_06_testing_set.csv',delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:,:-1]
train_y = train_data[:,-1].reshape((num_train,1))
test_x = test_data[:,:-1]
test_y = test_data[:,-1].reshape((num_test,1))

def svm_minimize(W):
    return 0.5*W[:2].T@W[0:2]

W = np.zeros((3))
x1= np.hstack((train_x,np.ones((num_train,1))))
y1= train_y
A = x1 * y1

svm_constraint = LinearConstraint(A=A, lb=np.ones(train_x.shape[0]), ub=np.inf)
result = minimize(fun=svm_minimize,x0=W,args=(),constraints=svm_constraint)
W = result.x
print(W)

train_x_class1 = train_x[train_y.flatten() == 1]
train_x_class0 = train_x[train_y.flatten() == -1]
w1, w2, b = W 

plt.figure(figsize=(8, 6))  
plt.scatter(train_x_class1[:, 0],  train_x_class1[:, 1],  c='red',label='class 1',alpha=0.7)
plt.scatter(train_x_class0[:, 0], train_x_class0[:, 1], c='blue',label='class 0',alpha=0.7)

x1_min, x1_max = train_x[:, 0].min() - 1, train_x[:, 0].max() + 1
x1_range = np.linspace(x1_min, x1_max, 100)  
x2_boundary = (-w1 * x1_range - b) / w2

plt.plot( x1_range,x2_boundary, 'k-',linewidth=2,label='SVM line')
plt.xlabel('feature 1', fontsize=12)
plt.ylabel('feature 2', fontsize=12)
plt.title('SVM training set scatter plot and SVM line', fontsize=14)
plt.legend(fontsize=10) 
plt.grid(alpha=0.3)     
plt.axis('equal')      
plt.show()  

def predict(x, w, b):
    y_test = x @ np.array([w[0], w[1]]) + b
    return np.sign(y_test)
acc = 0
y_test = predict(test_x, W[:2], W[2])
for i in range(test_y.shape[0]):
    if y_test[i] == test_y[i]:
        acc += 1 
acc = acc / test_y.shape[0]
print(f"acc: {acc:.4f} ")



