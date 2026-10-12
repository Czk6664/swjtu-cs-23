import time
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


class RandomSRDataset(Dataset):
    def __init__(self, length=2000, lr_size=32, scale=2):
        self.length = length
        self.lr_size = lr_size
        self.scale = scale

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        hr_size = self.lr_size * self.scale
        lr = torch.rand(3, self.lr_size, self.lr_size)
        hr = torch.rand(3, hr_size, hr_size)
        return lr, hr


class SimpleSRCNN(nn.Module):
    def __init__(self, scale=2):
        super().__init__()
        self.up = nn.Upsample(scale_factor=scale, mode="bilinear", align_corners=False)
        self.net = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=9, padding=4),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 3, kernel_size=5, padding=2),
        )

    def forward(self, x):
        x = self.up(x)
        return self.net(x)


def main():
    if not torch.cuda.is_available():
        print("CUDA 不可用，当前只能用 CPU。")
        return

    device = torch.device("cuda")
    print("GPU:", torch.cuda.get_device_name(0))

    dataset = RandomSRDataset(length=2000, lr_size=32, scale=2)
    loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True,
        num_workers=0,
        pin_memory=True,
    )

    model = SimpleSRCNN(scale=2).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    torch.cuda.reset_peak_memory_stats()
    start = time.time()

    model.train()
    for epoch in range(3):
        epoch_loss = 0.0
        epoch_start = time.time()

        for step, (lr, hr) in enumerate(loader):
            lr = lr.to(device, non_blocking=True)
            hr = hr.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            sr = model(lr)
            loss = criterion(sr, hr)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

            if step % 20 == 0:
                mem = torch.cuda.memory_allocated() / 1024**2
                print(
                    f"epoch={epoch+1} step={step:03d} "
                    f"loss={loss.item():.6f} mem={mem:.1f}MB"
                )

        print(
            f"[epoch {epoch+1}] "
            f"avg_loss={epoch_loss/len(loader):.6f} "
            f"time={time.time()-epoch_start:.1f}s"
        )

    total_time = time.time() - start
    peak_mem = torch.cuda.max_memory_allocated() / 1024**2
    print(f"总耗时: {total_time:.1f}s")
    print(f"峰值显存: {peak_mem:.1f}MB")


if __name__ == "__main__":
    main()
