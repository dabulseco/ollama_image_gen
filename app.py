import io
import os

import requests
import streamlit as st
from PIL import Image

from utils import (
    OLLAMA_BASE_URL,
    build_generate_payload,
    build_prompt,
    check_ollama_health,
    decode_image_bytes,
    filter_image_models,
    get_installed_model_names,
    get_model_short_name,
    get_output_path,
)

# ── Constants ──────────────────────────────────────────────────────────────────

IMAGE_CAPABLE_MODELS = [
    "x/z-image-turbo",
    "x/flux2-klein",
]

STYLE_PRESETS = {
    "None": "",
    "Photorealistic": "photorealistic,",
    "Anime / Manga": "anime style, manga,",
    "Digital Art": "digital art,",
    "Oil Painting": "oil painting,",
    "Watercolor": "watercolor painting,",
    "Sketch / Line Art": "sketch, line art,",
    "Cyberpunk": "cyberpunk style, neon,",
    "Fantasy": "fantasy art, epic,",
    "Minimalist": "minimalist, clean,",
}

SIZE_PRESETS = {
    "512×512 – Thumbnail (default)": (512, 512),
    "1024×1024 – Square": (1024, 1024),
    "1280×720 – HD Banner": (1280, 720),
    "1920×1080 – Full HD": (1920, 1080),
    "1200×630 – OG Card": (1200, 630),
    "800×600 – Blog Image": (800, 600),
}

OUTPUT_DIR = "output"

# ── Session state defaults ─────────────────────────────────────────────────────

def init_state() -> None:
    defaults = {
        "last_image": None,
        "last_request": None,
        "show_save_options": False,
        "status_message": "",
        "status_ok": True,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_state() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ── App entry point ────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="Ollama Image Generator", layout="wide")
    init_state()

    ollama_ok = check_ollama_health()
    installed = get_installed_model_names() if ollama_ok else []
    available_models = filter_image_models(
        [m.split(":")[0] for m in installed], IMAGE_CAPABLE_MODELS
    )

    render_top_bar(available_models, ollama_ok)
    render_main_panels(available_models, ollama_ok)


if __name__ == "__main__":
    main()


def render_top_bar(available_models: list[str], ollama_ok: bool) -> None:
    st.write("TOP BAR — coming in Task 5")


def render_main_panels(available_models: list[str], ollama_ok: bool) -> None:
    st.write("MAIN PANELS — coming in Task 6+")
