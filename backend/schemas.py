from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineInput:
    ppt_path: str
    current_slide: int = 1


@dataclass
class AgentState:
    ppt_path: str
    current_slide: int
    text_content: str = ""
    extracted_tables: list[dict[str, Any]] = field(default_factory=list)
    intent: dict[str, Any] = field(default_factory=dict)
    chart_spec: dict[str, Any] = field(default_factory=dict)
    chart_image: str = ""
    illustration_prompt: str = ""
    illustration_image: str = ""
    final_pptx_path: str = ""
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
