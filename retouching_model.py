import torch
import torch.nn as nn
from torchvision import models
from torchvision import transforms
from PIL import Image

class RetouchClassifier(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.backbone = models.efficientnet_b0(pretrained=False)
        self.backbone.classifier = nn.Identity()
        self.fc = nn.Sequential(
            nn.Linear(1280, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
    def forward(self, x):
        x = self.backbone(x)
        x = self.fc(x)
        return x

def load_retouching_models(model_paths, device="cpu"):
    models_loaded = []
    for path in model_paths:
        try:
            model = RetouchClassifier()
            model.load_state_dict(torch.load(path, map_location=device))
            model.to(device)
            model.eval()
            models_loaded.append(model)
            print(f"[OK] Loaded PyTorch Retouching model: {path}")
        except Exception as e:
            print(f"[WARN] Failed to load PyTorch Retouching model {path}: {e}")
    return models_loaded

def predict_retouching(models, pil_image, device="cpu"):
    if not models:
        return 0.0, None, None
        
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    input_tensor = transform(pil_image).unsqueeze(0).to(device)
    
    max_score = 0.0
    best_model = None
    
    # We must ensure gradients can be computed for GradCAM later
    input_tensor.requires_grad = True
    
    for m in models:
        try:
            out = m(input_tensor)
            probs = torch.softmax(out, dim=1)
            score = probs[0][0].item()
            if score >= max_score:
                max_score = score
                best_model = m
        except Exception as e:
            print(f"Error predicting with retouching model: {e}")
            
    return max_score, best_model, input_tensor
