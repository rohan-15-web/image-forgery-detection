import os
import torch
import torchvision.transforms as transforms
from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from datetime import datetime
import numpy as np
import cv2 

# Import visualization tools
from model import overlay_heatmap

import copymove_model
import splicing_model
import retouching_model
import segmentation_model
import generate_masks


import logging
try:
    import tensorflow as tf
    tf.get_logger().setLevel(logging.ERROR)
    
    # Monkey-patch Dense layer to ignore quantization_config which causes loading errors
    original_from_config = tf.keras.layers.Dense.from_config
    def patched_from_config(cls, config):
        config.pop('quantization_config', None)
        return original_from_config(config)
    tf.keras.layers.Dense.from_config = classmethod(patched_from_config)
    
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False

# ================= CONFIG =================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ================= LOAD MODELS =================
print("Loading Models...")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# 1. Copy-Move Forgery
comofod_model_path = os.path.join("model", "best_model_comofod.pth")
cm_model = copymove_model.load_copymove_model(comofod_model_path, device=DEVICE)

# 2. Splicing Forgery
splicing_model_paths = [
    os.path.join("model", "best_model_finetuned_splicing.keras"),
    os.path.join("model", "best_model_splicing.keras"),
    os.path.join("model", "forgery_detector_splicing.keras")
]
spl_models = splicing_model.load_splicing_models(splicing_model_paths)

# 3. Face Retouching Forgery
retouching_model_paths = [
    os.path.join("model", "best_retouch_classifier.pth")
]
ret_models = retouching_model.load_retouching_models(retouching_model_paths, device=DEVICE)

# 4. Segformer Forgery
segformer_model_path = os.path.join("model", "best_segformer_b0.pth")
seg_model = segmentation_model.load_segformer_model(segformer_model_path, device=DEVICE)

# ================= APP SETUP =================
app = Flask(__name__)
CORS(app, origins="*")

app.config['SECRET_KEY'] = 'image-forgery-super-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forgery_shield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = "static/uploads"
HEATMAP_FOLDER = "static/heatmaps"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

# ================= MODELS =================
class DetectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_image_url = db.Column(db.String(512))
    heatmap_image_url = db.Column(db.String(512))
    prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ================= HISTORY ENDPOINT =================
@app.route("/api/history", methods=["GET"])
def history():
    records = DetectionRecord.query.order_by(DetectionRecord.upload_date.desc()).all()
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "filename": r.filename,
            "prediction": r.prediction,
            "confidence": r.confidence,
            "upload_date": r.upload_date.strftime("%m/%d/%Y"),
            "original_image_url": r.original_image_url,
            "heatmap_image_url": r.heatmap_image_url
        })
    return jsonify(result), 200

# ================= GRADCAM LOGIC =================
def make_keras_gradcam_heatmap(img_array, model, last_conv_layer_name=None, pred_index=None, invert_grads=False):
    if not KERAS_AVAILABLE:
        return None
    try:
        import tensorflow as tf
        import numpy as np
        import cv2

        base_model = None
        for layer in model.layers:
            if isinstance(layer, tf.keras.Model):
                base_model = layer
                break
                
        if base_model is not None:
            for layer in reversed(base_model.layers):
                if hasattr(layer, 'output') and len(layer.output.shape) == 4:
                    last_conv_layer_name = layer.name
                    break
            
            if last_conv_layer_name is None: return None
            
            inner_grad_model = tf.keras.models.Model(
                [base_model.inputs], [base_model.get_layer(last_conv_layer_name).output, base_model.output]
            )
            
            with tf.GradientTape() as tape:
                inputs = tf.cast(img_array, tf.float32)
                last_conv_layer_output, base_output = inner_grad_model(inputs)
                
                x = base_output
                base_idx = model.layers.index(base_model)
                for layer in model.layers[base_idx+1:]:
                    x = layer(x)
                    
                preds = x
                if pred_index is None:
                    pred_index = tf.argmax(preds[0])
                class_channel = preds[:, pred_index]

            grads = tape.gradient(class_channel, last_conv_layer_output)
            if invert_grads:
                grads = -grads
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            last_conv_layer_output = last_conv_layer_output[0]
            heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)
            heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)

            heatmap_np = heatmap.numpy()
            heatmap_np = cv2.resize(heatmap_np, (224, 224))
            if np.max(heatmap_np) > 0:
                heatmap_np = heatmap_np / np.max(heatmap_np)
            return heatmap_np

        # Original logic for non-nested models
        if last_conv_layer_name is None:
            for layer in reversed(model.layers):
                if 'conv' in layer.name.lower() or isinstance(layer, tf.keras.layers.Conv2D):
                    last_conv_layer_name = layer.name
                    break
                    
        if last_conv_layer_name is None:
            return None
            
        grad_model = tf.keras.models.Model(
            inputs=[model.inputs], outputs=[model.get_layer(last_conv_layer_name).output, model.output]
        )
        
        with tf.GradientTape() as tape:
            inputs = tf.cast(img_array, tf.float32)
            last_conv_layer_output, preds = grad_model(inputs)
            if pred_index is None:
                pred_index = tf.argmax(preds[0])
            class_channel = preds[:, pred_index]

        grads = tape.gradient(class_channel, last_conv_layer_output)
        if grads is None:
            return None
        if invert_grads:
            grads = -grads
            
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        last_conv_layer_output = last_conv_layer_output[0]
        heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
        
        heatmap_np = heatmap.numpy()
        heatmap_np = cv2.resize(heatmap_np, (224, 224))
        if np.max(heatmap_np) > 0:
            heatmap_np = heatmap_np / np.max(heatmap_np)
            
        return heatmap_np
    except Exception as e:
        print(f"Keras GradCAM failed natively: {e}")
        return None

# ================= PREDICTION ENDPOINT =================
@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No selected file"}), 400

        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = "image.png"  
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        image = Image.open(filepath).convert("RGB")
        
        # Inference
        # 1. Copy-Move
        cm_score, cm_mask = copymove_model.predict_copymove(cm_model, image, device=DEVICE)
        
        # 2. Segformer
        seg_score, seg_mask = segmentation_model.predict_segformer(seg_model, image, device=DEVICE)
        
        # 3. Face Retouching (PyTorch)
        ret_score, best_ret_model, ret_input_tensor = retouching_model.predict_retouching(ret_models, image, device=DEVICE)
        
        # Heuristic: If it's a face image, the face retouching model should be prioritized
        cv2_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
        profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        faces1 = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(80, 80))
        faces2 = face_cascade_alt.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(80, 80))
        faces3 = profile_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(80, 80))
        
        face_detected = len(faces1) > 0 or len(faces2) > 0 or len(faces3) > 0
        
        if face_detected and ret_score > 0.3:
            # If a face is found, prioritize Face Retouching over everything else
            # by boosting it to 0.999 (which beats Copy-Move's 0.99 cap)
            ret_score = min(ret_score * 1.5 + 0.2, 0.999)
        elif not face_detected:
            # If all 3 aggressive Haar cascades failed to find a face, it's almost certainly not a face.
            # Strictly penalize to 0.0 to prevent out-of-distribution textures (like fur/grass) from winning.
            ret_score = 0.0
            
        # 4. Splicing (Keras)
        spl_score = 0.0
        best_spl_model = None
        if KERAS_AVAILABLE:
            keras_img = image.resize((224, 224))
            keras_arr = np.array(keras_img) / 255.0
            keras_arr = np.expand_dims(keras_arr, axis=0)
            spl_score, best_spl_model = splicing_model.predict_splicing(spl_models, keras_arr)
            
            # Boost splicing slightly to compete with Removal (Segformer) which is highly sensitive.
            # BUT do not boost it if Copy-Move is already higher, since Copy-Move is highly specialized.
            if spl_score > 0.5 and spl_score > cm_score:
                spl_score = min(spl_score * 1.15 + 0.05, 0.99)
        
        scores = {
            "copy_move": cm_score,
            "splicing": spl_score,
            "face_retouching": ret_score,
            "removal": seg_score
        }
        
        best_forgery = max(scores, key=scores.get)
        best_score = scores[best_forgery]
        
        if best_score >= 0.5:
            # Found forgery
            forgery_type = best_forgery.replace("_", "-").title()
            final_pred_str = forgery_type.upper()
            max_conf = min(best_score * 100, 99.9)
        else:
            # Authentic
            forgery_type = "Authentic"
            final_pred_str = "AUTHENTIC"
            max_conf = min((1.0 - best_score) * 100, 99.9)
            
        # Heatmap generation
        heatmap_url = None
        if forgery_type != "Authentic":
            heatmap_arr = None
            if best_forgery == "copy_move" and cm_mask is not None:
                heatmap_arr = cm_mask
            elif best_forgery == "removal" and seg_mask is not None:
                heatmap_arr = seg_mask
            elif best_forgery == "splicing":
                heatmap_arr = None
                if cm_mask is not None and np.max(cm_mask) > 0.1:
                    # The CoMoFoD U-Net provides excellent anomaly detection masks for Splicing
                    heatmap_arr = cm_mask
                elif seg_score > 0.5 and seg_mask is not None:
                    # Segformer provides a much cleaner semantic mask for Splicing than GradCAM
                    heatmap_arr = seg_mask
                if heatmap_arr is None:
                    heatmap_arr = generate_masks.generate_splicing_mask(np.array(image))
            elif best_forgery == "face_retouching" and best_ret_model is not None and ret_input_tensor is not None:
                try:
                    from model import GradCAM
                    target_layer = best_ret_model.backbone.features[-1]
                    cam = GradCAM(best_ret_model, target_layer)
                    heatmap_arr = cam.generate_heatmap(ret_input_tensor, 0) # Class 0 for forged
                except Exception as e:
                    print("GradCAM failed for Face Retouching:", e)
                    heatmap_arr = generate_masks.generate_retouch_mask(np.array(image))
                
            if heatmap_arr is not None:
                heatmap_filename = "heatmap_" + filename
                heatmap_filepath = os.path.join(HEATMAP_FOLDER, heatmap_filename)
                
                # generate_masks functions return 0-255 uint8 images, but overlay_heatmap expects 0-1 float
                if heatmap_arr.dtype == np.uint8:
                    heatmap_arr = heatmap_arr.astype(np.float32) / 255.0
                    
                overlay_heatmap(filepath, heatmap_arr, heatmap_filepath)
                heatmap_url = f"/{heatmap_filepath}".replace("\\", "/")

        original_url = f"/{filepath}".replace("\\", "/")

        # Save to history DB
        record = DetectionRecord(
            filename=filename,
            original_image_url=original_url,
            heatmap_image_url=heatmap_url,
            prediction=final_pred_str,
            confidence=round(max_conf, 2)
        )
        db.session.add(record)
        db.session.commit()

        # Format percentages for response
        formatted_scores = {k: round(min(v * 100, 99.99), 2) for k, v in scores.items()}

        return jsonify({
            "success": True,
            "forgery_type": forgery_type,
            "prediction": final_pred_str,  # Kept for frontend compatibility
            "confidence": round(max_conf, 2),
            "all_scores": formatted_scores,
            "original_image_url": original_url,
            "heatmap_url": heatmap_url
        }), 200

    except Exception as e:
        import traceback
        print("ERROR DURING PREDICTION:")
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Analysis error: {str(e)}"}), 500

# ================= STATIC FILES =================
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    if path and os.path.exists(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    if os.path.exists(os.path.join(dist, "index.html")):
        return send_from_directory(dist, "index.html")
    return "React build not found. Please run 'npm run dev' to see the frontend."

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    