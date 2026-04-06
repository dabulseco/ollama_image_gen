import base64
import io
import os
from datetime import datetime
from unittest.mock import patch

import pytest
from PIL import Image

from utils import (
    build_prompt,
    decode_image_bytes,
    filter_image_models,
    get_model_short_name,
    get_output_path,
)


def test_filter_image_models_returns_intersection():
    installed = ["llama3", "x/z-image-turbo", "mistral", "x/flux2-klein"]
    allowlist = ["x/z-image-turbo", "x/flux2-klein"]
    assert filter_image_models(installed, allowlist) == ["x/z-image-turbo", "x/flux2-klein"]


def test_filter_image_models_none_installed():
    assert filter_image_models(["llama3", "mistral"], ["x/z-image-turbo"]) == []


def test_filter_image_models_preserves_allowlist_order():
    installed = ["x/flux2-klein", "x/z-image-turbo"]
    allowlist = ["x/z-image-turbo", "x/flux2-klein"]
    result = filter_image_models(installed, allowlist)
    assert result == ["x/z-image-turbo", "x/flux2-klein"]


def test_build_prompt_with_style_prefix():
    assert build_prompt("photorealistic,", "a mountain lake") == "photorealistic, a mountain lake"


def test_build_prompt_no_prefix():
    assert build_prompt("", "a mountain lake") == "a mountain lake"


def test_build_prompt_strips_whitespace():
    assert build_prompt("digital art,", "  a cat  ") == "digital art, a cat"


def test_get_model_short_name_with_slash():
    assert get_model_short_name("x/z-image-turbo") == "z-image-turbo"


def test_get_model_short_name_without_slash():
    assert get_model_short_name("flux2-klein") == "flux2-klein"


def test_get_model_short_name_multiple_slashes():
    assert get_model_short_name("a/b/c-model") == "c-model"


def test_get_output_path_format():
    path = get_output_path("output", "x/z-image-turbo", "png")
    filename = os.path.basename(path)
    assert filename.endswith("_z-image-turbo.png")
    assert filename[:15].replace("_", "").isdigit()  # YYYYMMDD_HHMMSS prefix


def test_get_output_path_directory():
    path = get_output_path("output", "x/z-image-turbo", "png")
    assert path.startswith("output" + os.sep) or path.startswith("output/")


def test_decode_image_bytes_valid():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    response = {"images": [b64], "done": True}
    result = decode_image_bytes(response)
    assert isinstance(result, bytes)
    restored = Image.open(io.BytesIO(result))
    assert restored.size == (10, 10)


def test_decode_image_bytes_missing_images_key():
    with pytest.raises(ValueError, match="No image"):
        decode_image_bytes({"done": True})


def test_decode_image_bytes_empty_images_list():
    with pytest.raises(ValueError, match="No image"):
        decode_image_bytes({"images": [], "done": True})
