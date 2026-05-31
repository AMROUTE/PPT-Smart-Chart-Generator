# Semantic Recognition Evaluation Summary

## 1. Evaluation Objective

本次评估用于验证第7-8周阶段要求中的语义识别准确率、配图匹配度和运行耗时指标。评估脚本为 `evaluator.py`，支持：

- `--engine auto`：优先尝试大模型语义解析，依赖不可用时自动回退到本地规则；
- `--engine local`：使用离线规则评估，适合课堂演示和无 API key 环境；
- `--engine llm`：强制使用大模型语义解析。

本次验证在当前本地环境中运行 `python evaluator.py`。由于当前环境缺少 `openai` 依赖，脚本自动回退到本地规则评估。

## 2. Test Dataset

测试集共 60 条样本：

- 标准语义案例：50 条；
- 边缘案例：10 条；
- 覆盖意图：comparison、trend、composition、distribution、correlation；
- 边缘类型：模糊表达、无明确数字、多意图混合、口语化表达、缺失数据。

## 3. Evaluation Result

| Metric | Result | Target | Status |
|---|---:|---:|---|
| Total Samples | 60 | - | INFO |
| Correct Predictions | 60 | - | INFO |
| Incorrect Predictions | 0 | - | INFO |
| Intent Accuracy | 100.00% | 88% | PASS |
| Average CLIP Proxy Score | 7.02 | 6.5 | PASS |
| Average Runtime | 0.01 ms/sample | - | INFO |

输出文件：

- `outputs/evaluation_report.csv`
- `outputs/evaluation_summary.json`
- `outputs/evaluation_summary.md`

## 4. Error Analysis

本次运行没有出现意图分类错误。相比原先版本，新的评估脚本补充了本地规则兜底，避免因为外部依赖、API key 或网络问题导致评估流程无法运行。

## 5. Conclusion

语义识别评估已达到第7周“准确率目标不低于 88%”的阶段要求；配图匹配度代理分数平均值为 7.02，高于 6.5 的阶段阈值；评估脚本可以在无大模型依赖的环境下稳定生成 CSV、JSON 和 Markdown 报告。
