# FastAPI Integration Steps

Integrating the decoupled multi-region module into an existing production application ensures failure isolation and minimal impact on current capabilities. Follow these steps:

### 1. Minimal Initialization
Ensure the plug-in instance is instantiated safely once outside the endpoint routes. If `patch_model.pth` is missing, the initializer won't halt the API; it waits silently.
```python
# main.py or existing API
from fastapi import FastAPI
from modules.forgery_region_module import MultiRegionForgeryPipeline

app = FastAPI()

# 1. Initialize plugin safely at startup
plugin_pipeline = MultiRegionForgeryPipeline(
    patch_model_path="patch_model.pth", 
    device="cpu"
)
```

### 2. Plug Into Endpoint Post-Heatmap Extraction
Once the existing base model has identified the image as `"forged"` and output a grad-cam heatmap array, parse it through the standalone plugin before returning.

```python
@app.post("/predict")
async def analyze_image(file: UploadFile):
    # ... (Your existing file save code here > 'image_path')
    # ... (Your existing binary model predictor here > 'base_label')
    # ... (Your existing heatmap generator here > numpy array 'heatmap')
    
    # 2. Invoke the plugin gracefully!
    # Returns exactly { "label": "forged", "regions": [...] }
    final_output = plugin_pipeline.process(
        image_path=image_path, 
        heatmap=heatmap, 
        base_label=base_label
    )
    
    return final_output 
```

### Automation Scripts
- Use `python run_all.py` at any point on a fresh instance to install datasets, train the module's lightweight internal classifiers on synthetic patches, and auto-export the necessary `patch_model.pth`.
