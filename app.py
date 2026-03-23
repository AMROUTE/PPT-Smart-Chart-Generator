import gradio as gr
import os

# ================== 禁用 Gradio 所有网络检查（解决超时）==================
os.environ["GRADIO_ANALYTICS_ENABLED"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"


def process_ppt(pptx_file, slide_num):
    if not pptx_file:
        return None, None, None

    print(f"✅ 收到文件: {pptx_file.name} | 第 {slide_num} 页")

    # 第一周临时占位（后面 Week2 再接真实 pipeline）
    return (
        "https://picsum.photos/800/600",  # 临时图表
        "https://picsum.photos/800/600?random=2",  # 临时配图
        None
    )


with gr.Blocks(title="语义驱动的 PPT 智能助手") as demo:
    gr.Markdown("# 🎯 语义驱动的 PPT 智能图表生成与多模态配图系统")
    gr.Markdown("**第一周骨架已完成**｜临时演示版（已禁用网络检查）")

    with gr.Row():
        file = gr.File(label="📁 上传 PPT 文件", file_types=[".pptx"])
        slide = gr.Number(label="处理第几页", value=1, minimum=1)

    btn = gr.Button("🚀 一键生成图表 + 配图", variant="primary", size="large")

    with gr.Row():
        chart_out = gr.Image(label="📊 自动生成的图表", height=400)
        illus_out = gr.Image(label="🎨 语义匹配配图", height=400)

    download = gr.File(label="⬇️ 下载处理后的新 PPT")

    btn.click(
        process_ppt,
        inputs=[file, slide],
        outputs=[chart_out, illus_out, download]
    )

# ================== 最终启动配置（已优化 Mac + 学校网络）==================
demo.launch(
    share=False,
    server_name="127.0.0.1",
    server_port=7860,
    show_error=True,
    debug=True,
    prevent_thread_lock=True
)