# scripts/test_debate.py
"""Testa os agentes de acusação, defesa e fact-checker em sequência."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from config import DATA_DIR
from pathlib import Path
from src.agents.interpreter import interpret_case
from src.agents.prosecutor import build_prosecution
from src.agents.defense import build_defense
from src.agents.factchecker import factcheck_argument


CASO = """Maria Santos trabalhou como programadora na TechLda, S.A., entre Janeiro de 2019
e Fevereiro de 2024, com contrato sem termo. Em 10 de Janeiro de 2024, Maria
apresentou uma queixa na ACT (Autoridade para as Condições do Trabalho) alegando
que a empresa não lhe pagava trabalho suplementar desde 2022.

Em 05 de Fevereiro de 2024, o seu superior hierárquico, Eng. Rui Alves, enviou-lhe
um e-mail a solicitar que trabalhasse no fim-de-semana seguinte. Maria respondeu
por e-mail que não podia, por razões familiares, e que a solicitação não tinha
cabimento legal por não haver regime de turnos nem prevenção de acidente iminente.

Em 12 de Fevereiro de 2024, a TechLda comunicou a Maria o despedimento com
invocação de justa causa, alegando "insubordinação grave e reiterada" e
"quebra da relação de confiança". Maria nunca foi ouvida em processo disciplinar
escrito, nem teve acesso ao processo. Recebeu a comunicação por e-mail, sem
indicação de prazo de impugnação."""


def _print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    # 1. Intérprete
    dossier = interpret_case(CASO, top_k=10)

    # 2. Acusação
    prosecution = build_prosecution(dossier, CASO)

    # 3. Defesa
    defense = build_defense(dossier, prosecution, CASO)

    # 4. Fact-checking
    print("\n🔍 [Fact-checking]")
    fc_pros = factcheck_argument(prosecution, label="acusação")
    fc_def = factcheck_argument(defense, label="defesa")

    # 5. Apresentar
    _print_header("ACUSAÇÃO — Resumo")
    print("Tese:", prosecution.get("tese"))
    for a in prosecution.get("argumentos_principais", []):
        print(f"\n • {a.get('titulo')}")
        print(f"   Artigos: {', '.join(a.get('artigos_citados', []))}")

    _print_header("DEFESA — Resumo")
    print("Tese:", defense.get("tese"))
    for r in defense.get("refutacao_da_acusacao", []):
        print(f"\n ↳ Refuta: {r.get('argumento_da_acusacao')[:80]}...")
        print(f"   Contra: {r.get('contra_argumento')[:120]}...")

    _print_header("FACT-CHECKING — Acusação")
    print(fc_pros["resumo"])
    for c in fc_pros["invalidos"]:
        print(f" ⚠️  {c['artigo']} (severidade {c['severidade']}): {c['problema']}")

    _print_header("FACT-CHECKING — Defesa")
    print(fc_def["resumo"])
    for c in fc_def["invalidos"]:
        print(f" ⚠️  {c['artigo']} (severidade {c['severidade']}): {c['problema']}")

    # Gravar relatório completo para inspecção
    DATA_DIR.mkdir(exist_ok=True)
    report_path = DATA_DIR / "debate_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "dossier": dossier,
            "prosecution": prosecution,
            "defense": defense,
            "factcheck_prosecution": fc_pros,
            "factcheck_defense": fc_def,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Relatório completo gravado em {report_path}")


if __name__ == "__main__":
    main()