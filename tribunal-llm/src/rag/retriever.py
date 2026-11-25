"""Funções de recuperação de artigos do Código do Trabalho."""
import re
from typing import List, Dict, Optional
from pathlib import Path

from config import CHROMA_DIR, CHROMA_COLLECTION, DATA_DIR
from src.rag.parser import carregar_grafo, No, CONCEITOS_JURIDICOS
from src.rag.hybrid import construir_indice, busca_hibrida
from src.rag.reranker import rerank

_client = None
_collection = None
_nos_grafo: dict[str, No] = {}
_hybrid_ready = False

def _get_resources():
    global _client, _collection
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_collection(CHROMA_COLLECTION)
    return _collection

def _ensure_hybrid():
    global _hybrid_ready, _nos_grafo
    if _hybrid_ready:
        return
    _nos_grafo = carregar_grafo(DATA_DIR / "grafo.json")
    
    artigos = [{"id": n.id, "texto": n.texto} for n in _nos_grafo.values() if n.tipo == "artigo"]
    construir_indice(artigos)
    _hybrid_ready = True

def _get_artigo_by_base(base_ref: str) -> Optional[dict]:
    """Vai buscar o texto de um artigo ao Chroma dado o seu nome (ex: 'Artigo 351.º')."""
    collection = _get_resources()
    try:
        result = collection.get(where={"artigo": base_ref}, limit=1)
        if result["ids"]:
            return {
                "artigo": base_ref,
                "texto": result["documents"][0],
                "distancia": 0.0,
                "referencias": result["metadatas"][0].get("referencias", "").split("|") if result["metadatas"][0].get("referencias") else [],
            }
    except Exception:
        pass
    return None

def search_articles(query: str, k: int = 5) -> List[Dict[str, str]]:
    _ensure_hybrid()
    ids = busca_hibrida(query, k=k)
    collection = _get_resources()
    results = collection.get(ids=ids)
    
    hits_dict = {}
    for i, no_id in enumerate(ids):
        if no_id in results["ids"]:
            idx = results["ids"].index(no_id)
            meta = results["metadatas"][idx]
            hits_dict[no_id] = {
                "artigo": meta["artigo"],
                "texto": results["documents"][idx],
                "distancia": float(i),
                "referencias": meta.get("referencias", "").split("|") if meta.get("referencias") else [],
                "origem": "semantica",
            }
    return [hits_dict[i] for i in ids if i in hits_dict]

def search_with_references(query: str, k: int = 8, max_nos: int = 15) -> List[Dict[str, str]]:
    _ensure_hybrid()
    
    # 1. Injeção de Ontologia (Domain Ontology Injection)
    # Lê a query e força a entrada dos artigos associados aos conceitos detetados.
    query_lower = query.lower()
    injetados = []
    for conceito, artigos in CONCEITOS_JURIDICOS.items():
        if conceito in query_lower:
            for num in artigos:
                base_ref = f"Artigo {num}.º"
                if not any(h["artigo"] == base_ref for h in injetados):
                    art = _get_artigo_by_base(base_ref)
                    if art:
                        art["origem"] = "conceito"
                        injetados.append(art)

    # 2. Hits semânticos normais
    hits_semanticos = search_articles(query, k=k)
    
    # 3. Reranking (apenas aos semânticos, para não estragar a ordem)
    if hits_semanticos:
        hits_semanticos = rerank(query, hits_semanticos, top_n=k)
        
    # 4. Juntar tudo (Conceitos primeiro, depois Semânticos, sem duplicados)
    hits_iniciais = []
    vistos = set()
    for h in injetados + hits_semanticos:
        if h["artigo"] not in vistos:
            hits_iniciais.append(h)
            vistos.add(h["artigo"])

    resultado: dict[str, dict] = {h["artigo"]: h for h in hits_iniciais}

    # 5. Travessia no grafo (Apenas Out-links, para evitar explosão)
    fila = []
    for h in hits_iniciais:
        for no in _nos_grafo.values():
            if no.tipo == "artigo" and no.artigo_base == h["artigo"]:
                fila.append(no.id)
                break

    visitados = set(fila)
    while fila and len(resultado) < max_nos:
        no_id = fila.pop(0)
        no = _nos_grafo.get(no_id)
        if not no:
            continue
        
        for ref_id in no.referencias:
            if len(resultado) >= max_nos: # Respeitar o limite!
                break
            if ref_id in visitados:
                continue
            visitados.add(ref_id)
            ref_no = _nos_grafo.get(ref_id)
            
            if ref_no and ref_no.tipo == "artigo":
                if ref_no.artigo_base not in resultado:
                    resultado[ref_no.artigo_base] = {
                        "artigo": ref_no.artigo_base,
                        "texto": ref_no.texto,
                        "distancia": 99.0,
                        "referencias": ref_no.referencias,
                        "origem": "expansao",
                    }
                fila.append(ref_id)

    return list(resultado.values())

# --- Funções utilitárias (mantêm-se iguais) ---
_REF_RE = re.compile(r"(\d+)\.?\s*º")
def extract_article_refs(text: str) -> list[str]:
    nums = _REF_RE.findall(text)
    seen, refs = set(), []
    for n in nums:
        ref = f"Artigo {n}.º"
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs

def get_article(article_ref: str) -> Optional[dict]:
    art = _get_artigo_by_base(article_ref)
    if art:
        return {"artigo": art["artigo"], "texto": art["texto"]}
    
    hits = search_articles(article_ref, k=3)
    for h in hits:
        if h["artigo"].lower() == article_ref.lower():
            return {"artigo": h["artigo"], "texto": h["texto"]}
    return None

def article_exists(article_ref: str) -> bool:
    return get_article(article_ref) is not None