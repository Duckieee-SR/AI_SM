import numpy as np
from rapidbm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

_bm25 = None
_corpus_ids: list[str] = []
_corpus_textos: list[str] = []
_embeddings = None
_model = None

def construir_indice(nos_artigos: list[dict]):
    global _bm25, _corpus_ids, _corpus_textos, _embeddings, _model
    _corpus_ids = [n["id"] for n in nos_artigos]
    _corpus_textos = [n["texto"] for n in nos_artigos]
    tokenized = [t.lower().split() for t in _corpus_textos]
    _bm25 = BM25Okapi(tokenized)
    _model = SentenceTransformer("BAAI/bge-m3")
    _embeddings = _model.encode(_corpus_textos, normalize_embeddings=True, show_progress_bar=False)

def busca_hibrida(query: str, k: int = 15, rrf_k: int = 60) -> list[str]:
    scores_bm25 = _bm25.get_scores(query.lower().split())
    idx_bm25 = np.argsort(scores_bm25)[::-1]

    q_emb = _model.encode(query, normalize_embeddings=True)
    scores_dense = _embeddings @ q_emb
    idx_dense = np.argsort(scores_dense)[::-1]

    rrf: dict[str, float] = {}
    for rank, idx in enumerate(idx_bm25):
        rrf[_corpus_ids[idx]] = rrf.get(_corpus_ids[idx], 0) + 1.0 / (rrf_k + rank)
    for rank, idx in enumerate(idx_dense):
        rrf[_corpus_ids[idx]] = rrf.get(_corpus_ids[idx], 0) + 1.0 / (rrf_k + rank)

    return sorted(rrf, key=rrf.get, reverse=True)[:k]