# src/agents/interpreter.py
"""Agente 1 — Intérprete da Lei (Direito do Trabalho)."""
from src.agents.base import call_llm, parse_json_safe
from src.rag.retriever import search_articles


INTERPRETER_SYSTEM = """És um jurista especializado em DIREITO DO TRABALHO português,
com profundo conhecimento do Código do Trabalho e da legislação laboral conexa.

A tua função é interpretar a lei de forma estritamente NEUTRA e OBJECTIVA.

Receberás: (1) a descrição de um caso laboral; (2) os artigos do Código do Trabalho
considerados potencialmente relevantes.

A tua tarefa:
1. Identifica os artigos efectivamente aplicáveis ao caso (por exemplo: despedimento
   ilícito, justa causa, poder disciplinar, retaliação, assédio, acidente de trabalho,
   trabalho suplementar, férias, etc.).
2. Para cada artigo, decompõe os seus REQUISITOS ou PRESSUPOSTOS legais.
3. Mapeia os factos do caso a cada requisito: "verificado", "não verificado" ou "controvertido".
4. Identifica EXCEPÇÕES ou DEFESAS que possam ser invocadas (ex.: caducidade do
   direito, justa causa, caso de força maior, prescrição, etc.).
5. Lista circunstâncias relevantes (agravantes, atenuantes, contra-ordenações aplicáveis).
6. Lista factos controvertidos e questões abertas.

NÃO emitas juízo sobre a culpa ou razão de nenhuma das partes.
A tua análise é a base para os advogados das partes.

DEVOLVE APENAS JSON VÁLIDO, com este esquema exacto:
{
  "artigos_aplicaveis": [
    {
      "artigo": "Artigo 381.º",
      "materia": "Despedimento por facto imputável ao trabalhador",
      "requisitos": ["requisito 1", "requisito 2", ...],
      "mapeamento_factual": "explicação de como os factos preenchem (ou não) os requisitos"
    }
  ],
  "excepcoes_ou_defesas": ["..."],
  "circunstancias_relevantes": ["..."],
  "factos_controvertidos": ["..."],
  "questoes_abertas": ["..."]
}"""


def interpret_case(case_description: str, top_k: int = 8) -> dict:
    """Corre o agente intérprete e devolve o dossiê como dict."""
    print(f"⚖️  [Intérprete] A analisar o caso laboral e a consultar o RAG (top_k={top_k})...")

    # 1. RAG
    hits = search_articles(case_description, k=top_k)
    law_context = "\n\n".join(
        f"[{h['artigo']}]\n{h['texto']}" for h in hits
    )

    # 2. Prompt
    user_prompt = f"""CASO LABORAL:
{case_description}

ARTIGOS POTENCIALMENTE RELEVANTES (extraídos por RAG — descarta os irrelevantes):
{law_context}

Produz o dossiê jurídico-laboral em JSON conforme instruído."""

    # 3. LLM
    raw = call_llm(
        INTERPRETER_SYSTEM,
        user_prompt,
        temperature=0.1,
        json_mode=True,
    )

    dossier = parse_json_safe(raw)
    print(f"   → {len(dossier.get('artigos_aplicaveis', []))} artigo(s) seleccionado(s).")
    return dossier