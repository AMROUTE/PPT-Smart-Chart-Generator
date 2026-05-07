from __future__ import annotations

import json

from backend.services import process_demo_text


def main() -> None:
    sample_text = "2020: 100\n2021: 150\n2022: 220\n2023: 300\n整体持续增长。"
    payload = process_demo_text(sample_text, semantic_mode="local")

    print("文本演示处理完成：")
    print(json.dumps(payload["pipeline"]["intent"], ensure_ascii=False, indent=2))
    print(f"图表预览：{payload['pipeline'].get('chart_image_url', '')}")
    print(f"配图预览：{payload['pipeline'].get('illustration_image_url', '')}")
    print(f"增强版 PPT：{payload['pipeline'].get('final_pptx_url', '')}")


if __name__ == "__main__":
    main()
