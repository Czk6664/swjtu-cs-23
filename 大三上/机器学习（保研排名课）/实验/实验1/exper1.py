import numpy as np
load_data = np.loadtxt('experiment_01_dataset_01.csv',delimiter=',')
# print(load_data)
# print(load_data.shape)
ssetotal = 0
maetotal = 0
sample = np.zeros((3,4))
for j in range(3):
    for i in range(load_data.shape[0]):
        ssetotal = (load_data[i,1]-load_data[i,j+2])**2 + ssetotal
        maetotal = abs(load_data[i,1]-load_data[i,j+2]) + maetotal
    sample[j][0] = ssetotal
    sample[j][1] = ssetotal/load_data.shape[0]
    sample[j][3] = maetotal/load_data.shape[0]
    sample[j][2] = np.sqrt(sample[j][1])
    ssetotal = 0
    maetotal = 0
print(round(sample[0][0],2),round(sample[0][1],2),round(sample[0][2],2),round(sample[0][3],2))
print(round(sample[1][0],2),round(sample[1][1],2),round(sample[1][2],2),round(sample[1][3],2))
print(round(sample[2][0],2),round(sample[2][1],2),round(sample[2][2],2),round(sample[2][3],2))