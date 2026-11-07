"""Alt-text suggestions for images that have NO alt attribute.

Default: a lightweight heuristic based on the file name.
Optional: set USE_ML_ALT=1 (and pip install -r backend/requirements-ml.txt) to
caption images with the BLIP model from Hugging Face."""
import io
import os
import re
from functools import lru_cache
from urllib.parse import unquote, urlparse

from ..security import is_public_url

MODEL_NAME = "Salesforce/blip-image-captioning-base"
MAX_ML_IMAGES = 15


def heuristic_alt(src: str) -> str:
    stem = os.path.splitext(os.path.basename(unquote(urlparse(src or "").path)))[0]
    words = re.sub(r"[-_.]+", " ", stem)
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", words)
    words = re.sub(r"\b(img|image|icon|png|jpg|jpeg|svg|webp|\d+x\d+|\d+)\b", " ", words, flags=re.I)
    words = " ".join(words.split())
    if len(words) >= 3 and not re.fullmatch(r"[0-9a-f ]{8,}", words.lower()):
        return words.capitalize()
    return "Describe what this image shows (or use alt=\"\" if it is purely decorative)"


@lru_cache(maxsize=1)
def _load_model():
    from transformers import BlipForConditionalGeneration, BlipProcessor

    return (
        BlipProcessor.from_pretrained(MODEL_NAME),
        BlipForConditionalGeneration.from_pretrained(MODEL_NAME),
    )


def caption_with_blip(src: str) -> str:
    import httpx
    from PIL import Image

    resp = httpx.get(src, timeout=10, follow_redirects=True)
    resp.raise_for_status()
    image = Image.open(io.BytesIO(resp.content)).convert("RGB")
    processor, model = _load_model()
    inputs = processor(image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=30)
    return processor.decode(output[0], skip_special_tokens=True).strip().capitalize()


def suggest_alt_text(images: list, use_ml: bool = False) -> list:
    """Return suggestions for images whose alt attribute is missing (None)."""
    suggestions = []
    ml_used = 0
    for img in images:
        if img.get("alt") is not None or not img.get("src"):
            continue
        suggestion, method = heuristic_alt(img["src"]), "filename-heuristic"
        if use_ml and ml_used < MAX_ML_IMAGES and is_public_url(img["src"]):
            try:
                suggestion, method = caption_with_blip(img["src"]), "blip-model"
                ml_used += 1
            except Exception:
                pass  # fall back to the heuristic suggestion
        suggestions.append({
            "selector": img["selector"], "src": img["src"],
            "suggestion": suggestion, "method": method,
        })
    return suggestions
