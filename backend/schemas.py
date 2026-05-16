from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineInput:
    ppt_path: str
    current_slide: int = 1
    request_id: str = ""
    semantic_mode: str = "local"
    chart_type_override: str = ""
    chart_theme: str = "tech"
    illustration_style: str = "auto"
    image_model: str = "local"
    custom_qwen_api_key: str = ""
    custom_qwen_model: str = ""
    custom_wanx_api_key: str = ""
    custom_flux_api_key: str = ""


@dataclass
class AgentState:
    ppt_path: str
    current_slide: int
    request_id: str = ""
    semantic_mode: str = "local"
    chart_type_override: str = ""
    chart_theme: str = "tech"
    illustration_style: str = "auto"
    image_model: str = "local"
    custom_qwen_api_key: str = ""
    custom_qwen_model: str = ""
    custom_wanx_api_key: str = ""
    custom_flux_api_key: str = ""
    text_content: str = ""
    extracted_tables: list[dict[str, Any]] = field(default_factory=list)
    shapes: list[dict[str, Any]] = field(default_factory=list)
    intent: dict[str, Any] = field(default_factory=dict)
    chart_spec: dict[str, Any] = field(default_factory=dict)
    chart_image: str = ""
    chart_image_url: str = ""
    illustration_prompt: str = ""
    illustration_image: str = ""
    illustration_image_url: str = ""
    illustration_meta: dict[str, Any] = field(default_factory=dict)
    final_pptx_path: str = ""
    final_pptx_url: str = ""
    logs: list[str] = field(default_factory=list)
    stage_history: list[dict[str, Any]] = field(default_factory=list)
    progress: int = 0
    status: str = "pending"
    retry_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
