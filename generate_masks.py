import os
import cv2
import numpy as np
from tqdm import tqdm

# ================= CONFIG =================
DATASET_ROOT = "."
MASK_DIR = "./generateteI nid_masks"
os.makedirs(MASK_DIR, exist_ok=True)

# ================= UTILS =================
def save_mask(mask, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, mask)

def preprocess(img):
    return cv2.GaussianBlur(img, (5,5), 0)

# ================= COPY-MOVE (CoMoFoD) =================
def generate_copy_move_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(gray, None)

    mask = np.zeros(gray.shape, dtype=np.uint8)

    if des is None or len(kp) < 2:
        return mask

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des, des, k=2)

    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            x, y = kp[m.queryIdx].pt
            cv2.circle(mask, (int(x), int(y)), 5, 255, -1)

    return cv2.dilate(mask, None)

# ================= SPLICING =================
def generate_splicing_mask(img):
    # Perform Error Level Analysis (ELA) for high-resolution splicing detection
    try:
        # Encode original image to JPEG with 90% quality
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, encoded_img = cv2.imencode('.jpg', img, encode_param)
        
        # Decode back to image
        compressed_img = cv2.imdecode(encoded_img, 1)
        
        # Calculate absolute difference
        diff = cv2.absdiff(img, compressed_img)
        
        # Convert to grayscale
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Enhance the error level signal
        ela_mask = cv2.normalize(gray_diff, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply a subtle blur to smooth the noise but keep sharp boundaries
        ela_mask = cv2.GaussianBlur(ela_mask, (5, 5), 0)
        
        # Convert to 0-1 float array for heatmap blending
        return ela_mask.astype(np.float32) / 255.0
    except Exception as e:
        print("ELA Failed:", e)
        return np.zeros((img.shape[0], img.shape[1]), dtype=np.float32)

# ================= RETOUCHING =================
def generate_retouch_mask(img):
    blur = cv2.GaussianBlur(img, (21, 21), 0)
    diff = cv2.absdiff(img, blur)

    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    # Highlight smooth areas (where diff is low)
    _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
    
    # We only want to highlight smooth areas ON THE FACE
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 4)
    
    face_mask = np.zeros_like(mask)
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # Shrink the face box slightly to avoid background/hair
            pad_x, pad_y = int(w * 0.1), int(h * 0.1)
            cv2.rectangle(face_mask, (x + pad_x, y + pad_y), (x+w - pad_x, y+h - pad_y), 255, -1)
    else:
        # If no face detected, assume center of image
        h, w = mask.shape
        cv2.rectangle(face_mask, (int(w*0.2), int(h*0.2)), (int(w*0.8), int(h*0.8)), 255, -1)
        
    final_mask = cv2.bitwise_and(mask, face_mask)
    
    # Morphological opening to remove noise
    kernel = np.ones((5,5), np.uint8)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)
    
    return final_mask

# ================= AI GENERATED =================
def generate_ai_mask(img):
    # ================= STEP 1: GRAYSCALE =================
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ================= STEP 2: FREQUENCY DOMAIN =================
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.log(np.abs(fshift) + 1)

    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    magnitude = np.uint8(magnitude)

    # ================= STEP 3: LAPLACIAN (EDGE NOISE) =================
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    lap = np.uint8(np.absolute(lap))

    # ================= STEP 4: COMBINE =================
    combined = cv2.addWeighted(magnitude, 0.6, lap, 0.4, 0)

    # ================= STEP 5: THRESHOLD =================
    _, mask = cv2.threshold(combined, 30, 255, cv2.THRESH_BINARY)

    # ================= STEP 6: CLEAN =================
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask

# ================= MAIN =================
def process_dataset():
    for root, dirs, files in os.walk(DATASET_ROOT):
        for file in tqdm(files):
            if not file.lower().endswith((".jpg", ".png", ".tif")):
                continue

            img_path = os.path.join(root, file)
            img = cv2.imread(img_path)

            if img is None:
                continue

            relative_path = os.path.relpath(img_path, DATASET_ROOT)
            save_path = os.path.join(MASK_DIR, relative_path)

            # ================= DETECT TYPE =================
            lower_path = img_path.lower()

            if "comofod" in lower_path or "_f_" in file.lower():
                mask = generate_copy_move_mask(img)

            elif "coverage" in lower_path:
                mask = generate_splicing_mask(img)

            elif "deepfake" in lower_path or "fake" in lower_path:
                mask = generate_ai_mask(img)

            elif "retouch" in lower_path:
                mask = generate_retouch_mask(img)

            else:
                # fallback
                mask = generate_splicing_mask(img)

            save_mask(mask, save_path)

    print("✅ All masks generated successfully!")

# ================= RUN =================
if __name__ == "__main__":
    process_dataset()