# coding=utf-8
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset ,DataLoader, random_split 

# read data from files
train_data = np.loadtxt('experiment_05_training_set.csv',delimiter=',')
test_data = np.loadtxt('experiment_05_testing_set.csv',delimiter=',')
num_train = train_data.shape[0]
num_test = test_data.shape[0]
train_x = train_data[:,:-1]/255
train_y = train_data[:,-1]
test_x = test_data[:,:-1]/255
test_y = test_data[:,-1]

class mnistdataset(Dataset):
    def __init__(self,datax : np.ndarray, datay:np.ndarray):
        self.datax = datax.reshape(-1,1,28,28).astype(np.float32)
        self.datay = datay.astype(np.int64)
    def __len__(self):
        return self.datax.shape[0]
    def __getitem__(self, index):
        x = torch.from_numpy(self.datax[index])
        y = torch.tensor(self.datay[index], dtype=torch.long)
        return x, y

train_dataset = mnistdataset(train_x,train_y)#实例化类
test_dataset = mnistdataset(test_x, test_y)

train_rate = 0.8
valid_rate = 1-train_rate
train_size = int(len(train_dataset) * train_rate)
valid_size = len(train_dataset) - train_size
trainset, validset = random_split(train_dataset, [train_size, valid_size])

def make_dataloader(dataset,batch_size=64,shuffle=True):
    return DataLoader(dataset,batch_size=batch_size,shuffle=shuffle)

trainloader = make_dataloader(trainset)
validloader = make_dataloader(validset,shuffle=False) 
testloader = make_dataloader(test_dataset,shuffle=False)  

class mnistcnn(nn.Module):# 新建卷积神经网络类集成nn.Module类
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        self.fc_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128*7*7, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 10)
        )
    def forward(self,x):
        x = self.conv(x)
        x = self.fc_head(x)
        return x


def run_epoch(model,loss,optimizer,device,dataloader):# 定义训练一轮的函数
    model.train()
    running_loss = 0.0
    running_acc = 0.0
    for batch_x, batch_y in dataloader:
        batch_x = batch_x.to(device)
        batch_y = batch_y.to(device)
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss_value = loss(outputs, batch_y)
        loss_value.backward()
        optimizer.step()
        running_loss += loss_value.item()
        running_acc += (outputs.argmax(dim=1) == batch_y).float().mean().item()
    return running_loss/len(dataloader), running_acc/len(dataloader)

def validate_epoch(model,loss,device,dataloader):
    model.eval()
    run_loss  = 0
    run_acc = 0 
    
    with torch.no_grad():
        for batch_x, batch_y in dataloader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            outputs = model(batch_x)
            loss_value = loss(outputs, batch_y)
            run_loss += loss_value.item()
            run_acc += (outputs.argmax(dim=1) == batch_y).float().mean().item()
    return run_loss/len(dataloader), run_acc/len(dataloader)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print (f"设备: {device}")
model = mnistcnn().to(device)
loss = nn.CrossEntropyLoss()
learn_rate = 0.001 
adam_optimizer = optim.Adam(model.parameters(), lr=learn_rate)

epochs = 20
train_losses, train_accs = [], []
val_losses, val_accs = [], []
best_acc = 0

print("开始训练cnn模型")
for epoch in range(epochs):
    train_loss,train_acc = run_epoch(model,loss,adam_optimizer,device,trainloader)
    val_loss,val_acc = validate_epoch(model,loss,device,validloader)
    train_losses.append(train_loss)
    train_accs.append(train_acc)
    val_losses.append(val_loss)
    val_accs.append(val_acc)
    print(f"第 {epoch+1}/{epochs}轮: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), "mnist_best_model.pth")
        print(f"保存最优模型，当前最优模型准确率: {best_acc:.4f}")
print("训练结束")

print("开始测试cnn模型")
model.load_state_dict(torch.load("mnist_best_model.pth"))
test_loss, test_acc = validate_epoch(model, loss, device, testloader)
print(f"测试集损失: {test_loss:.4f}, 测试集准确率: {test_acc:.4f}")

plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses, label="Train Loss")
plt.plot(val_losses, label="Val Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.subplot(1, 2, 2)
plt.plot(train_accs, label="Train Acc")
plt.plot(val_accs, label="Val Acc")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend()
plt.grid(alpha=0.3)
plt.show()