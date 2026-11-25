import sys
import json
import argparse
from pathlib import Path

# Garantir que a raiz está no path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_DIR, BASE_DIR
from src.agents.interpreter import interpret_case
from src.agents.prosecutor import build_prosecution
from src.agents.defense import build_defense
from src.agents.factchecker import factcheck_argument
from src.agents.judge import render_verdict

def obter_caso(file_path: Path) -> str:
    """Lê o caso do ficheiro. Aborta se não existir."""
    if not file_path.exists():
        print(f"❌ ERRO: Ficheiro '{file_path.name}' não encontrado na raiz do projeto.")
        print(f"   Por favor, cria o ficheiro e insere lá o caso prático.")
        sys.exit(1)
    
    texto = file_path.read_text(encoding="utf-8").strip()
    if not texto:
        print(f"❌ ERRO: O ficheiro '{file_path.name}' está vazio.")
        sys.exit(1)
        
    return texto

def main():
    parser = argparse.ArgumentParser(description="Tribunal LLM - Simulador de Julgamento Laboral")
    parser.add_argument(
        "--file", 
        type=str, 
        default="Caso.txt", 
        help="Nome do ficheiro de texto com o caso prático (default: Caso.txt)"
    )
    args = parser.parse_args()

    caminho_caso = BASE_DIR / args.file
    caso_texto = obter_caso(caminho_caso)

    print("=" * 60)
    print(" TRIBUNAL LLM - INÍCIO DA SESSÃO ")
    print("=" * 60)
    print(f"📄 Caso carregado de: {caminho_caso.name}\n")

    # 1. Intérprete
    dossier = interpret_case(caso_texto, top_k=5)

    # 2. Acusação
    prosecution = build_prosecution(dossier, caso_texto)

    # 3. Defesa
    defense = build_defense(dossier, prosecution, caso_texto)

    # 4. Fact-checking
    print("\n🔍 [Fact-checking] A verificar as alegações das partes...")
    fc_pros = factcheck_argument(prosecution, label="acusação")
    fc_def = factcheck_argument(defense, label="defesa")

    # 5. O Juiz
    verdict = render_verdict(caso_texto, dossier, prosecution, defense, fc_pros, fc_def)

    # 6. Apresentar a Sentença
    print("\n" + "=" * 60)
    print(" SENTENÇA FINAL ")
    print("=" * 60)
    print(verdict)

    # 7. Gravar os resultados
    DATA_DIR.mkdir(exist_ok=True)
    
    # Gravar a sentença em txt
    out_path = DATA_DIR / "sentenca_final.txt"
    out_path.write_text(verdict, encoding="utf-8")
    print(f"\n💾 Sentença gravada em: {out_path}")

    # Gravar o relatório completo em JSON (opcional, para debug)
    report_path = DATA_DIR / "relatorio_completo.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "dossier": dossier,
            "prosecution": prosecution,
            "defense": defense,
            "factcheck_prosecution": fc_pros,
            "factcheck_defense": fc_def,
            "verdict": verdict
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()