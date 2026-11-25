# src/rag/reranker.py
from sentence_transformers import CrossEncoder

_reranker = None

def rerank(query: str, candidatos: list[dict], top_n: int = 10) -> list[dict]:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
    
    pares = [(query, c["texto"][:2000]) for c in candidatos]
    scores = _reranker.predict(pares)
    
    ordenados = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)
    return [c for _, c in ordenados[:top_n]]