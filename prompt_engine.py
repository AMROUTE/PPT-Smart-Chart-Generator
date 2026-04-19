import os
import json
import re
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

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
你是一个“PPT 智能图表生成系统”的语义识别模块。
你的任务是：根据输入文本，识别其最适合的可视化意图，并输出统一 JSON。

【可选意图，只能选一个】
1. comparison：比较
   - 适用于不同对象/类别之间高低、多少、优劣对比
   - 常用图表：bar_chart

2. trend：趋势
   - 适用于时间序列、阶段变化、逐年增长/下降
   - 常用图表：line_chart

3. composition：构成
   - 适用于部分占整体比例、份额、占比
   - 常用图表：pie_chart

4. distribution：分布
   - 适用于数据集中在哪些区间/类别、频数分布
   - 常用图表：bar_chart

5. correlation：相关性
   - 适用于两个变量之间正相关、负相关、关系强弱
   - 常用图表：scatter_chart

【图表类型限制，只能从以下中选择】
- bar_chart
- line_chart
- pie_chart
- scatter_chart

【输出要求】
1. 必须严格输出 JSON，对象格式如下：
{{
  "intent": "",
  "chart_type": "",
  "title": "",
  "x": [],
  "y": [],
  "reason": ""
}}

2. 不要输出 Markdown，不要输出 ```json，不要输出额外解释。
3. 如果文本中没有完整数值，也可以根据文本补出合理的 x/y：
   - comparison：x 放类别名，y 可放相对值
   - trend：x 放时间/阶段，y 可放数值
   - composition：x 放组成部分，y 放占比或相对值
   - distribution：x 放区间/类别，y 放频数或相对值
   - correlation：x、y 都放数值列表
4. title 请生成简洁中文标题。
5. reason 用一句中文简要说明判断依据。

【输入文本】
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
    prompt = PROMPT_TEMPLATE.format(text=text)

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