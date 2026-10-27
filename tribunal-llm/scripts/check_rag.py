"""Script de validação do pipeline RAG."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retriever import search_articles, article_exists, get_article


def main():
    print("=" * 60)
    print("TESTE 1: Pesquisa semântica")
    print("=" * 60)
    hits = search_articles("Sindicalização", k=3)
    for h in hits:
        print(f"\n[{h['artigo']}]  (distância: {h['distancia']})")
        print(h["texto"][:300].replace("\n", " ") + "...")

    print("\n" + "=" * 60)
    print("TESTE 2: Verificação de existência de artigo")
    print("=" * 60)
    for ref in ["Artigo 131.º", "Artigo 9999.º"]:
        existe = article_exists(ref)
        emoji = "✅" if existe else "❌"
        print(f"{emoji}  {ref}  →  {'existe' if existe else 'NÃO existe'}")
        
        from src.rag.retriever import get_article

def test_article_text():
    for ref in ["Artigo 356.º", "Artigo 101.º-G", "Artigo 351.º", "Artigo 382.º"]:
        art = get_article(ref)
        if art:
            preview = art["texto"][:180].replace("\n", " ")
            print(f"\n✅ {ref}: {preview}...")
            # Deteção de índice:
            if "\t" in art["texto"][:100] and len(art["texto"]) < 300:
                print("   ⚠️  AINDA PARECE ENTRADA DE ÍNDICE")
        else:
            print(f"\n❌ {ref}: não encontrado")

test_article_text()


if __name__ == "__main__":
    main()