import json
import gradio as gr

from prompt_engine import semantic_parse
from chart_generator import draw_chart


def process_text(text: str):
    if not text or not text.strip():
        return "请输入文本。", None

    try:
        result = semantic_parse(text)
        output_path = draw_chart(result, "outputs/gradio_result.png")
        pretty_json = json.dumps(result, ensure_ascii=False, indent=2)
        return pretty_json, output_path
    except Exception as e:
        return f"处理失败：{e}", None


demo = gr.Interface(
    fn=process_text,
    inputs=gr.Textbox(lines=6, label="请输入用于生成图表的文本描述"),
    outputs=[
        gr.Textbox(label="语义识别结果(JSON)"),
        gr.Image(label="生成图表")
    ],
    title="语义驱动的 PPT 智能图表生成系统 Demo",
    description="输入一段描述性文本，系统自动识别可视化意图并生成图表。"
)

if __name__ == "__main__":
    demo.launch()