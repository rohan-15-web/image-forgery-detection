import cv2
import numpy as np

def detect_copy_move(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=2000)
    kp, des = orb.detectAndCompute(gray, None)

    if des is None:
        return None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des, des)

    suspicious_points = []

    for m in matches:
        if m.distance < 30 and m.queryIdx != m.trainIdx:
            pt1 = kp[m.queryIdx].pt
            pt2 = kp[m.trainIdx].pt

            if np.linalg.norm(np.array(pt1) - np.array(pt2)) > 20:
                suspicious_points.append((pt1, pt2))

    mask = np.zeros(gray.shape, dtype=np.uint8)

    for (x1, y1), (x2, y2) in suspicious_points:
        cv2.circle(mask, (int(x1), int(y1)), 10, 255, -1)
        cv2.circle(mask, (int(x2), int(y2)), 10, 255, -1)

    return mask