import base64
import os
from datetime import datetime

import requests


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
    """Extract and decode the base64 image from an Ollama generate response.

    Tries 'image' (singular, current Ollama diffusion models), then 'images[0]',
    then falls back to the 'response' field (older Ollama builds).
    """
    image_b64 = response_json.get("image", "").strip()
    if image_b64:
        return base64.b64decode(image_b64)
    images = response_json.get("images")
    if images:
        return base64.b64decode(images[0])
    response_b64 = response_json.get("response", "").strip()
    if response_b64:
        return base64.b64decode(response_b64)
    raise ValueError("No image data in Ollama response")


OLLAMA_BASE_URL = "http://localhost:11434"


def check_ollama_health(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Return True if Ollama is reachable."""
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_installed_model_names(base_url: str = OLLAMA_BASE_URL) -> list[str]:
    """Return list of installed model name strings from Ollama."""
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def build_generate_payload(
    model: str,
    prompt: str,
    width: int,
    height: int,
    negative_prompt: str,
    seed: int,
    steps: int,
) -> dict:
    """Build the JSON payload for POST /api/generate.

    width/height/steps are kept as parameters for future use but are not
    sent to Ollama — diffusion models ignore or reject these options fields.
    Only seed is passed when non-zero, as it is broadly supported.
    """
    options: dict = {}
    if seed != 0:
        options["seed"] = seed

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if options:
        payload["options"] = options
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    return payload
