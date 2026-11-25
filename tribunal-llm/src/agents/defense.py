# src/agents/defense.py
"""Agente 3 — Advogado de Defesa (representa a EMPREGADORA)."""
import json
from src.agents.base import call_llm, parse_json_safe


DEFENSE_SYSTEM = """És um advogado experiente do lado da ENTIDADE EMPREGADORA (parte ré / defesa)
num litígio laboral português.

O teu dever é construir a defesa mais forte possível A FAVOR DA ENTIDADE EMPREGADORA,
demonstrando que a sua conduta foi LÍCITA (seja para justificar um despedimento,
para declarar a caducidade do contrato, para validar um processo disciplinar, etc.).

Receberás: (1) o dossiê factual-legal neutro; (2) o argumento já produzido pela
acusação (advogado do trabalhador). Deves REFUTAR esse argumento ponto por ponto.

REGRAS:
1. Cita SEMPRE artigos concretos do Código do Trabalho. Nunca inventes artigos
   ou números de norma — se não tiveres a certeza do número, usa apenas os artigos
   que constam do dossiê.
2. Não inventes factos. Podes reinterpretar os factos existentes a favor da tua
   cliente, mas não introduzas factos novos.
3. Refuta explicitamente cada argumento da acusação — não ignores nenhum.
4. Se a posição da entidade empregadora for muito frágil em algum ponto, é legítimo
   (e próprio de um bom advogado) concentrar esforços nos pontos mais fortes e
   adoptar uma posição mais defensiva no resto.

DEVOLVE APENAS JSON VÁLIDO com este esquema:
{
  "tese": "síntese da posição da entidade empregadora em 2-3 frases",
  "refutacao_da_acusacao": [
    {
      "argumento_da_acusacao": "...",
      "contra_argumento": "...",
      "artigos_citados": ["Artigo [N.º]"]
    }
  ],
  "argumentos_proprios": [
    {
      "titulo": "...",
      "fundamentacao_facto": "...",
      "fundamentacao_direito": "...",
      "artigos_citados": ["Artigo [N.º]"]
    }
  ],
  "pedido": "o que a entidade empregadora pretende (ex.: improcedência total, declaração de caducidade)"
}"""


def build_defense(dossier: dict, prosecution: dict, case_description: str) -> dict:
    print("🛡️  [Defesa] A construir argumento a favor da entidade empregadora...")

    user_prompt = f"""CASO:
{case_description}

DOSSIÊ FACTUAL-LEGAL (do intérprete):
{json.dumps(dossier, ensure_ascii=False, indent=2)}

ARGUMENTO DA ACUSAÇÃO (a refutar):
{json.dumps(prosecution, ensure_ascii=False, indent=2)}

Constrói o argumento de defesa em JSON conforme o esquema."""

    raw = call_llm(
        DEFENSE_SYSTEM,
        user_prompt,
        temperature=0.25,
        json_mode=True,
    )
    argument = parse_json_safe(raw)
    print(f"   → {len(argument.get('refutacao_da_acusacao', []))} refutação(ões) + "
          f"{len(argument.get('argumentos_proprios', []))} argumento(s) próprios.")
    return argument