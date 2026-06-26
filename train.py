import os
import torch
import torch.nn as nn
import pandas as pd
from PIL import Image
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader, random_split
import torchvision.transforms as transforms
import torchvision.models as models
import random

# ================= CONFIG =================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BASE_PATH = "/kaggle/input/your-dataset-name"   # 🔥 CHANGE THIS

BATCH_SIZE = 16
EPOCHS = 30
LR = 1e-4
IMG_SIZE = 224

LABEL_MAP = {
    "authentic": 0,
    "copy-move": 1,
    "splicing": 2,
    "retouching": 3,
    "ai-generated": 4
}
NUM_CLASSES = len(LABEL_MAP)

torch.backends.cudnn.benchmark = True

# ================= PATCH FUNCTION =================
def random_patch(img, size=IMG_SIZE):
    w, h = img.size
    if w < size or h < size:
        return img.resize((size, size))

    x = random.randint(0, w - size)
    y = random.randint(0, h - size)
    return img.crop((x, y, x + size, y + size))

# ================= DATASET =================
class ForgeryDataset(Dataset):
    def __init__(self, csv_file, transform=None):
        self.df = pd.read_csv(csv_file)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        img_path = row["image_path"]

        if "kaggle" in BASE_PATH:
            img_path = os.path.join(BASE_PATH, img_path)

        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Missing: {img_path}")

        img = Image.open(img_path).convert("RGB")

        # Patch-based learning
        img = random_patch(img)

        if self.transform:
            img = self.transform(img)

        label = LABEL_MAP.get(row["forgery_type"], 0)

        return img, label

# ================= TRANSFORMS =================
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(0.2, 0.2, 0.2),
    transforms.ToTensor(),
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

# ================= LOAD DATA =================
full_dataset = ForgeryDataset("labels.csv", transform=train_transform)

train_size = int(0.85 * len(full_dataset))
val_size = len(full_dataset) - train_size

train_data, val_data = random_split(full_dataset, [train_size, val_size])

# 🔥 apply val transform
val_data.dataset.transform = val_transform

train_loader = DataLoader(
    train_data,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=2,
    pin_memory=True
)

val_loader = DataLoader(val_data, batch_size=BATCH_SIZE)

# ================= MODEL =================
class UltraModel(nn.Module):
    def __init__(self):
        super().__init__()

        self.backbone = models.efficientnet_b4(pretrained=True)
        self.backbone.classifier = nn.Identity()

        feature_dim = 1792

        self.embedding = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 128)
        )

        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(512, NUM_CLASSES)
        )

    def forward(self, x):
        features = self.backbone(x)
        embedding = self.embedding(features)
        logits = self.classifier(features)
        return logits, embedding

model = UltraModel().to(DEVICE)

if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)

# ================= LOSSES =================
ce_loss = nn.CrossEntropyLoss()
triplet_loss = nn.TripletMarginLoss(margin=1.0)

# ================= OPTIMIZER =================
optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

# 🔥 Scheduler
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3)

# 🔥 Mixed precision
scaler = torch.cuda.amp.GradScaler()

# ================= SAFE TRIPLET =================
def create_triplet_batch(images, labels):
    anchors, positives, negatives = [], [], []

    for i in range(len(images)):
        anchor = images[i]
        label = labels[i]

        pos_indices = (labels == label).nonzero(as_tuple=True)[0]
        neg_indices = (labels != label).nonzero(as_tuple=True)[0]

        if len(pos_indices) < 2 or len(neg_indices) == 0:
            continue

        pos_idx = random.choice(pos_indices)
        neg_idx = random.choice(neg_indices)

        anchors.append(anchor)
        positives.append(images[pos_idx])
        negatives.append(images[neg_idx])

    if len(anchors) == 0:
        return None, None, None

    return torch.stack(anchors), torch.stack(positives), torch.stack(negatives)

# ================= TRAIN =================
def train():
    best_acc = 0

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0

        loop = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}")

        for images, labels in loop:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            with torch.cuda.amp.autocast():
                logits, emb = model(images)
                loss_cls = ce_loss(logits, labels)

                anc, pos, neg = create_triplet_batch(images, labels)

                if anc is not None:
                    _, emb_a = model(anc.to(DEVICE))
                    _, emb_p = model(pos.to(DEVICE))
                    _, emb_n = model(neg.to(DEVICE))

                    loss_triplet = triplet_loss(emb_a, emb_p, emb_n)
                    loss = loss_cls + 0.3 * loss_triplet
                else:
                    loss = loss_cls

            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            total_loss += loss.item()
            loop.set_postfix(loss=loss.item())

        val_acc = validate()
        scheduler.step(val_acc)

        print(f"\nEpoch {epoch+1} Loss: {total_loss:.4f} | Val Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc

            save_path = "best_model.pth"
            if "kaggle" in BASE_PATH:
                save_path = "/kaggle/working/best_model.pth"

            torch.save(model.state_dict(), save_path)
            print("✅ Best model saved!")

# ================= VALIDATION =================
def validate():
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            logits, _ = model(images)
            _, preds = torch.max(logits, 1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

    return correct / total

# ================= RUN =================
if __name__ == "__main__":
    train()