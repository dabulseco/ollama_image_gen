import base64
import io
import os
from datetime import datetime

from PIL import Image


def filter_image_models(installed: list[str], allowlist: list[str]) -> list[str]:
    """Return allowlist entries that are present in installed, preserving allowlist order."""
    installed_set = set(installed)
    return [m for m in allowlist if m in installed_set]


def build_prompt(style_prefix: str, user_prompt: str) -> str:
    """Combine style prefix with user prompt."""
    user_prompt = user_prompt.strip()
    if not style_prefix:
        return user_prompt
    return f"{style_prefix} {user_prompt}"


def get_model_short_name(model_name: str) -> str:
    """Return the part of the model name after the last '/'."""
    return model_name.rsplit("/", 1)[-1]


def get_output_path(output_dir: str, model_name: str, ext: str) -> str:
    """Return a timestamped output file path."""
    short = get_model_short_name(model_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{short}.{ext}"
    return os.path.join(output_dir, filename)


def decode_image_bytes(response_json: dict) -> bytes:
    """Extract and decode the base64 image from an Ollama generate response."""
    images = response_json.get("images")
    if not images:
        raise ValueError("No image data in Ollama response")
    return base64.b64decode(images[0])
