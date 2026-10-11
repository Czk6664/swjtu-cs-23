import numpy as np
import matplotlib.pyplot as plt
from numpy.f2py.cfuncs import errmess
# read data from files
load_data1 = np.loadtxt('experiment_03_training_set.csv',delimiter=',')
load_data2 = np.loadtxt('experiment_03_testing_set.csv',delimiter=',')

train_x = load_data1[:,:-1]
train_y = load_data1[:,-1].reshape([load_data1.shape[0],1])
test_x = load_data2[:,:-1]
test_y = load_data2[:,-1].reshape([load_data2.shape[0],1])
#print (train_x)
# print(train_y)

one_colx = np.ones(train_x.shape[0]).reshape((train_x.shape[0],1))
train_xone = np.hstack((train_x,one_colx))
#print(train_xone.shape)
w = np.zeros((train_xone.shape[1],1))
#print(w.shape)
sigmaw = np.zeros((train_xone.shape[0],1))
Hw = np.zeros((train_xone.shape[1],1))
loss = np.zeros((1000,1))
for epoch in range(1000):
    for i in range (train_x.shape[0]):
        sigmaw[i] = 1/(1+np.exp(-np.dot(w.T,train_xone[i])))
        for  j  in range(train_xone.shape[1]):
            Hw[j] = ((sigmaw[i])-train_y[i])*train_xone[i,j]
            w[j] = w[j] - 0.001*Hw[j]
    loss[epoch]= -np.sum(train_y*np.log(sigmaw) + (1-train_y)*np.log(1-sigmaw))
#print(w)
plt.plot(loss)
plt.show()

one_test = np.ones((test_x.shape[0],1))
test_xone = np.hstack((test_x,one_test))
py1x = 1/(1+np.exp(-np.dot(test_xone,w)))
for i in range(test_xone.shape[0]):
    if py1x[i]>=0.5:
        py1x[i]=1
    else:
        py1x[i]=0
#print(py1x)
tp = 0
tn = 0
fp = 0
fn = 0
err = 0
acc = 0
pre = 0
rec = 0
f1 = 0

for i in range(test_xone.shape[0]):
    if py1x[i]==test_y[i] and py1x[i]==1:
        tp = tp+1
    if py1x[i]==test_y[i] and py1x[i]==0:
        tn = tn+1
    if py1x[i]!=test_y[i] and py1x[i]==1:
        fp = fp+1
    if py1x[i]!=test_y[i] and py1x[i]==0:
        fn = fn+1
err = (fp+fn)/(tp+tn+fp+fn)
acc = (tp+tn)/(tp+tn+fp+fn)
pre = tp/(tp+fp)
rec = tp/(tp+fn)
f1 = 2*pre*rec/(pre+rec)
print(tp)
print(tn)
print(fp)
print(fn)
print(err)
print(acc)
print(pre)
print(rec)
print(f1)



