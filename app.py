import gradio as gr
import os

# 环境变量保持不变
os.environ["GRADIO_ANALYTICS_ENABLED"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"


def process_ppt(pptx_file, slide_num):
    # 这里的 pptx_file 在旧版本是 tempfile 路径，在新版本可能是个 dict
    # 我们先做一层安全检查
    if pptx_file is None:
        return None, None, gr.update(value=None)

        # 获取文件路径（兼容不同版本的 Gradio）
    file_path = pptx_file.name if hasattr(pptx_file, 'name') else pptx_file
    print(f"✅ 收到文件: {file_path} | 第 {slide_num} 页")

    # 模拟处理过程
    chart_url = "https://picsum.photos/800/600"
    illus_url = "https://picsum.photos/800/600?random=2"

    # 重点：对于 gr.File 输出，如果没有文件，建议返回 gr.update()
    return chart_url, illus_url, gr.update(value=None)


with gr.Blocks(title="语义驱动的 PPT 智能助手") as demo:
    gr.Markdown("# 🎯 语义驱动的 PPT 智能图表生成与多模态配图系统")

    with gr.Row():
        # 作为输入时，设置 file_count="single" 确保传入的是单个文件对象
        file = gr.File(label="📁 上传 PPT 文件", file_types=[".pptx"], type="filepath")
        slide = gr.Number(label="处理第几页", value=1, minimum=1)

    btn = gr.Button("🚀 一键生成图表 + 配图", variant="primary")

    with gr.Row():
        chart_out = gr.Image(label="📊 自动生成的图表")
        illus_out = gr.Image(label="🎨 语义匹配配图")

    download = gr.File(label="⬇️ 下载处理后的新 PPT")

    btn.click(
        process_ppt,
        inputs=[file, slide],
        outputs=[chart_out, illus_out, download]
    )

# ================== 启动配置优化 ==================
if __name__ == "__main__":
    # 修改代码最后部分
    demo.launch(
        share=False,  # 先关掉 share，确保本地能跑通
        server_name="0.0.0.0",  # 允许所有网络接口访问
        server_port=7860,
        show_error=True,
        debug=True
    )