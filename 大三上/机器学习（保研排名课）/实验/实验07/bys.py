import numpy
import numpy as np
import scipy.stats as stats
train_data = np.loadtxt('experiment_07_training_set.csv',delimiter=',')
test_data = np.loadtxt('experiment_07_testing_set.csv',delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:,:-1]
train_y = train_data[:,-1].reshape((num_train,1))
test_x = test_data[:,:-1]
test_y = test_data[:,-1].reshape((num_test,1))

pc1,pc2,pc3=0,0,0
for  i in range(num_train):
    if train_y[i] == 1:
        pc1 +=1
    if train_y[i] == 2:
        pc2 +=1
    if train_y[i] == 3:
        pc3 +=1
pc1 = pc1/num_train
pc2 = pc2/num_train
pc3 = pc3/num_train
print(pc1,pc2,pc3)

meanlist = [[0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]
sdlist = [[0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0], [0.0,0.0,0.0]]

train_y_Index = train_data[:, -1].astype(int)
def make_ProbabilityDensity(label,row,train_x,train_y):
    train_data_label_row = train_x[train_y ==label,row]
    mean = np.mean(train_data_label_row, 0)
    var = numpy.var(train_data_label_row)
    sd = numpy.sqrt(var)
    return mean,sd
for i in range(4):## x zhi
    print("特征x=",i)
    for  j in range(3):## y zhi
        print("标签y=",j+1)
        meantemp,sdtemp=make_ProbabilityDensity(j + 1, i, train_x,train_y_Index)
        sdlist[i][j]=sdtemp
        meanlist[i][j]=meantemp
        print(f"均值{meantemp:.2f}",f"标准差{sdtemp:.2f}")

def ProbabilityDensity(sd,mean,x):
    pd1 = 1/(np.sqrt(2*np.pi)*sd)
    pd2 = np.exp(-(x-mean)**2/(2*sd**2))
    pd = pd1*pd2
    return pd

def acc(pre_y,test_y):
    acc=0
    for i in range(num_test):
        if pre_y[i] == test_y[i]:
            acc +=1
    acc = acc/num_test
    return acc

def make_Predict(row,meanlist,sdlist):
    py1,py2,py3=0,0,0
    py1 = pc1*ProbabilityDensity(sdlist[0][0],meanlist[0][0],row[0])*ProbabilityDensity(sdlist[1][0],meanlist[1][0],row[1])*ProbabilityDensity(sdlist[2][0],meanlist[2][0],row[2])*ProbabilityDensity(sdlist[3][0],meanlist[3][0],row[3])
    py2 = pc2*ProbabilityDensity(sdlist[0][1],meanlist[0][1],row[0])*ProbabilityDensity(sdlist[1][1],meanlist[1][1],row[1])*ProbabilityDensity(sdlist[2][1],meanlist[2][1],row[2])*ProbabilityDensity(sdlist[3][1],meanlist[3][1],row[3])
    py3 = pc3*ProbabilityDensity(sdlist[0][2], meanlist[0][2], row[0]) * ProbabilityDensity(sdlist[1][2],meanlist[1][2], row[ 1]) * ProbabilityDensity( sdlist[2][2], meanlist[2][2], row[2]) * ProbabilityDensity(sdlist[3][2], meanlist[3][2], row[3])
    if py1 > py2:
        if py1 > py3:
            return 1
    if py3 > py2:
        if py3 > py1:
            return 3
    if py2 > py1:
        if py2 > py3:
            return 2

prey_y= np.zeros(num_test)
for i in range (num_test):
    row = test_x[i]
    prey_y[i]= make_Predict(row,meanlist,sdlist)
print(f"精度={acc(prey_y,test_y):.2f}")