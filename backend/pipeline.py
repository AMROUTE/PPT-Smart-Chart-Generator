from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.schemas import AgentState, PipelineInput

try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:  # pragma: no cover
    END = "__END__"
    StateGraph = None


PIPELINE_NODES = [
    "parse_ppt",
    "semantic_analysis",
    "generate_chart",
    "generate_illustration",
    "save_pptx",
]


def append_log(state: dict[str, Any], message: str) -> dict[str, Any]:
    state.setdefault("logs", [])
    state["logs"].append(message)
    return state


def parse_ppt_node(state: dict[str, Any]) -> dict[str, Any]:
    ppt_path = Path(state["ppt_path"])
    state["text_content"] = f"Parsed slide {state['current_slide']} from {ppt_path.name}"
    state["extracted_tables"] = [
        {
            "title": "sample_table",
            "columns": ["category", "value"],
            "rows": [["Q1", 120], ["Q2", 180]],
        }
    ]
    return append_log(state, "PPT parsing completed.")


def semantic_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    state["intent"] = {
        "task": "chart_generation",
        "chart_type": "bar",
        "audience": "business",
    }
    return append_log(state, "Semantic analysis completed.")


def generate_chart_node(state: dict[str, Any]) -> dict[str, Any]:
    rows = state.get("extracted_tables", [{}])[0].get("rows", [])
    state["chart_spec"] = {
        "type": state["intent"].get("chart_type", "bar"),
        "title": f"Slide {state['current_slide']} chart recommendation",
        "data_points": len(rows),
    }
    state["chart_image"] = f"outputs/chart_slide_{state['current_slide']}.png"
    return append_log(state, "Chart generation placeholder completed.")


def generate_illustration_node(state: dict[str, Any]) -> dict[str, Any]:
    state["illustration_prompt"] = (
        "Create a clean technology-themed illustration aligned with the slide topic."
    )
    state["illustration_image"] = f"outputs/illustration_slide_{state['current_slide']}.png"
    return append_log(state, "Illustration generation placeholder completed.")


def save_pptx_node(state: dict[str, Any]) -> dict[str, Any]:
    ppt_path = Path(state["ppt_path"])
    state["final_pptx_path"] = str(
        ppt_path.with_name(f"{ppt_path.stem}_enhanced{ppt_path.suffix}")
    )
    return append_log(state, "PPT save placeholder completed.")


class FallbackCompiledGraph:
    def __init__(self, nodes: list[tuple[str, Any]]):
        self._nodes = nodes

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        current = dict(state)
        for _, node in self._nodes:
            current = node(current)
        return current

    def get_graph(self) -> "FallbackCompiledGraph":
        return self

    def draw_mermaid(self) -> str:
        return "\n".join(
            [
                "graph TD",
                "    start([Start]) --> parse_ppt",
                "    parse_ppt --> semantic_analysis",
                "    semantic_analysis --> generate_chart",
                "    generate_chart --> generate_illustration",
                "    generate_illustration --> save_pptx",
                "    save_pptx --> end([End])",
            ]
        )


def build_pipeline():
    node_pairs = [
        ("parse_ppt", parse_ppt_node),
        ("semantic_analysis", semantic_analysis_node),
        ("generate_chart", generate_chart_node),
        ("generate_illustration", generate_illustration_node),
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


def run_pipeline(payload: PipelineInput | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, PipelineInput):
        initial_state = AgentState(
            ppt_path=payload.ppt_path,
            current_slide=payload.current_slide,
        ).to_dict()
    else:
        initial_state = dict(payload)
        initial_state.setdefault("logs", [])
    return PIPELINE_APP.invoke(initial_state)


def export_pipeline_mermaid() -> str:
    return PIPELINE_APP.get_graph().draw_mermaid()
