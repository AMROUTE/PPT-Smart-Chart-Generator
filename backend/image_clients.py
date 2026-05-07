from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from backend.config import get_settings


def _download_image(url: str, output_path: Path) -> Path:
    response = requests.get(url, timeout=get_settings().image_generation_timeout_seconds)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path


def generate_wanx_image(prompt: str, output_path: str | Path) -> Path:
    settings = get_settings()
    if not settings.wanx_api_key:
        raise RuntimeError("WANX_API_KEY is not configured.")

    target_path = Path(output_path).with_suffix(".png")
    response = requests.post(
        settings.wanx_base_url,
        headers={
            "Authorization": f"Bearer {settings.wanx_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.wanx_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt,
                            }
                        ],
                    }
                ],
            },
            "parameters": {
                "size": "1280*1280",
                "n": 1,
                "prompt_extend": True,
                "watermark": False,
            },
        },
        timeout=settings.image_generation_timeout_seconds,
    )
    if not response.ok:
        raise RuntimeError(f"WANX request failed ({response.status_code}): {response.text}")
    payload = response.json()
    choices = payload.get("output", {}).get("choices", [])
    if not choices:
        raise RuntimeError(f"WANX did not return any choices: {payload}")
    content = choices[0].get("message", {}).get("content", [])
    if not content:
        raise RuntimeError(f"WANX choice does not contain any message content: {payload}")
    image_url = content[0].get("image")
    if not image_url:
        raise RuntimeError(f"WANX result does not contain an image URL: {payload}")
    return _download_image(image_url, target_path)


def _resolve_flux_result_url(payload: dict[str, Any]) -> str:
    for key in ("result", "sample", "image_url", "url"):
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    result = payload.get("result")
    if isinstance(result, dict):
        for key in ("sample", "image_url", "url"):
            value = result.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
    raise RuntimeError(f"FLUX response does not contain a downloadable image URL: {payload}")


def generate_flux_image(prompt: str, output_path: str | Path) -> Path:
    settings = get_settings()
    if not settings.flux_api_key:
        raise RuntimeError("FLUX_API_KEY is not configured.")

    target_path = Path(output_path).with_suffix(".png")
    submit_response = requests.post(
        f"{settings.flux_base_url.rstrip('/')}/{settings.flux_model_endpoint.lstrip('/')}",
        headers={
            "x-key": settings.flux_api_key,
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "width": 1280,
            "height": 720,
            "output_format": "png",
        },
        timeout=settings.image_generation_timeout_seconds,
    )
    submit_response.raise_for_status()
    submit_payload = submit_response.json()

    polling_url = submit_payload.get("polling_url")
    if not polling_url:
        direct_url = _resolve_flux_result_url(submit_payload)
        return _download_image(direct_url, target_path)

    deadline = time.time() + settings.image_generation_timeout_seconds
    last_payload: dict[str, Any] = submit_payload
    while time.time() < deadline:
        poll_response = requests.get(
            polling_url,
            headers={"x-key": settings.flux_api_key},
            timeout=settings.image_generation_timeout_seconds,
        )
        poll_response.raise_for_status()
        last_payload = poll_response.json()
        status = str(last_payload.get("status", "")).lower()
        if status in {"ready", "completed", "succeeded", "success"}:
            direct_url = _resolve_flux_result_url(last_payload)
            return _download_image(direct_url, target_path)
        if status in {"failed", "error"}:
            raise RuntimeError(f"FLUX generation failed: {last_payload}")
        time.sleep(settings.image_poll_interval_seconds)

    raise TimeoutError(f"FLUX generation timed out while polling: {last_payload}")
