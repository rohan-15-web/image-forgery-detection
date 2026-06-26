t  fimport argparse
import os
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image, ImageDraw, ImageChops, ImageEnhance
from model import get_model


# ===============================
# 🔬 ELA
# ===============================
def convert_to_ela(image, quality=90):
    temp_path = "temp_ela.jpg"

    image = image.convert("RGB")
    image.save(temp_path, "JPEG", quality=quality)
    compressed = Image.open(temp_path)

    diff = ImageChops.difference(image, compressed)
    extrema = diff.getextrema()

    max_diff = max([ex[1] for ex in extrema])
    max_diff = max(max_diff, 1)

    scale = 255.0 / max_diff
    ela = ImageEnhance.Brightness(diff).enhance(scale)

    return ela


# ===============================
# 🔮 Highlight Tampered Areas
# ===============================
def highlight(image_path, model_path, model_type="cnn"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = get_model(model_type)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    patch_size = 128
    stride = 128

    w, h = image.size

    tampered_count = 0

    with torch.no_grad():
        for y in range(0, h, stride):
            for x in range(0, w, stride):

                box = (x, y, min(x + patch_size, w), min(y + patch_size, h))
                patch = image.crop(box)
                patch = patch.resize((128, 128))

                ela_patch = convert_to_ela(patch)

                rgb_tensor = transform(patch)
                ela_tensor = transform(ela_patch)

                x_input = torch.cat([rgb_tensor, ela_tensor], dim=0)
                x_input = x_input.unsqueeze(0).to(device)

                out = model(x_input)
                prob = F.softmax(out, dim=1)[0]
                tamper_prob = prob[1].item()

                # 🔥 threshold for marking tampered
                if tamper_prob > 0.5:
                    draw.rectangle(box, outline="red", width=3)
                    tampered_count += 1

    output_path = "tampered_output.png"
    image.save(output_path)

    print("\n✅ DONE")
    print(f"Tampered patches: {tampered_count}")
    print(f"Saved image: {output_path}")


# ===============================
# 🚀 Main
# ===============================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--model_path", default="models/model_best.pth")
    parser.add_argument("--model", default="cnn")

    args = parser.parse_args()

    highlight(args.image, args.model_path, args.model)