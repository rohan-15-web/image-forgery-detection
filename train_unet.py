import os
import cv2
import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader, random_split
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from tqdm import tqdm

# ================= CONFIG =================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BASE_PATH = "/kaggle/input/your-dataset-name"
CSV_PATH = "labels.csv"

torch.backends.cudnn.benchmark = True

# ================= DATA AUGMENT =================
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128,128)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor()
])

# ================= DATASET =================
class ForgeryDataset(Dataset):
    def __init__(self, csv_file):
        self.data = pd.read_csv(csv_file)
        self.data["mask_path"] = self.data["mask_path"].fillna("")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]

        img_path = os.path.join(BASE_PATH, row["image_path"])
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = transform(img)

        mask_path = row["mask_path"]
        if mask_path != "":
            mask_path = os.path.join(BASE_PATH, mask_path)

        if mask_path != "" and os.path.exists(mask_path):
            mask = cv2.imread(mask_path, 0)
            mask = cv2.resize(mask, (128,128))
            mask = mask / 255.0
        else:
            mask = np.zeros((128,128))

        mask = torch.tensor(mask).unsqueeze(0).float()

        return img, mask

# ================= MODEL =================
class EfficientUNet(nn.Module):
    def __init__(self):
        super().__init__()

        backbone = models.efficientnet_b4(pretrained=True)

        self.encoder = backbone.features

        self.up1 = nn.ConvTranspose2d(1792, 512, 2, stride=2)
        self.conv1 = nn.Conv2d(512, 256, 3, padding=1)

        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv2 = nn.Conv2d(128, 64, 3, padding=1)

        self.up3 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.conv3 = nn.Conv2d(32, 16, 3, padding=1)

        self.out = nn.Conv2d(16, 1, 1)

    def forward(self, x):
        x = self.encoder(x)

        x = self.up1(x)
        x = self.conv1(x)

        x = self.up2(x)
        x = self.conv2(x)

        x = self.up3(x)
        x = self.conv3(x)

        return torch.sigmoid(self.out(x))

# ================= LOSS =================
class DiceLoss(nn.Module):
    def forward(self, pred, target):
        smooth = 1
        pred = pred.view(-1)
        target = target.view(-1)
        inter = (pred * target).sum()
        return 1 - (2*inter + smooth)/(pred.sum()+target.sum()+smooth)

# ================= TRAIN =================
def train():
    dataset = ForgeryDataset(CSV_PATH)

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=16)

    model = EfficientUNet().to(DEVICE)

    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)

    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    bce = nn.BCELoss()
    dice = DiceLoss()

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2)

    scaler = torch.cuda.amp.GradScaler()

    for epoch in range(10):
        model.train()
        train_loss = 0

        for img, mask in tqdm(train_loader):
            img, mask = img.to(DEVICE), mask.to(DEVICE)

            with torch.cuda.amp.autocast():
                pred = model(img)
                loss = bce(pred, mask) + dice(pred, mask)

            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()

        # ===== VALIDATION =====
        model.eval()
        val_loss = 0

        with torch.no_grad():
            for img, mask in val_loader:
                img, mask = img.to(DEVICE), mask.to(DEVICE)
                pred = model(img)
                val_loss += (bce(pred, mask) + dice(pred, mask)).item()

        scheduler.step(val_loss)

        print(f"Epoch {epoch+1} | Train: {train_loss:.4f} | Val: {val_loss:.4f}")

    torch.save(model.state_dict(), "efficient_unet.pth")
    print("✅ PRO MAX model saved!")

# ================= RUN =================
if __name__ == "__main__":
    train()