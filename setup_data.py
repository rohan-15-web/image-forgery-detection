import os
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np

def create_synthetic_datasets():
    """
    Automated dataset generation pipeline to fulfill the ONE-COMMAND requirement.
    Produces structurally compliant data without requiring massive external downloads.
    """
    print("🚀 Initializing Setup Data Pipeline...")
    base_dir = "data"
    os.makedirs(f"{base_dir}/images", exist_ok=True)
    os.makedirs(f"{base_dir}/masks", exist_ok=True)
    
    rows = []
    
    # Generate 100 mock images (50 authentic, 25 copy-move, 25 splicing)
    print("⏳ Generating unified synthetic dataset...")
    for i in range(1, 101):
        # Create base noise image
        img_arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_arr)
        
        filepath = f"{base_dir}/images/synthetic_{i}.jpg"
        maskpath = f"{base_dir}/masks/synthetic_{i}.png"
        
        if i <= 50:
            # Authentic
            img.save(filepath)
            rows.append([filepath, "", "authentic"])
            
        elif i <= 75:
            # Copy-Move Simulation
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 100, 100], fill=(255, 0, 0))
            draw.rectangle([150, 150, 200, 200], fill=(255, 0, 0)) # Copied Region
            img.save(filepath)
            
            mask = Image.new("L", (256, 256), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rectangle([150, 150, 200, 200], fill=255)
            mask.save(maskpath)
            
            rows.append([filepath, maskpath, "copy-move"])
            
        else:
            # Splicing Simulation
            draw = ImageDraw.Draw(img)
            draw.ellipse([100, 100, 180, 180], fill=(0, 255, 0))
            img.save(filepath)
            
            mask = Image.new("L", (256, 256), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([100, 100, 180, 180], fill=255)
            mask.save(maskpath)
            
            rows.append([filepath, maskpath, "splicing"])
            
    # Standardize merged datasets
    df = pd.DataFrame(rows, columns=["image_path", "mask_path", "forgery_type"])
    df.to_csv(f"{base_dir}/labels_unified.csv", index=False)
    print(f"✅ Auto-Data Setup Complete: {len(df)} images ready in {base_dir}/")

if __name__ == "__main__":
    create_synthetic_datasets()
