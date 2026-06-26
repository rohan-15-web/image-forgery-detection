import torch
import torch.nn as nn
import cv2
import numpy as np

try:
    import segmentation_models_pytorch as smp
except ImportError:
    smp = None

def load_segformer_model(model_path, device="cpu"):
    if smp is None:
        print("[WARN] segmentation_models_pytorch is not installed. Skipping Segformer model.")
        return None
    try:
        model = smp.Segformer(encoder_name='mit_b0', encoder_weights=None, classes=1)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.to(device)
        model.eval()
        print(f"[OK] Loaded Segformer model: {model_path}")
        return model
    except Exception as e:
        print(f"[WARN] Failed to load Segformer model {model_path}: {e}")
        return None

def predict_segformer(model, pil_image, device="cpu"):
    if model is None:
        return 0.0, None
        
    img_rgb = np.array(pil_image.resize((224, 224)))
    img_rgb = img_rgb / 255.0
    input_tensor = torch.tensor(img_rgb).permute(2, 0, 1).unsqueeze(0).float().to(device)
    
    with torch.no_grad():
        out = model(input_tensor)
        out = torch.sigmoid(out) # Since classes=1, use sigmoid
        mask = out[0, 0].cpu().numpy()
        
    # Robust scoring using contours to avoid single pixel noise spikes
    binary_mask = (mask > 0.4).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    total_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 10:  # Ignore tiny noise
            total_area += area
            
    image_area = 224 * 224
    forged_ratio = total_area / image_area
    
    if forged_ratio > 0.25:
        # If the mask covers > 25% of the image, Segformer is likely hallucinating 
        # on a general texture or a massive Splicing image.
        score = 0.2
    elif forged_ratio > 0.01:
        # Use actual mean confidence of the mask rather than artificially boosting
        mean_conf = np.mean(mask[mask > 0.4])
        score = min(float(mean_conf), 0.99)
    else:
        # Downgrade if it's just tiny noise
        score = min(float(np.max(mask)) * 0.4, 0.49)
        
    return float(score), mask