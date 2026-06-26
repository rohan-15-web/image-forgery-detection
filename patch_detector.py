import torch
import numpy as np
from PIL import Image

def extract_patches(image, patch_size=64, stride=32):
    image = np.array(image)
    h, w, _ = image.shape

    patches = []
    coords = []

    for y in range(0, h - patch_size, stride):
        for x in range(0, w - patch_size, stride):
            patch = image[y:y+patch_size, x:x+patch_size]
            patches.append(patch)
            coords.append((x, y))

    return patches, coords


def analyze_patches(model, patches, transform, device):
    suspicious = []

    for patch in patches:
        patch_img = Image.fromarray(patch)
        input_tensor = transform(patch_img).unsqueeze(0).to(device)

        output = model(input_tensor)
        prob = torch.softmax(output, dim=1)
        conf, pred = torch.max(prob, 1)

        if pred.item() != 0 and conf.item() > 0.6:
            suspicious.append(True)
        else:
            suspicious.append(False)

    return suspicious