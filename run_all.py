import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import pandas as pd
from tqdm import tqdm

from setup_data import create_synthetic_datasets

class PatchDataset(Dataset):
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.label_map = {"copy-move": 0, "splicing": 1, "inpainting": 2}
        
        # Filter for valid forged types only to train the patch classifier
        self.df = self.df[self.df["forgery_type"].isin(self.label_map.keys())].reset_index(drop=True)
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = Image.open(row["image_path"]).convert("RGB")
        tensor = self.transform(img)
        label = self.label_map.get(row["forgery_type"], 0)
        return tensor, torch.tensor(label, dtype=torch.long)

def train_patch_classifier():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🚀 Training Lightweight Patch Classifier (MobileNetV3 on {device})...")
    
    dataset = PatchDataset("labels.csv")
    loader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    model = models.mobilenet_v3_small(pretrained=True)
    
    # Freeze backbone
    for param in model.parameters():
        param.requires_grad = False
        
    # Expose classification head (copy-move, splicing, inpainting)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 3)
    model.to(device)
    
    model.train()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    
    # Minimal epochs for fast convergence demonstration
    EPOCHS = 20
    for epoch in range(EPOCHS):
        running_loss = 0.0
        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        for imgs, labels in pbar:
            imgs, labels = imgs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            pbar.set_postfix({"Loss": running_loss/(pbar.n+1)})
            
    torch.save(model.state_dict(), "patch_model.pth")
    print("✅ Fast Plugin Pipeline Weights saved to patch_model.pth")

if __name__ == "__main__":
    print("-" * 50)
    print("ANTIGRAVITY MODE: FULL AUTOMATION PIPELINE")
    print("-" * 50)
    
    # Step 1: Auto Download/Merge/Format Datasets
    # create_synthetic_datasets() # Skipped! User has real datasets now.
    
    # Step 2: Extract patches, Train the Module and Save Weights
    train_patch_classifier()
    
    print("-" * 50)
    print("🎉 Antigravity Pipeline Execution Complete! Ready to Plugin!")
