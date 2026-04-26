from difflib import SequenceMatcher
from test_cases import test_cases


def similarity(a: str, b: str) -> float:
    """
    计算两个文本的相似度。
    这里使用 Python 内置的 SequenceMatcher，
    不需要额外安装向量数据库。
    """
    return SequenceMatcher(None, a, b).ratio()


def retrieve_similar_cases(query: str, top_k: int = 5):
    """
    从 test_cases.py 中检索与输入文本最相似的案例。
    """
    scored_cases = []

    for case in test_cases:
        score = similarity(query, case["text"])
        scored_cases.append((score, case))

    scored_cases.sort(key=lambda item: item[0], reverse=True)

    return [case for score, case in scored_cases[:top_k]]


def format_cases_for_prompt(cases):
    """
    把检索到的案例整理成 Prompt 中可以直接使用的 few-shot 示例。
    """
    lines = []

    for i, case in enumerate(cases, start=1):
        lines.append(
            f"""案例{i}：
文本：{case["text"]}
正确意图：{case["label"]}"""
        )

    return "\n\n".join(lines)