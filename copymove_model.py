import torch
import cv2
import numpy as np
from torchvision import transforms
from model import load_comofod_model

def load_copymove_model(model_path, device="cpu"):
    try:
        return load_comofod_model(model_path, device=device)
    except Exception as e:
        print(f"[WARN] Failed to load Copy-Move PyTorch model {model_path}: {e}")
        return None

def predict_copymove(model, image, device="cpu"):
    comofod_mask_arr = None
    max_score = 0.0

    if model is not None:
        comofod_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        comofod_tensor = comofod_transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(comofod_tensor)
            prob_mask = torch.sigmoid(out)
            comofod_mask_arr = prob_mask.squeeze().cpu().numpy()
            
            # Robust scoring using contours
            binary_mask = (comofod_mask_arr > 0.5).astype(np.uint8) * 255
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            total_area = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 10:  # Ignore tiny noise
                    total_area += area
                    
            image_area = 256 * 256
            forged_ratio = total_area / image_area
            
            if forged_ratio > 0.25:
                # If the mask covers > 25% of the image, the U-Net is likely hallucinating 
                # on a general texture. True copy-move patches are rarely this large.
                max_score = 0.2
            elif forged_ratio > 0.005:
                # Use the natural confidence of the U-Net. We no longer artificially boost it,
                # so that Splicing can win if this is actually a Splicing anomaly.
                mean_conf = np.mean(comofod_mask_arr[comofod_mask_arr > 0.5])
                max_score = min(float(mean_conf), 0.99)
            else:
                max_score = min(float(prob_mask.max().item()) * 0.4, 0.49) # Downgrade if it's just tiny noise

    try:
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create()
        kp, des = sift.detectAndCompute(gray, None)
        if des is not None and len(des) > 2:
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des, des, k=3)
            
            valid_matches = []
            for match_group in matches:
                if len(match_group) >= 3:
                    m, n, o = match_group
                    if n.distance < 0.75 * o.distance:
                        x1, y1 = kp[n.queryIdx].pt
                        x2, y2 = kp[n.trainIdx].pt
                        distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                        if distance > 50:
                            valid_matches.append((x1, y1, x2, y2, x1 - x2, y1 - y2))
            
            from collections import defaultdict
            clusters = defaultdict(list)
            for match in valid_matches:
                x1, y1, x2, y2, dx, dy = match
                bin_dx = round(dx / 10) * 10
                bin_dy = round(dy / 10) * 10
                clusters[(bin_dx, bin_dy)].append(match)
                
            sorted_clusters = sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True)
            top_matches = []
            if len(sorted_clusters) > 0:
                top_matches.extend(sorted_clusters[0][1])
            if len(sorted_clusters) > 1:
                top_matches.extend(sorted_clusters[1][1])
                
            sift_mask = np.zeros_like(gray)
            match_count = len(top_matches) // 2  # Each pair appears twice (A->B and B->A)
            
            for match in top_matches:
                x1, y1, x2, y2, _, _ = match
                cv2.circle(sift_mask, (int(x1), int(y1)), 25, 255, -1)
                cv2.circle(sift_mask, (int(x2), int(y2)), 25, 255, -1)
                
            if match_count > 10:
                # Require at least 11 identical translation pairs to avoid false positives 
                # on highly repetitive textures like animal fur, brick walls, or symmetrical facial features.
                sift_conf = min(0.85, 0.5 + (match_count * 0.02)) 
                max_score = max(max_score, sift_conf)
                sift_mask_norm = cv2.resize(sift_mask, (256, 256)) / 255.0
                if comofod_mask_arr is None:
                    comofod_mask_arr = sift_mask_norm
                else:
                    comofod_mask_arr = np.maximum(comofod_mask_arr, sift_mask_norm)
    except Exception as e:
        print(f"SIFT Copy-Move failed: {e}")

    return max_score, comofod_mask_arr
