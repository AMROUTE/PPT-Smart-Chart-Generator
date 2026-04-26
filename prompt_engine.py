import os
import json
import re
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from rag_retriever import retrieve_similar_cases, format_cases_for_prompt

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen-plus")

if not API_KEY:
    raise ValueError("未读取到 OPENAI_API_KEY，请检查 .env 文件。")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

PROMPT_TEMPLATE = """
你是“语义驱动的PPT智能图表生成系统”的语义识别模块。
你的任务是根据输入文本，完成：
1. 意图分类
2. 数据提取
3. 图表推荐

你必须从以下五类意图中选择唯一一个：

【意图类别】
1. comparison：比较
适用场景：不同对象、产品、区域、方案之间的高低、多少、强弱对比。
常见关键词：高于、低于、相比、对比、最高、最低、分别为。
推荐图表：bar_chart。

2. trend：趋势
适用场景：数据随时间、阶段、年份、月份、季度变化。
常见关键词：增长、下降、上升、减少、逐年、近几年、从...到...。
推荐图表：line_chart。

3. composition：构成
适用场景：部分与整体之间的比例关系、占比、份额、组成结构。
常见关键词：占、占比、比例、构成、组成、份额。
推荐图表：pie_chart。

4. distribution：分布
适用场景：数据集中在某些区间、类别或频次范围。
常见关键词：集中、分布、区间、大多数、主要位于。
推荐图表：bar_chart。

5. correlation：相关性
适用场景：两个变量之间存在正相关、负相关、影响关系。
常见关键词：相关、关系、影响、越...越...、随着...而...。
推荐图表：scatter_chart。

【相似案例参考】
{rag_examples}

【输出要求】
只能输出合法 JSON，不要输出 Markdown，不要输出解释性文字。
JSON 格式必须如下：
{{
  "intent": "",
  "chart_type": "",
  "title": "",
  "x": [],
  "y": [],
  "reason": ""
}}

【字段要求】
- intent 必须是 comparison、trend、composition、distribution、correlation 之一。
- chart_type 必须是 bar_chart、line_chart、pie_chart、scatter_chart 之一。
- title 使用简洁中文标题。
- x 和 y 必须是列表。
- 如果原文有明确数字，请优先提取原文数字。
- 如果原文没有明确数字，请根据语义生成可演示的合理相对值。
- reason 用一句中文说明判断依据。

【待分析文本】
{text}
"""


def _clean_llm_output(content: str) -> str:
    """清理模型输出，去掉 ```json 包裹等。"""
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    return content


def _extract_json_block(text: str) -> str:
    """尽量从文本中提取 JSON 主体。"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def _normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """对返回结果做兜底和标准化。"""
    valid_intents = {"comparison", "trend", "composition", "distribution", "correlation"}
    valid_chart_types = {"bar_chart", "line_chart", "pie_chart", "scatter_chart"}

    intent = data.get("intent", "")
    chart_type = data.get("chart_type", "")
    title = data.get("title", "自动生成图表")
    x = data.get("x", [])
    y = data.get("y", [])
    reason = data.get("reason", "")

    if intent not in valid_intents:
        intent = "comparison"

    if chart_type not in valid_chart_types:
        mapping = {
            "comparison": "bar_chart",
            "trend": "line_chart",
            "composition": "pie_chart",
            "distribution": "bar_chart",
            "correlation": "scatter_chart",
        }
        chart_type = mapping[intent]

    if not isinstance(x, list):
        x = [x]
    if not isinstance(y, list):
        y = [y]

    return {
        "intent": intent,
        "chart_type": chart_type,
        "title": title,
        "x": x,
        "y": y,
        "reason": reason
    }


def semantic_parse(text: str) -> Dict[str, Any]:
    """调用大模型进行语义识别并返回结构化结果。"""

    similar_cases = retrieve_similar_cases(text, top_k=5)
    rag_examples = format_cases_for_prompt(similar_cases)

    prompt = PROMPT_TEMPLATE.format(
        text=text,
        rag_examples=rag_examples
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "你擅长中文语义理解、信息抽取和数据可视化映射。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content.strip()
    content = _clean_llm_output(content)
    content = _extract_json_block(content)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"模型输出不是合法 JSON。\n原始输出：\n{content}\n错误信息：{e}")

    return _normalize_result(result)