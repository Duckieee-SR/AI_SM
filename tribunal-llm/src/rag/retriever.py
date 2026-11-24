"""Funções de recuperação de artigos do Código do Trabalho."""
import re
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL

_model = None
_client = None
_collection = None
_REF_RE = re.compile(r"(\d+)\.?\s*º(?:-([A-Z]))?")

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
        refs_str = meta.get("referencias", "") or ""
        hits.append({
            "artigo": meta["artigo"],
            "texto": doc,
            "distancia": round(dist, 4),
            "referencias": refs_str.split("|") if refs_str else [],
            "origem": "semantica",
        })
    return hits

def search_with_references(
    query: str,
    k: int = 5,
    max_expansao: int = 15,
) -> List[Dict[str, str]]:
    """
    Pesquisa semântica + expansão por referências cruzadas (1 hop).
    - Hits semânticos mantêm a ordem e a distância originais.
    - Artigos referenciados são acrescentados no fim, com distância 99.0
      e origem='expansao', para não competirem com os hits reais.
    """
    hits_iniciais = search_articles(query, k=k)
    todos = {h["artigo"]: h for h in hits_iniciais}

    # Recolher referências ainda não presentes nos hits iniciais
    refs_a_adicionar: list[str] = []
    for h in hits_iniciais:
        for ref in h.get("referencias", []):
            if ref in todos or ref in refs_a_adicionar:
                continue
            if len(refs_a_adicionar) >= max_expansao:
                break
            refs_a_adicionar.append(ref)
        if len(refs_a_adicionar) >= max_expansao:
            break

    # Adicionar cada artigo referenciado (usa get_article, que já existe)
    for ref in refs_a_adicionar:
        art = get_article(ref)
        if not art:
            continue
        refs_str = ""  # não expandimos 2 hops por omissão
        todos[ref] = {
            "artigo": art["artigo"],
            "texto": art["texto"],
            "distancia": 99.0,
            "referencias": refs_str.split("|") if refs_str else [],
            "origem": "expansao",
        }

    return list(todos.values())


def extract_article_refs(text: str) -> list[str]:
    """
    Extrai referências base 'Artigo N.º' (com sub-letra opcional) de qualquer string.
      "Artigo 382.º, n.º 2, alínea a)"    -> ["Artigo 382.º"]
      "Artigos 331.º e 391.º"             -> ["Artigo 331.º", "Artigo 391.º"]
      "Artigo 101.º-G"                    -> ["Artigo 101.º-G"]
    """
    matches = _REF_RE.findall(text)
    seen, refs = set(), []
    for n, letra in matches:
        ref = f"Artigo {n}.º" + (f"-{letra}" if letra else "")
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