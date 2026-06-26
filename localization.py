    import argparse
import os
import torch
import torch.nn.functional as F
import numpy as np
import cv2

from torchvision import transforms
from PIL import Image, ImageChops, ImageEnhance
from model import get_model


# ==============================
# ELA generation
# ==============================
def convert_to_ela(image, quality=90):
    temp = "temp_ela.jpg"
    image.save(temp, "JPEG", quality=quality)

    compressed = Image.open(temp)
    diff = ImageChops.difference(image, compressed)

    extrema = diff.getextrema()
    max_diff = max([e[1] for e in extrema])
    scale = 255.0 / max_diff if max_diff != 0 else 1

    ela = ImageEnhance.Brightness(diff).enhance(scale)
    return ela


# ==============================
# Localization
# ==============================
def localize(image_path, model_path):

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    model = get_model("cnn")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((128,128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485,0.456,0.406],
            std=[0.229,0.224,0.225]
        )
    ])

    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    patch_size = 128
    stride = 64

    heatmap = np.zeros((height, width))

    with torch.no_grad():

        for y in range(0, height-patch_size, stride):
            for x in range(0, width-patch_size, stride):

                patch = image.crop((x,y,x+patch_size,y+patch_size))
                ela = convert_to_ela(patch)

                rgb = transform(patch)
                ela = transform(ela)

                inp = torch.cat([rgb,ela],dim=0).unsqueeze(0).to(device)

                out = model(inp)

                prob = F.softmax(out,dim=1)[0][1].item()  # tampered probability

                heatmap[y:y+patch_size,x:x+patch_size] += prob


    heatmap = heatmap / heatmap.max()

    # convert to heatmap image
    heatmap_img = (heatmap*255).astype(np.uint8)
    heatmap_img = cv2.applyColorMap(heatmap_img, cv2.COLORMAP_JET)

    original = cv2.imread(image_path)

    heatmap_img = cv2.resize(heatmap_img,(original.shape[1],original.shape[0]))

    overlay = cv2.addWeighted(original,0.6,heatmap_img,0.4,0)

    cv2.imwrite("tamper_heatmap.png",heatmap_img)
    cv2.imwrite("tamper_overlay.png",overlay)

    print("\nLocalization complete")
    print("Saved:")
    print("tamper_heatmap.png")
    print("tamper_overlay.png")


# ==============================
# Main
# ==============================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--image",required=True)
    parser.add_argument("--model_path",default="models/model_best.pth")

    args = parser.parse_args()

    localize(args.image,args.model_path)
