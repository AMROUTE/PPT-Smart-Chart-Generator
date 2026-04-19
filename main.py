from prompt_engine import semantic_parse
from chart_generator import draw_chart


def main():
    text = "2020年到2023年销售额分别为100万、150万、220万、300万，整体持续增长。"

    result = semantic_parse(text)

    print("语义识别结果：")
    print(result)

    output_path = draw_chart(result, "outputs/result.png")
    print(f"图表已保存到：{output_path}")


if __name__ == "__main__":
    main()