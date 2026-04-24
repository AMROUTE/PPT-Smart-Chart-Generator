import csv
import os
from collections import defaultdict

from prompt_engine import semantic_parse
from test_cases import test_cases


def evaluate():
    os.makedirs("outputs", exist_ok=True)

    total = len(test_cases)
    correct = 0
    rows = []
    error_by_label = defaultdict(int)

    print("=" * 80)
    print("开始评估语义识别准确率")
    print("=" * 80)

    for idx, case in enumerate(test_cases, start=1):
        text = case["text"]
        true_label = case["label"]

        try:
            result = semantic_parse(text)
            pred_label = result.get("intent", "")
            chart_type = result.get("chart_type", "")
            reason = result.get("reason", "")
            error = ""
        except Exception as e:
            pred_label = "ERROR"
            chart_type = ""
            reason = ""
            error = str(e)

        is_correct = pred_label == true_label

        if is_correct:
            correct += 1
        else:
            error_by_label[true_label] += 1

        rows.append({
            "id": idx,
            "text": text,
            "true_label": true_label,
            "pred_label": pred_label,
            "chart_type": chart_type,
            "is_correct": "1" if is_correct else "0",
            "reason": reason,
            "error": error
        })

        print(f"[{idx}] 文本：{text}")
        print(f"    标注：{true_label}")
        print(f"    预测：{pred_label}")
        print(f"    图表：{chart_type}")
        print(f"    是否正确：{'√' if is_correct else '×'}")
        if error:
            print(f"    错误信息：{error}")
        print("-" * 80)

    accuracy = correct / total if total else 0

    report_path = "outputs/evaluation_report.csv"

    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "text",
                "true_label",
                "pred_label",
                "chart_type",
                "is_correct",
                "reason",
                "error"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 80)
    print("评估结果")
    print("=" * 80)
    print(f"总样本数：{total}")
    print(f"预测正确：{correct}")
    print(f"准确率：{accuracy:.2%}")
    print(f"测试报告已保存到：{report_path}")

    if error_by_label:
        print("\n错误类别统计：")
        for label, count in error_by_label.items():
            print(f"{label}: {count} 条")
    else:
        print("\n错误类别统计：无错误")


if __name__ == "__main__":
    evaluate()