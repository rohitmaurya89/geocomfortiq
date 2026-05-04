"""
apps/analysis/dl_segmenter.py  — Phase 6

Pretrained Deep Learning Land-Cover Segmentation.
Model : DeepLabV3+ with ResNet-50 backbone (torchvision)
Mode  : Inference ONLY — no training, no custom weights needed.
        Model is downloaded automatically on first run (~160 MB, cached by torch).

Pascal VOC class indices used for land-cover mapping:
  0  = background  → built-up proxy
  8  = boat        → water proxy
  9  = bottle      → (skip)
  15 = person      → (skip / congestion proxy)
  17 = cat/animal  → vegetation proxy
  20 = train       → road/congestion proxy

We map the 21 Pascal VOC classes to our 5 comfort parameters using
a simple lookup table — good enough for an academic project demo.

Falls back silently if torch/torchvision not installed.
"""

"""
apps/analysis/dl_segmenter.py

DeepLabV3 ResNet-50 — inference only, no training.
KEY FIX: Model is loaded ONCE into _MODEL_CACHE and reused every request.
         First load takes ~10-15 seconds. All subsequent calls are instant.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── Module-level cache — loaded once, reused forever ──────────────────────────
_MODEL_CACHE = None
_TRANSFORM_CACHE = None

VOC_TO_PARAM = {
    0:  None,
    1:  'builtup',
    2:  'builtup',
    3:  None,
    4:  None,
    5:  'builtup',
    6:  'builtup',
    7:  'builtup',
    8:  'green',
    9:  'green',
    10: None,
    11: 'green',
    12: 'green',
    13: 'green',
    14: 'builtup',
    15: 'green',
    16: 'builtup',
    17: 'green',
    18: 'water',
    19: 'builtup',
    20: 'builtup',
}


def _get_model():
    """Load model once and cache it. Returns (model, transform) or (None, None)."""
    global _MODEL_CACHE, _TRANSFORM_CACHE

    if _MODEL_CACHE is not None:
        return _MODEL_CACHE, _TRANSFORM_CACHE

    try:
        import torch
        import torchvision.transforms as T
        from torchvision.models.segmentation import (
            deeplabv3_resnet50,
            DeepLabV3_ResNet50_Weights,
        )

        logger.info("Loading DeepLabV3 model for the first time (one-time ~15s wait)...")
        weights  = DeepLabV3_ResNet50_Weights.DEFAULT
        model    = deeplabv3_resnet50(weights=weights)
        model.eval()

        transform = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std =[0.229, 0.224, 0.225]),
        ])

        _MODEL_CACHE     = model
        _TRANSFORM_CACHE = transform
        logger.info("DeepLabV3 model loaded and cached. Future requests will be instant.")
        return _MODEL_CACHE, _TRANSFORM_CACHE

    except ImportError:
        logger.info("torch/torchvision not installed — DL segmentation disabled.")
        _MODEL_CACHE     = False   # Mark as unavailable so we don't retry
        _TRANSFORM_CACHE = False
        return None, None
    except Exception as e:
        logger.warning(f"Model load failed: {e}")
        _MODEL_CACHE     = False
        _TRANSFORM_CACHE = False
        return None, None


def run_dl_segmentation(image_bgr: np.ndarray):
    """
    Run DeepLabV3 on image. Uses cached model — fast after first call.
    Returns dict with green_pct, builtup_pct, water_pct or None.
    """
    model, transform = _get_model()
    if not model:
        return None

    try:
        import torch
        import cv2
        from PIL import Image

        rgb_img     = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img     = Image.fromarray(rgb_img).resize((520, 520))
        input_tensor = transform(pil_img).unsqueeze(0)

        with torch.no_grad():
            output  = model(input_tensor)['out']
            seg_map = output.argmax(dim=1).squeeze().numpy()

        total  = seg_map.size
        counts = {'green': 0, 'builtup': 0, 'water': 0}

        for voc_class, param in VOC_TO_PARAM.items():
            if param in counts:
                counts[param] += int(np.sum(seg_map == voc_class))

        return {
            'green_pct':    round((counts['green']   / total) * 100, 2),
            'builtup_pct':  round((counts['builtup'] / total) * 100, 2),
            'water_pct':    round((counts['water']   / total) * 100, 2),
            'dl_available': True,
        }

    except Exception as e:
        logger.warning(f"DL inference failed: {e}")
        return None


def blend_with_opencv(opencv_params: dict, dl_params, dl_weight: float = 0.4) -> dict:
    """Blend OpenCV + DL results. DL refines green, builtup, water only."""
    if not dl_params:
        return opencv_params

    blended = dict(opencv_params)
    cv_w    = 1.0 - dl_weight

    for key in ('green_pct', 'builtup_pct', 'water_pct'):
        if key in dl_params:
            blended[key] = round(
                cv_w * opencv_params.get(key, 0) + dl_weight * dl_params[key], 2
            )

    blended['dl_available'] = True
    return blended