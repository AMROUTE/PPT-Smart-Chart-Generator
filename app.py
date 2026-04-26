import gradio as gr

from prompt_engine import semantic_parse
from chart_generator import draw_chart


INTENT_TO_CHART = {
    "comparison": "bar_chart",
    "trend": "line_chart",
    "composition": "pie_chart",
    "distribution": "bar_chart",
    "correlation": "scatter_chart"
}


def auto_process(text: str):
    if not text or not text.strip():
        return {}, None, "请输入文本后再进行识别。"

    try:
        result = semantic_parse(text)
        output_path = draw_chart(result, "outputs/gradio_auto_result.png")
        return result, output_path, "自动识别完成。"
    except Exception as e:
        return {}, None, f"处理失败：{e}"


def manual_fix(result, fixed_intent):
    if not result:
        return {}, None, "请先点击“自动识别并生成图表”。"

    if not fixed_intent:
        return result, None, "请选择修正后的意图。"

    result["intent"] = fixed_intent
    result["chart_type"] = INTENT_TO_CHART.get(fixed_intent, "bar_chart")
    result["reason"] = result.get("reason", "") + "；用户已手动修正意图。"

    try:
        output_path = draw_chart(result, "outputs/gradio_fixed_result.png")
        return result, output_path, "已根据用户修正结果重新生成图表。"
    except Exception as e:
        return result, None, f"重新生成失败：{e}"


with gr.Blocks(title="语义驱动的PPT智能图表生成系统") as demo:
    gr.Markdown("# 语义驱动的 PPT 智能图表生成系统 Demo")
    gr.Markdown(
        "输入一段PPT页面文本，系统会自动完成语义意图识别、数据提取、图表推荐和图表生成。"
        "如果识别结果不准确，也可以手动修正意图并重新生成图表。"
    )

    text_input = gr.Textbox(
        label="请输入文本",
        lines=6,
        placeholder="例如：2020年到2023年销售额分别为100万、150万、220万、300万，整体持续增长。"
    )

    auto_btn = gr.Button("自动识别并生成图表")

    with gr.Row():
        json_output = gr.JSON(label="语义识别结果 JSON")
        image_output = gr.Image(label="生成图表")

    status_output = gr.Textbox(label="状态信息")

    gr.Markdown("## 用户手动修正意图")

    fixed_intent = gr.Dropdown(
        choices=[
            "comparison",
            "trend",
            "composition",
            "distribution",
            "correlation"
        ],
        label="修正后的意图"
    )

    fix_btn = gr.Button("根据修正结果重新生成图表")

    auto_btn.click(
        fn=auto_process,
        inputs=text_input,
        outputs=[json_output, image_output, status_output]
    )

    fix_btn.click(
        fn=manual_fix,
        inputs=[json_output, fixed_intent],
        outputs=[json_output, image_output, status_output]
    )


if __name__ == "__main__":
    demo.launch()