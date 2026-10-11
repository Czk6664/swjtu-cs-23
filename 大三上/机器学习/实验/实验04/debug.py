import numpy as np
print('NumPy version:', np.__version__)
try:
    data = np.loadtxt('experiment_04_training_set.csv', delimiter=',')
    print('Successfully loaded training data, shape:', data.shape)
except Exception as e:
    print('Error:', str(e))