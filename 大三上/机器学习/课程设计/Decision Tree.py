import numpy as np
import matplotlib.pyplot as plt
# read data from files
train_data = np.loadtxt('experiment_05_training_set.csv',delimiter=',')
test_data = np.loadtxt('experiment_05_testing_set.csv',delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:,:-1]/255
train_y = train_data[:,-1]
test_x = test_data[:,:-1]/255
test_y = test_data[:,-1]

