import numpy as np

def load_splicing_models(model_paths):
    models = []
    try:
        from tensorflow.keras.models import load_model
        for path in model_paths:
            try:
                models.append(load_model(path))
                print(f"[OK] Loaded Splicing model: {path}")
            except Exception as e:
                print(f"[WARN] Failed to load Splicing model {path}: {e}")
    except ImportError:
        pass
    return models

def predict_splicing(models, keras_arr):
    max_score = 0.0
    best_model = None
    for m_obj in models:
        try:
            pred = m_obj.predict(keras_arr, verbose=0)
            score = 1.0 - float(pred[0][0])
            if score >= max_score:
                max_score = score
                best_model = m_obj
        except Exception as e:
            print(f"Error predicting with a splicing model: {e}")
    return max_score, best_model
