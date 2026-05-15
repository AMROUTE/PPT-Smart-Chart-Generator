from sentence_transformers import SentenceTransformer
import numpy as np

from test_cases import test_cases

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

texts = [case["text"] for case in test_cases]
embeddings = model.encode(texts)


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def retrieve_similar_cases(query: str, top_k: int = 5):
    query_embedding = model.encode([query])[0]

    scores = []

    for idx, emb in enumerate(embeddings):
        score = cosine_similarity(query_embedding, emb)
        scores.append((score, test_cases[idx]))

    scores.sort(key=lambda x: x[0], reverse=True)

    return [case for score, case in scores[:top_k]]


def format_cases_for_prompt(cases):
    lines = []

    for i, case in enumerate(cases, start=1):
        lines.append(
            f"""案例{i}：
文本：{case["text"]}
正确意图：{case["label"]}"""
        )

    return "\n\n".join(lines)