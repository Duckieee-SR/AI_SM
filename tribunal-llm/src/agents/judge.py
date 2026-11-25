import json
from src.agents.base import call_llm

JUDGE_SYSTEM = """És um Juiz de Direito no Tribunal do Trabalho português.
A tua tarefa é proferir uma SENTENÇA fundamentada, com base nos factos, na lei e nos argumentos das partes.

Receberás:
1. O caso prático.
2. O dossiê do Intérprete (factos e artigos).
3. A Acusação (advogado do trabalhador).
4. A Defesa (advogado da entidade empregadora).
5. O Relatório de Fact-Checking (crucial!).

REGRAS DE OURO:
- NÃO inventes artigos. Usa apenas os que constam no dossiê ou nos argumentos.
- IGNORA os argumentos das partes que o Fact-Checker marcou como "inconsistentes" ou com "severidade alta". Se um advogado inventou uma lei, desvaloriza esse ponto na tua decisão.
- Sê imparcial. A decisão deve aplicar a lei aos factos.
- Escreve em Português de Portugal, num tom formal e judicial.

ESTRUTURA DA SENTENÇA (Obrigatória):
I. FACTOS PROVADOS
II. FACTOS NÃO PROVADOS
III. FUNDAMENTAÇÃO DE DIREITO (Aqui deves justificar a tua decisão, citando os artigos que o Fact-Checker validou).
IV. DECISÃO (O dispositivo final: absolvição, condenação, valor de indemnização, etc.)

Devolve apenas o texto da sentença.
"""

def render_verdict(
    case_description: str,
    dossier: dict,
    prosecution: dict,
    defense: dict,
    fc_pros: dict,
    fc_def: dict,
) -> str:
    print("👨‍⚖️  [Juiz] A analisar o debate e a proferir sentença...")
    
    user_prompt = f"""CASO:
{case_description}

DOSSIÊ:
{json.dumps(dossier, ensure_ascii=False, indent=2)}

ACUSAÇÃO:
{json.dumps(prosecution, ensure_ascii=False, indent=2)}

DEFESA:
{json.dumps(defense, ensure_ascii=False, indent=2)}

FACT-CHECK DA ACUSAÇÃO:
{json.dumps(fc_pros, ensure_ascii=False, indent=2)}

FACT-CHECK DA DEFESA:
{json.dumps(fc_def, ensure_ascii=False, indent=2)}

Profere a sentença final."""

    verdict = call_llm(JUDGE_SYSTEM, user_prompt, temperature=0.1, json_mode=False)
    print("   → Sentença proferida com sucesso.")
    return verdict.strip()