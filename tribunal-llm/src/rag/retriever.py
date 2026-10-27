"""Funções de recuperação de artigos do Código do Trabalho."""
import re
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL

_model = None
_client = None
_collection = None
_REF_RE = re.compile(r"(\d+)\.?\s*º")

def _get_resources():
    """Carrega o modelo e a coleção uma única vez (singleton)."""
    global _model, _client, _collection
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_collection(CHROMA_COLLECTION)
    return _model, _collection


def search_articles(query: str, k: int = 5) -> List[Dict[str, str]]:
    """
    Devolve os k artigos mais relevantes para a query.
    Retorna lista de {'artigo': ..., 'texto': ..., 'distancia': ...}.
    """
    model, collection = _get_resources()
    query_emb = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "artigo": meta["artigo"],
            "texto": doc,
            "distancia": round(dist, 4),
        })
    return hits


def extract_article_refs(text: str) -> list[str]:
    """
    Extrai referências base 'Artigo N.º' de qualquer string.
    Exemplos:
      "Artigo 382.º, n.º 2, alínea a) do Código do Trabalho" -> ["Artigo 382.º"]
      "Artigos 331.º e 391.º do CT"                          -> ["Artigo 331.º", "Artigo 391.º"]
      "Artigo 351.º"                                         -> ["Artigo 351.º"]
    """
    nums = _REF_RE.findall(text)
    seen, refs = set(), []
    for n in nums:
        ref = f"Artigo {n}.º"
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def get_article(article_ref: str) -> Optional[dict]:
    """
    Devolve {'artigo': ..., 'texto': ...} se o artigo existir, None se não.
    Usa correspondência exacta pelo metadado; fallback semântico.
    """
    _, collection = _get_resources()
    ref = article_ref.strip()
    if not ref.lower().startswith("artigo"):
        ref = f"Artigo {ref}"

    try:
        result = collection.get(where={"artigo": ref}, limit=1)
        if result["ids"]:
            return {"artigo": ref, "texto": result["documents"][0]}
    except Exception:
        pass

    hits = search_articles(ref, k=3)
    for h in hits:
        if h["artigo"].lower() == ref.lower():
            return {"artigo": h["artigo"], "texto": h["texto"]}
    return None


def article_exists(article_ref: str) -> bool:
    return get_article(article_ref) is not None