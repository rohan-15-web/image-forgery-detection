import torch
import torch.nn as nn
from torchvision import models
import cv2
import numpy as np
import os
from PIL import Image

try:
    import segmentation_models_pytorch as smp
except ImportError:
    pass

class CasiaModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 56 * 56, 128),
            nn.ReLU(),
            nn.Linear(128, 2)
        )
    def forward(self, x):
        x = self.conv(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x

def load_comofod_model(model_path, device="cpu"):
    if 'smp' not in globals():
        print("[WARN] segmentation_models_pytorch is not installed. Skipping Comofod model.")
        return None
    model = smp.UnetPlusPlus(encoder_name="resnet34", encoder_weights=None, in_channels=3, classes=1)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def load_casia_model(model_path, device="cpu"):
    model = CasiaModel()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def get_model(device="cpu", pretrained=False, num_classes=4, model_path=None):
    if pretrained:
        model = models.efficientnet_b0(pretrained=True)
    else:
        model = models.efficientnet_b0(pretrained=False)
        
    model.classifier[1] = nn.Sequential(
        nn.Linear(model.classifier[1].in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256, num_classes)
    )
    
    if model_path and os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        
    model = model.to(device)
    return model

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_full_backward_hook(self.save_gradient)
        
    def save_activation(self, module, input, output):
        self.activations = output
        
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
        
    def generate_heatmap(self, input_tensor, class_idx):
        self.model.eval()

        output = self.model(input_tensor)
        self.model.zero_grad()

        score = output[0, class_idx]
        score.backward()

        gradients = self.gradients[0].cpu().data.numpy()
        activations = self.activations[0].cpu().data.numpy()

        weights = np.mean(gradients, axis=(1, 2))

        cam = np.zeros(activations.shape[1:], dtype=np.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = np.maximum(cam, 0)

        cam = cv2.resize(cam, (224, 224))
        cam = (cam - cam.min()) / (cam.max() + 1e-8)

        return cam

def overlay_heatmap(img_path, heatmap, save_path):
    # Read original image
    org_img = cv2.imread(img_path)
    if org_img is None:
        return
        
    # Resize the heatmap to match the image dimensions
    heatmap_resized = cv2.resize(heatmap, (org_img.shape[1], org_img.shape[0]))
    
    # Ensure the heatmap is properly scaled to [0, 1]
    heatmap_resized = heatmap_resized.astype(np.float32)
    h_min, h_max = np.min(heatmap_resized), np.max(heatmap_resized)
    if h_max > h_min:
        heatmap_norm = (heatmap_resized - h_min) / (h_max - h_min)
    else:
        heatmap_norm = np.zeros_like(heatmap_resized)
        
    # Apply JET colormap
    heatmap_color = cv2.applyColorMap(
        np.uint8(heatmap_norm * 255),
        cv2.COLORMAP_JET
    )

    # Overlay with original image using addWeighted
    overlay = cv2.addWeighted(
        org_img,
        0.6,
        heatmap_color,
        0.4,
        0
    )
            
    cv2.imwrite(save_path, overlay)
