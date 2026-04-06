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
    col_model, col_style, col_size, col_spacer, col_reset = st.columns(
        [2, 2, 2.5, 2, 1], vertical_alignment="bottom"
    )

    with col_model:
        if available_models:
            st.selectbox("Model", available_models, key="selected_model")
        else:
            st.selectbox("Model", ["No image models found"], key="selected_model", disabled=True)

    with col_style:
        st.selectbox("Style", list(STYLE_PRESETS.keys()), key="selected_style")

    with col_size:
        st.selectbox(
            "Size",
            list(SIZE_PRESETS.keys()),
            key="selected_size",
        )

    with col_reset:
        if st.button("↺ Reset", type="secondary", use_container_width=True):
            reset_state()


def render_main_panels(available_models: list[str], ollama_ok: bool) -> None:
    left_col, right_col = st.columns([3, 2])

    with right_col:
        render_settings_panel(available_models, ollama_ok)

    with left_col:
        render_preview_panel()


def render_settings_panel(available_models: list[str], ollama_ok: bool) -> None:
    st.text_area(
        "Prompt",
        key="prompt_text",
        height=120,
        placeholder="Describe the image you want to generate...",
    )

    with st.expander("Negative Prompt (optional)"):
        st.text_area(
            "Negative prompt",
            key="negative_prompt_text",
            height=80,
            placeholder="blurry, low quality, watermark, text...",
            label_visibility="collapsed",
        )

    with st.expander("Advanced Settings"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            st.number_input("Seed", min_value=0, value=0, step=1, key="seed_value",
                            help="0 = random each time")
        with adv_col2:
            st.number_input("Steps", min_value=0, value=0, step=1, key="steps_value",
                            help="0 = model default")

    can_generate = ollama_ok and bool(available_models)
    if st.button(
        "✨ Generate Image",
        type="primary",
        use_container_width=True,
        disabled=not can_generate,
    ):
        st.session_state["show_save_options"] = False
        run_generation()

    # Status indicator
    if not ollama_ok:
        st.error("✗ Ollama not reachable — is it running? `ollama serve`")
    elif not available_models:
        st.warning(
            "No image models found. Install one:\n\n"
            "`ollama pull x/z-image-turbo`\n\n"
            "`ollama pull x/flux2-klein`"
        )
    elif st.session_state.get("status_message"):
        if st.session_state["status_ok"]:
            st.success(st.session_state["status_message"])
        else:
            st.error(st.session_state["status_message"])
    else:
        st.success("✓ Ready — Ollama connected")


def run_generation() -> None:
    model = st.session_state.get("selected_model", "")
    style_label = st.session_state.get("selected_style", "None")
    size_label = st.session_state.get("selected_size", list(SIZE_PRESETS.keys())[0])
    prompt_text = st.session_state.get("prompt_text", "").strip()
    negative_prompt = st.session_state.get("negative_prompt_text", "").strip()
    seed = int(st.session_state.get("seed_value", 0))
    steps = int(st.session_state.get("steps_value", 0))

    if not prompt_text:
        st.session_state["status_message"] = "Please enter a prompt before generating."
        st.session_state["status_ok"] = False
        return

    style_prefix = STYLE_PRESETS.get(style_label, "")
    full_prompt = build_prompt(style_prefix, prompt_text)
    width, height = SIZE_PRESETS[size_label]

    payload = build_generate_payload(
        model=model,
        prompt=full_prompt,
        width=width,
        height=height,
        negative_prompt=negative_prompt,
        seed=seed,
        steps=steps,
    )
    st.session_state["last_request"] = payload

    with st.spinner("Generating image..."):
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=300,
            )
            resp.raise_for_status()
            image_bytes = decode_image_bytes(resp.json())
        except ValueError as e:
            st.session_state["status_message"] = f"Model returned no image. {e}"
            st.session_state["status_ok"] = False
            return
        except requests.RequestException as e:
            st.session_state["status_message"] = f"Generation failed: {e}"
            st.session_state["status_ok"] = False
            return

    st.session_state["last_image"] = image_bytes
    st.session_state["status_message"] = "Image generated successfully."
    st.session_state["status_ok"] = True


def render_preview_panel() -> None:
    image_bytes = st.session_state.get("last_image")

    if image_bytes:
        st.image(image_bytes, use_container_width=True)
    else:
        st.markdown(
            """
            <div style='border: 2px dashed #555; border-radius:10px;
                        min-height:300px; display:flex; align-items:center;
                        justify-content:center; color:#888;'>
              <p style='font-size:1.1em;'>🖼️ Generated image will appear here</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if image_bytes:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Save Image", use_container_width=True):
                st.session_state["show_save_options"] = True
        with btn_col2:
            if st.button("🔄 Regenerate", use_container_width=True):
                st.session_state["show_save_options"] = False
                run_generation()

        if st.session_state.get("show_save_options"):
            render_save_panel(image_bytes)


def render_save_panel(image_bytes: bytes) -> None:
    st.write("SAVE PANEL — coming in Task 8")
