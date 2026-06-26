import os
import pandas as pd

rows = []

MASK_DIR = "generated_masks"

# ================= HELPER =================
def get_mask_path(img_path):
    mask_path = os.path.join(MASK_DIR, img_path).replace("\\", "/")
    return mask_path if os.path.exists(mask_path) else ""

# ================= CASIA =================
if os.path.exists("./CASIA/authentic"):
    for f in os.listdir("./CASIA/authentic"):
        img_path = f"CASIA/authentic/{f}"
        rows.append([img_path, "", "authentic"])
else:
    print("❌ CASIA authentic not found")

if os.path.exists("./CASIA/tampered"):
    for f in os.listdir("./CASIA/tampered"):
        img_path = f"CASIA/tampered/{f}"
        rows.append([img_path, get_mask_path(img_path), "copy-move"])  # 🔥 changed from unknown
else:
    print("❌ CASIA tampered not found")


# ================= CoMoFoD =================
if os.path.exists("./CoMoFod"):
    for f in os.listdir("./CoMoFod"):
        if f.endswith((".png", ".jpg")):
            img_path = f"CoMoFod/{f}"

            if "_B" in f:
                rows.append([img_path, "", "authentic"])
            elif "_F_" in f:
                rows.append([img_path, get_mask_path(img_path), "copy-move"])
else:
    print("❌ CoMoFod not found")


# ================= Coverage =================
if os.path.exists("./coverage"):
    for f in os.listdir("./coverage"):
        if f.endswith((".tif", ".png", ".jpg")):
            img_path = f"coverage/{f}"
            rows.append([img_path, get_mask_path(img_path), "splicing"])
else:
    print("❌ Coverage not found")


# ================= DeepFake =================
if os.path.exists("./deepfake"):
    for root, dirs, files in os.walk("./deepfake"):
        for f in files:
            if f.endswith((".jpg", ".png")):
                img_path = os.path.join(root, f).replace("\\", "/")

                if "real" in root.lower():
                    rows.append([img_path, "", "authentic"])
                else:
                    rows.append([img_path, get_mask_path(img_path), "ai-generated"])
else:
    print("❌ Deepfake dataset not found")


# ================= CREATE DATAFRAME =================
df = pd.DataFrame(rows, columns=["image_path", "mask_path", "forgery_type"])

# 🔥 CRITICAL FIX: remove NaN
df["mask_path"] = df["mask_path"].fillna("")

# 🔥 Remove invalid rows (image not found)
df = df[df["image_path"].apply(os.path.exists)]

# 🔥 Shuffle dataset (better training)
df = df.sample(frac=1).reset_index(drop=True)

# ================= SAVE =================
df.to_csv("labels.csv", index=False)

print("✅ labels.csv created successfully!")
print(f"📊 Total samples: {len(df)}")