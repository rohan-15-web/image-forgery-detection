import cv2
import numpy as np

def detect_retouch(image_path):
    img = cv2.imread(image_path)
    blur = cv2.GaussianBlur(img, (5,5), 0)

    diff = cv2.absdiff(img, blur)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    _, mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)

    return mask