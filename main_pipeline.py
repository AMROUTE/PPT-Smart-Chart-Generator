from langgraph.graph import StateGraph, END
from typing import TypedDict
import gradio as gr

class AgentState(TypedDict):
    ppt_path: str
    current_slide: int
    text_content: str
    intent: dict
    chart_code: str
    chart_image: str
    illustration_prompt: str
    illustration_image: str
    final_pptx_path: str

# ============== 你本周先写空的节点 ==============
def ppt_parser_node(state: AgentState):

    return state

def semantic_analysis_node(state: AgentState):

    return state

def chart_generation_node(state: AgentState):

    return state

def illustration_node(state: AgentState):

    return state

def save_pptx_node(state: AgentState):

    return state

# 构建图
workflow = StateGraph(AgentState)
workflow.add_node("parse_ppt", ppt_parser_node)
workflow.add_node("semantic_analysis", semantic_analysis_node)
workflow.add_node("generate_chart", chart_generation_node)
workflow.add_node("generate_illustration", illustration_node)
workflow.add_node("save_pptx", save_pptx_node)

# 流程顺序
workflow.set_entry_point("parse_ppt")
workflow.add_edge("parse_ppt", "semantic_analysis")
workflow.add_edge("semantic_analysis", "generate_chart")
workflow.add_edge("generate_chart", "generate_illustration")
workflow.add_edge("generate_illustration", "save_pptx")
workflow.add_edge("save_pptx", END)

app = workflow.compile()

# 导出 Mermaid 图（给汇报用）
print(app.get_graph().draw_mermaid())