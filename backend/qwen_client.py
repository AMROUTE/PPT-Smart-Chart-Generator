from __future__ import annotations

import json
from typing import Any

import requests

from backend.config import get_settings


CHART_TYPE_MAP = {
    "bar_chart": "bar",
    "line_chart": "line",
    "pie_chart": "pie",
    "scatter_chart": "scatter",
    "heatmap_chart": "heatmap",
    "area_chart": "area",
    "histogram_chart": "histogram",
    "box_chart": "box",
    "bar": "bar",
    "line": "line",
    "pie": "pie",
    "scatter": "scatter",
    "heatmap": "heatmap",
    "area": "area",
    "histogram": "histogram",
    "box": "box",
}


SEMANTIC_PROMPT = """
你是“PPT 智能图表生成系统”的语义分析模块。
请根据输入的文本和表格摘要，判断最适合的图表类型，并生成一个更贴近主题的配图创意方向。

只允许从以下图表类型中选一个：
- bar
- line
- pie
- scatter
- heatmap
- area
- histogram
- box

请严格输出 JSON，格式如下：
{
  "chart_type": "",
  "reason": "",
  "title": "",
  "audience": "",
  "visual_theme": "",
  "palette": ["", ""],
  "keywords": ["", "", ""]
}

要求：
1. 不要输出 Markdown，不要输出解释。
2. reason 用中文，一句话说明判断依据。
3. visual_theme 用中文短语，例如“科技商业增长插画”“教育数据分析卡片”。
4. palette 返回 2 到 3 个颜色名或中文颜色描述。
5. keywords 返回 3 个左右与主题相关的关键词。

文本内容：
{text_content}

表格摘要：
{table_summary}
"""


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start : end + 1]
    return json.loads(content)


def _normalize_semantic_result(result: dict[str, Any]) -> dict[str, Any]:
    chart_type = CHART_TYPE_MAP.get(str(result.get("chart_type", "")).strip().lower(), "bar")
    palette = result.get("palette") or ["蓝色", "青色"]
    keywords = result.get("keywords") or ["数据", "分析", "表达"]
    if not isinstance(palette, list):
        palette = [str(palette)]
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    return {
        "chart_type": chart_type,
        "reason": str(result.get("reason", "模型未提供判断依据。")).strip(),
        "title": str(result.get("title", f"{chart_type.title()} 图表推荐")).strip(),
        "audience": str(result.get("audience", "business")).strip() or "business",
        "visual_theme": str(result.get("visual_theme", "科技数据分析插画")).strip(),
        "palette": [str(item).strip() for item in palette[:3] if str(item).strip()],
        "keywords": [str(item).strip() for item in keywords[:4] if str(item).strip()],
    }


def analyze_semantics_with_qwen(text_content: str, table_summary: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.enable_qwen_api or not settings.qwen_api_key:
        raise RuntimeError("Qwen API is disabled or API key is missing.")

    payload = {
        "model": settings.qwen_model,
        "messages": [
            {"role": "system", "content": "你擅长中文语义理解、图表推荐和视觉创意归纳。"},
            {
                "role": "user",
                "content": SEMANTIC_PROMPT.format(
                    text_content=text_content or "无文本内容",
                    table_summary=table_summary or "无表格摘要",
                ),
            },
        ],
        "temperature": 0.2,
    }
    response = requests.post(
        settings.qwen_base_url,
        headers={
            "Authorization": f"Bearer {settings.qwen_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=settings.qwen_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return _normalize_semantic_result(_extract_json(content))
