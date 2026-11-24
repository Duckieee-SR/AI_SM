"""Divide o Código Penal por artigos e indexa no ChromaDB."""
import re
from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer
from src.rag.retriever import extract_article_refs

from config import CODIGO_DO_TRABALHO_PATH, CHROMA_DIR, CHROMA_COLLECTION, EMBEDDING_MODEL


ARTICLE_RE = re.compile(r"^(Artigo\s+\d+\.º(?:-[A-Z])?)", re.IGNORECASE | re.MULTILINE)


def split_into_articles(full_text: str) -> List[Dict[str, str]]:
    matches = list(ARTICLE_RE.finditer(full_text))
    if not matches:
        raise ValueError("Nenhum 'Artigo X.º' encontrado. Verifica o ficheiro.")

    articles = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        block = full_text[start:end].strip()
        header = match.group(1).strip()
        articles.append({"artigo": header, "texto": block})

    return articles


def ingest():
    print("📖 A ler o Código do Trabalho...")
    full_text = CODIGO_DO_TRABALHO_PATH.read_text(encoding="utf-8")

    print("✂️  A dividir por artigos...")
    articles = split_into_articles(full_text)
    print(f"   → {len(articles)} artigos encontrados.")

    print("🔢 A carregar modelo de embeddings (primeira vez descarrega ~470MB)...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("🧮 A gerar embeddings...")
    texts = [a["texto"] for a in articles]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    print("💾 A guardar no ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Apaga coleção se já existir (para reingestão limpa)
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    metadatas = []
    total_com_refs = 0
    for a in articles:
        refs = extract_article_refs(a["texto"])
        # remove autorreferência (o próprio artigo não deve referenciar-se)
        refs = [r for r in refs if r != a["artigo"]]
        if refs:
            total_com_refs += 1
        metadatas.append({
            "artigo": a["artigo"],
            "referencias": "|".join(refs),  # string vazia se não houver
        })

    print(f"🔗 {total_com_refs}/{len(articles)} artigos têm referências cruzadas.")

    collection.add(
        embeddings=[e.tolist() for e in embeddings],
        documents=texts,
        metadatas=metadatas,
        ids=[f"art_{i}" for i in range(len(articles))],
    )
    print(f"✅ Ingestão concluída. {len(articles)} artigos no ChromaDB.")


if __name__ == "__main__":
    ingest()