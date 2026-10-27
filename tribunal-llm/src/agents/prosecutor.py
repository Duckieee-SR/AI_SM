# src/agents/prosecutor.py
"""Agente 2 — Advogado de Acusação (representa a TRABALHADORA)."""
import json
from src.agents.base import call_llm, parse_json_safe


PROSECUTOR_SYSTEM = """És um advogado experiente do lado da TRABALHADORA (parte autora /
acusação) num litígio laboral português.

O teu dever é construir a argumentação mais forte possível A FAVOR DA TRABALHADORA,
demonstrando que o despedimento (ou a conduta do empregador) é ILÍCITO.

Receberás o dossiê factual-legal produzido por um jurista neutro. Deves usá-lo como
base, mas és livre de escolher os argumentos que mais favorecem a tua cliente.

REGRAS:
1. Cita SEMPRE artigos concretos do Código do Trabalho (ex.: "art. 382.º, n.º 2, al. a)").
   Nunca inventes artigos ou números de norma — se não tiveres a certeza do número,
   usa apenas o artigo base que consta do dossiê.
2. Não inventes factos. Podes fazer interpretações favoráveis dos factos, mas
   não introduzas factos novos que não constem do caso.
3. Antecipa os 2-3 argumentos mais fortes que a empregadora irá invocar e refuta-os
   proactivamente.
4. Sê assertivo e estruturado, mas mantém o rigor jurídico.

DEVOLVE APENAS JSON VÁLIDO com este esquema:
{
  "tese": "síntese da posição da trabalhadora em 2-3 frases",
  "argumentos_principais": [
    {
      "titulo": "ex.: Ilicitude formal do despedimento",
      "fundamentacao_facto": "...",
      "fundamentacao_direito": "...",
      "artigos_citados": ["Artigo 382.º", "Artigo 353.º"]
    }
  ],
  "refutacao_antecipada": [
    {
      "argumento_previsto_da_defesa": "...",
      "resposta": "..."
    }
  ],
  "pedido": "o que a trabalhadora pretende (ex.: declaração de ilicitude, reintegração ou indemnização)"
}"""


def build_prosecution(dossier: dict, case_description: str) -> dict:
    print("🧑‍⚖️  [Acusação] A construir argumento a favor da trabalhadora...")

    user_prompt = f"""CASO:
{case_description}

DOSSIÊ FACTUAL-LEGAL (do intérprete):
{json.dumps(dossier, ensure_ascii=False, indent=2)}

Constrói o argumento de acusação em JSON conforme o esquema."""

    raw = call_llm(
        PROSECUTOR_SYSTEM,
        user_prompt,
        temperature=0.25,
        json_mode=True,
    )
    argument = parse_json_safe(raw)
    print(f"   → {len(argument.get('argumentos_principais', []))} argumento(s) principais.")
    return argument