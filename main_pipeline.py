from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:  # pragma: no cover - fallback path for local validation
    END = "__END__"
    StateGraph = None


@dataclass
class PipelineInput:
    ppt_path: str
    current_slide: int = 1


@dataclass
class AgentState:
    ppt_path: str
    current_slide: int
    text_content: str = ""
    extracted_tables: List[Dict[str, Any]] | None = None
    intent: Dict[str, Any] | None = None
    chart_spec: Dict[str, Any] | None = None
    chart_image: str = ""
    illustration_prompt: str = ""
    illustration_image: str = ""
    final_pptx_path: str = ""
    logs: List[str] | None = None


PIPELINE_NODES = [
    "parse_ppt",
    "semantic_analysis",
    "generate_chart",
    "generate_illustration",
    "save_pptx",
]


def _with_log(state: Dict[str, Any], message: str) -> Dict[str, Any]:
    state.setdefault("logs", [])
    state["logs"].append(message)
    return state


def ppt_parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    ppt_path = Path(state["ppt_path"])
    state["text_content"] = f"Parsed slide {state['current_slide']} from {ppt_path.name}"
    state["extracted_tables"] = [
        {
            "title": "sample_table",
            "columns": ["category", "value"],
            "rows": [["Q1", 120], ["Q2", 180]],
        }
    ]
    return _with_log(state, "PPT parsing completed.")


def semantic_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["intent"] = {
        "task": "chart_generation",
        "chart_type": "bar",
        "audience": "business",
    }
    return _with_log(state, "Semantic analysis completed.")


def chart_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["chart_spec"] = {
        "type": state["intent"]["chart_type"],
        "title": f"Slide {state['current_slide']} chart recommendation",
        "data_points": len(state.get("extracted_tables", [])[0]["rows"]),
    }
    state["chart_image"] = f"outputs/chart_slide_{state['current_slide']}.png"
    return _with_log(state, "Chart generation placeholder completed.")


def illustration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["illustration_prompt"] = (
        "Create a clean technology-themed illustration aligned with the slide topic."
    )
    state["illustration_image"] = f"outputs/illustration_slide_{state['current_slide']}.png"
    return _with_log(state, "Illustration generation placeholder completed.")


def save_pptx_node(state: Dict[str, Any]) -> Dict[str, Any]:
    ppt_path = Path(state["ppt_path"])
    state["final_pptx_path"] = str(
        ppt_path.with_name(f"{ppt_path.stem}_enhanced{ppt_path.suffix}")
    )
    return _with_log(state, "PPT save placeholder completed.")


class FallbackCompiledGraph:
    def __init__(self, nodes: List[tuple[str, Any]]):
        self._nodes = nodes

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        current = dict(state)
        for _, node in self._nodes:
            current = node(current)
        return current

    def get_graph(self) -> "FallbackCompiledGraph":
        return self

    def draw_mermaid(self) -> str:
        lines = ["graph TD"]
        lines.append("    start([Start]) --> parse_ppt")
        lines.append("    parse_ppt --> semantic_analysis")
        lines.append("    semantic_analysis --> generate_chart")
        lines.append("    generate_chart --> generate_illustration")
        lines.append("    generate_illustration --> save_pptx")
        lines.append("    save_pptx --> end([End])")
        return "\n".join(lines)


def build_pipeline():
    node_pairs = [
        ("parse_ppt", ppt_parser_node),
        ("semantic_analysis", semantic_analysis_node),
        ("generate_chart", chart_generation_node),
        ("generate_illustration", illustration_node),
        ("save_pptx", save_pptx_node),
    ]
    if StateGraph is None:
        return FallbackCompiledGraph(node_pairs)

    workflow = StateGraph(dict)
    for name, node in node_pairs:
        workflow.add_node(name, node)
    workflow.set_entry_point("parse_ppt")
    workflow.add_edge("parse_ppt", "semantic_analysis")
    workflow.add_edge("semantic_analysis", "generate_chart")
    workflow.add_edge("generate_chart", "generate_illustration")
    workflow.add_edge("generate_illustration", "save_pptx")
    workflow.add_edge("save_pptx", END)
    return workflow.compile()


PIPELINE_APP = build_pipeline()


def run_pipeline(payload: PipelineInput | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, PipelineInput):
        initial_state = asdict(
            AgentState(
                ppt_path=payload.ppt_path,
                current_slide=payload.current_slide,
                extracted_tables=[],
                intent={},
                chart_spec={},
                logs=[],
            )
        )
    else:
        initial_state = dict(payload)
        initial_state.setdefault("logs", [])
    return PIPELINE_APP.invoke(initial_state)


def export_pipeline_mermaid() -> str:
    return PIPELINE_APP.get_graph().draw_mermaid()


if __name__ == "__main__":
    print(export_pipeline_mermaid())
