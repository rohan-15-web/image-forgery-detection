import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
import cv2
from PIL import Image
import os

# ================= CONFIG =================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 128

LABEL_MAP = ["authentic", "copy-move", "splicing", "retouching", "ai-generated"]

# ================= TRANSFORM =================
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

# ================= LOAD CLASSIFIER =================
def load_classifier():
    model = models.efficientnet_b4(pretrained=False)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(LABEL_MAP))
    model.load_state_dict(torch.load("best_model.pth", map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

# ================= LOAD UNET =================
class UNet(nn.Module):
    def __init__(self):
        super().__init__()

        def C(in_c, out_c):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, 3, padding=1),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_c, out_c, 3, padding=1),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True)
            )

        self.down1 = C(3, 64)
        self.pool1 = nn.MaxPool2d(2)

        self.down2 = C(64, 128)
        self.pool2 = nn.MaxPool2d(2)

        self.down3 = C(128, 256)
        self.pool3 = nn.MaxPool2d(2)

        self.middle = C(256, 512)

        self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.conv3 = C(512, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv2 = C(256, 128)

        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv1 = C(128, 64)

        self.out = nn.Conv2d(64, 1, 1)

    def forward(self, x):
        d1 = self.down1(x)
        d2 = self.down2(self.pool1(d1))
        d3 = self.down3(self.pool2(d2))

        m = self.middle(self.pool3(d3))

        u3 = self.up3(m)
        u3 = torch.cat([u3, d3], dim=1)
        u3 = self.conv3(u3)

        u2 = self.up2(u3)
        u2 = torch.cat([u2, d2], dim=1)
        u2 = self.conv2(u2)

        u1 = self.up1(u2)
        u1 = torch.cat([u1, d1], dim=1)
        u1 = self.conv1(u1)

        return torch.sigmoid(self.out(u1))

def load_unet():
    model = UNet().to(DEVICE)
    model.load_state_dict(torch.load("unet_model.pth", map_location=DEVICE))
    model.eval()
    return model

# ================= GRADCAM =================
class GradCAM:
    def __init__(self, model):
        self.model = model
        self.gradients = None
        self.activations = None

        target_layer = model.features[-1]

        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_full_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, x, class_idx):
        output = self.model(x)
        self.model.zero_grad()

        loss = output[0, class_idx]
        loss.backward()

        gradients = self.gradients[0].cpu().numpy()
        activations = self.activations[0].cpu().numpy()

        weights = np.mean(gradients, axis=(1, 2))
        cam = np.zeros(activations.shape[1:], dtype=np.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = np.maximum(cam, 0)
        cam = cv2.resize(cam, (IMG_SIZE, IMG_SIZE))
        cam = (cam - cam.min()) / (cam.max() + 1e-8)

        return cam

# ================= COPY-MOVE =================
def copy_move_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(gray, None)

    if des is None:
        return np.zeros_like(gray)

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des, des, k=2)

    mask = np.zeros_like(gray)

    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            x1, y1 = kp[m.queryIdx].pt
            x2, y2 = kp[m.trainIdx].pt

            if abs(x1 - x2) > 10 or abs(y1 - y2) > 10:
                cv2.circle(mask, (int(x1), int(y1)), 5, 255, -1)
                cv2.circle(mask, (int(x2), int(y2)), 5, 255, -1)

    return mask / 255.0

# ================= LOAD MODELS ONCE =================
classifier = load_classifier()
unet = load_unet()
gradcam = GradCAM(classifier)

# ================= PREDICT =================
def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    img_np = np.array(image)

    input_tensor = transform(image).unsqueeze(0).to(DEVICE)

    # ===== CLASSIFICATION =====
    outputs = classifier(input_tensor)
    probs = torch.softmax(outputs, dim=1)
    pred_class = torch.argmax(probs).item()
    confidence = probs[0][pred_class].item()

    label = LABEL_MAP[pred_class]

    # ===== UNET MASK =====
    with torch.no_grad():
        unet_mask = unet(input_tensor)[0][0].cpu().numpy()

    # ===== GRADCAM =====
    cam = gradcam.generate(input_tensor.clone(), pred_class)

    # ===== COPY MOVE =====
    copy_mask = copy_move_detection(img_np)

    # ===== FUSION =====
    fused = 0.5 * unet_mask + 0.3 * cam + 0.2 * copy_mask
    fused = np.clip(fused, 0, 1)

    # ===== VISUALIZATION =====
    heatmap = cv2.applyColorMap(np.uint8(255 * fused), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_np, 0.6, heatmap, 0.4, 0)

    # ===== SAVE =====
    os.makedirs("results", exist_ok=True)
    output_path = "results/output.jpg"
    cv2.imwrite(output_path, overlay)

    print(f"Prediction: {label} ({confidence*100:.2f}%)")
    print(f"Saved: {output_path}")

    return label, output_path

# ================= RUN =================
if __name__ == "__main__":
    predict_image("test.jpg")