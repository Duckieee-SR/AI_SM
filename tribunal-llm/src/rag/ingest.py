"""Divide o Código Penal por artigos e indexa no ChromaDB."""
import re
from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer

from config import CODIGO_DO_TRABALHO_PATH, CHROMA_DIR, CHROMA_COLLECTION, DATA_DIR
from src.rag.parser import parse_codigo, guardar_grafo

def ingest():
    print("📖 A ler o Código do Trabalho...")
    full_text = CODIGO_DO_TRABALHO_PATH.read_text(encoding="utf-8")

    print("🔬 A fazer parsing estrutural...")
    nos = parse_codigo(full_text)
    print(f"   → {len(nos)} nós (artigos + números + alíneas).")

    # Guarda na pasta DATA_DIR da raiz!
    guardar_grafo(nos, DATA_DIR / "grafo.json")

    artigos = [n for n in nos.values() if n.tipo == "artigo"]
    print(f"   → {len(artigos)} artigos a indexar no Chroma.")

    print("🔢 A carregar modelo de embeddings BGE-M3...")
    model = SentenceTransformer("BAAI/bge-m3")

    print("🧮 A gerar embeddings...")
    texts = [a.texto for a in artigos]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=16)

    print("💾 A guardar no ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    metadatas = []
    for a in artigos:
        metadatas.append({
            "artigo": a.artigo_base,
            "no_id": a.id,
            "referencias": "|".join(a.referencias),
        })

    collection.add(
        embeddings=[e.tolist() for e in embeddings],
        documents=texts,
        metadatas=metadatas,
        ids=[a.id for a in artigos],
    )
    print(f"✅ Ingestão concluída. {len(artigos)} artigos no ChromaDB.")

if __name__ == "__main__":
    ingest()