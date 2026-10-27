"""Verifica se o corpus tem texto real dos artigos ou só o índice."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.rag.retriever import get_article

REFS = ["Artigo 356.º", "Artigo 380.º", "Artigo 197.º",
        "Artigo 63.º", "Artigo 101.º-G", "Artigo 331.º"]

for ref in REFS:
    art = get_article(ref)
    print("=" * 70)
    if not art:
        print(f"❌ {ref} — NÃO encontrado")
        continue
    print(f"📄 {art['artigo']}  ({len(art['texto'])} chars)")
    print("-" * 70)
    print(art["texto"][:400])
    print()