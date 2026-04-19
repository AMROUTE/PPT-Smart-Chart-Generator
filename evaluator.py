from prompt_engine import semantic_parse
from test_cases import test_cases


def evaluate():
    correct = 0
    total = len(test_cases)

    print("=" * 80)
    print("开始评估语义识别准确率")
    print("=" * 80)

    for idx, case in enumerate(test_cases, start=1):
        text = case["text"]
        true_label = case["label"]

        try:
            result = semantic_parse(text)
            pred_label = result["intent"]
        except Exception as e:
            pred_label = "ERROR"
            print(f"[{idx}] 调用失败：{e}")

        is_correct = pred_label == true_label
        if is_correct:
            correct += 1

        print(f"[{idx}] 文本：{text}")
        print(f"    预测：{pred_label}")
        print(f"    标注：{true_label}")
        print(f"    是否正确：{'√' if is_correct else '×'}")
        print("-" * 80)

    accuracy = correct / total if total > 0 else 0
    print(f"总样本数：{total}")
    print(f"预测正确：{correct}")
    print(f"准确率：{accuracy:.2%}")


if __name__ == "__main__":
    evaluate()