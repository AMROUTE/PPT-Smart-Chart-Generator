from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineInput:
    ppt_path: str
    current_slide: int = 1
    request_id: str = ""


@dataclass
class AgentState:
    ppt_path: str
    current_slide: int
    request_id: str = ""
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
    final_pptx_path: str = ""
    final_pptx_url: str = ""
    logs: list[str] = field(default_factory=list)
    stage_history: list[dict[str, Any]] = field(default_factory=list)
    progress: int = 0
    status: str = "pending"
    retry_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
