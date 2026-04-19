import os
from typing import Dict, Any

import matplotlib.pyplot as plt

# 尝试支持中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def draw_chart(data: Dict[str, Any], output_path: str = "outputs/output.png") -> str:
    """
    根据结构化语义结果绘图并保存。
    返回保存路径。
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    chart_type = data.get("chart_type", "bar_chart")
    title = data.get("title", "自动生成图表")
    x = data.get("x", [])
    y = data.get("y", [])

    plt.figure(figsize=(8, 5))

    if chart_type == "line_chart":
        plt.plot(x, y, marker="o")
        plt.xlabel("类别 / 时间")
        plt.ylabel("数值")

    elif chart_type == "bar_chart":
        plt.bar(x, y)
        plt.xlabel("类别")
        plt.ylabel("数值")

    elif chart_type == "pie_chart":
        if not x or not y or len(x) != len(y):
            raise ValueError("饼图需要长度一致的 x 和 y。")
        plt.pie(y, labels=x, autopct="%1.1f%%")
    elif chart_type == "scatter_chart":
        if not x or not y or len(x) != len(y):
            raise ValueError("散点图需要长度一致的 x 和 y。")
        plt.scatter(x, y)
        plt.xlabel("X")
        plt.ylabel("Y")

    else:
        plt.bar(x, y)
        plt.xlabel("类别")
        plt.ylabel("数值")

    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path