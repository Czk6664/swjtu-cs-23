import numpy as np
import matplotlib.pyplot as plt
from sklearn import tree
# read data from files
load_data1 = np.loadtxt('experiment_08_training_set.csv',delimiter=',')
load_data2 = np.loadtxt('experiment_08_testing_set.csv',delimiter=',')
train_x = load_data1[:,:-1]
train_y = load_data1[:,-1]
test_x = load_data2[:,:-1]
test_y = load_data2[:,-1]

T = 20
test_errors = []
test_accs = []
for t in range(T):
    # print(train_x.shape)
    sample_weights = np.full(train_x.shape[0],1/train_x.shape[0])
    a = np.zeros(t+1)
    models = []
    train_errors = []
    for i in range(t+1):
        model = tree.DecisionTreeClassifier(random_state=1,criterion='entropy',max_depth = 2)
        model.fit(train_x,train_y,sample_weight=sample_weights)
        models.append(model)
        train_pred_y = model.predict(train_x)
        train_error = 0
        for j in range(train_x.shape[0]):
            train_error += (train_pred_y[j] != train_y[j]) * sample_weights[j]

        a[i] = 0.5 * np.log((1 - train_error) / train_error)
        train_errors.append(train_error)
        sample_weights = sample_weights * np.exp(-a[i] * train_y * train_pred_y)
        sample_weights = sample_weights / np.sum(sample_weights)

    result = np.zeros(test_x.shape[0])
    for i in range(t+1):
        test_pred_y = models[i].predict(test_x)
        result += a[i] * test_pred_y
    test_pred_y = np.sign(result)
    test_error = np.sum(test_pred_y != test_y) / test_y.shape[0]
    test_acc = 1 - test_error
    test_accs.append(test_acc)
    print('t = %d,test acc=%.2f' % (t+1, test_acc))
    test_errors.append(test_error)

plt.plot(range(1,T+1),test_accs)
plt.xlabel('T')
plt.ylabel('test acc')
plt.show()
