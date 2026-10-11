import numpy as np
load_data = np.loadtxt('experiment_01_dataset_02.csv',delimiter=',')
# print(load_data)
# print(load_data.shape)
tp,fp,fn,tn = 0,0,0,0
result1 = np.zeros((2,2))
result2 = np.zeros((2,2))
result3 = np.zeros((2,2))
result = [result1,result2,result3]
p = np.zeros(3)
r = np.zeros(3)
f1 = np.zeros(3)
for i in range(3):
    for j in range(load_data.shape[0]):
        if load_data[j,1] == load_data[j,i+2] and load_data[j,1] == 1:
            tp += 1
        elif load_data[j,1] != load_data[j,i+2] and load_data[j,1] == 1:
            fp += 1
        elif load_data[j,1] == load_data[j,i+2] and load_data[j,1] == 0:
            tn += 1
        elif load_data[j,1] != load_data[j,i+2] and load_data[j,1] == 0:
            fn += 1
    result[i][0][0] = tp
    result[i][0][1] = fp
    result[i][1][0] = fn
    result[i][1][1] = tn
    tp,fp,fn,tn = 0,0,0,0
    print(result[i])
    p[i]=result[i][0][0]/(result[i][0][0]+result[i][1][0])
    r[i]=result[i][0][0]/(result[i][0][0]+result[i][0][1])
    f1[i]=2*p[i]*r[i]/(p[i]+r[i])
    print(round(p[i],2),round(r[i],2),round(f1[i],2))
        