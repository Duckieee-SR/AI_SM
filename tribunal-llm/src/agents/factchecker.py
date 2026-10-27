# src/agents/factchecker.py
"""Agente de fact-checking — verifica citações legais nos argumentos."""
import json
from src.agents.base import call_llm, parse_json_safe
from src.rag.retriever import get_article


EXTRACT_SYSTEM = """És um assistente rigoroso de fact-checking jurídico.
A tua tarefa é EXTRAIR citações a artigos de lei de um texto argumentativo.

Para cada citação, devolve:
- "artigo": a referência o mais completa possível (ex.: "Artigo 382.º",
  "Artigo 63.º, n.º 1")
- "afirmacao": a afirmação concreta que o autor do texto faz sobre o conteúdo
  desse artigo (o que ele diz que a lei estabelece)

Se o argumento não citar artigos, devolve lista vazia.

DEVOLVE APENAS JSON: {"citacoes": [{"artigo": "...", "afirmacao": "..."}]}"""


VERIFY_SYSTEM = """És um verificador jurídico rigoroso. Recebes uma lista de citações,
cada uma com a afirmação que o advogado fez e o TEXTO REAL do artigo citado.

Para cada citação, avalia:
- "consistente": true se a afirmação está suportada pelo texto real do artigo;
  false se contradiz o texto ou extrapola claramente o seu conteúdo;
- "problema": descrição breve do problema (null se consistente);
- "severidade": "nenhuma" | "baixa" | "media" | "alta"
  (alta = contradiz o texto / inventa conteúdo / atribui ao artigo algo que ele
   não diz).

DEVOLVE APENAS JSON: {"verificacoes": [
  {"artigo": "...", "consistente": true, "problema": null, "severidade": "nenhuma"}
]}"""


def _extract_citations(argument_text: str) -> list:
    raw = call_llm(
        EXTRACT_SYSTEM,
        f"ARGUMENTO:\n{argument_text}",
        temperature=0.0,
        json_mode=True,
    )
    return parse_json_safe(raw).get("citacoes", [])


def _verify_consistency(citacoes: list) -> list:
    if not citacoes:
        return []
    raw = call_llm(
        VERIFY_SYSTEM,
        json.dumps(citacoes, ensure_ascii=False, indent=2),
        temperature=0.0,
        json_mode=True,
    )
    return parse_json_safe(raw).get("verificacoes", [])


def factcheck_argument(argument: dict, label: str = "argumento") -> dict:
    from src.rag.retriever import extract_article_refs, get_article
    print(f"🔍 [Fact-checker] A verificar {label}...")

    argument_text = json.dumps(argument, ensure_ascii=False, indent=2)
    citacoes = _extract_citations(argument_text)
    print(f"   → {len(citacoes)} citação(ões) detectada(s).")

    if not citacoes:
        return {"label": label, "citacoes": [], "invalidos": [],
                "resumo": "Nenhuma citação legal detectada no argumento."}

    # Expande cada citação em uma entrada por referência base
    expanded = []
    for c in citacoes:
        refs = extract_article_refs(c["artigo"])
        if not refs:
            expanded.append({
                "artigo": c["artigo"], "afirmacao": c["afirmacao"],
                "ref_base": None, "existe": False, "texto_real": None,
            })
            continue
        for ref in refs:
            art = get_article(ref)
            expanded.append({
                "artigo": c["artigo"], "afirmacao": c["afirmacao"],
                "ref_base": ref,
                "existe": art is not None,
                "texto_real": art["texto"][:1500] if art else None,
            })

    # Verifica consistência só dos que existem
    existentes = [e for e in expanded if e["existe"]]
    verificacoes = _verify_consistency([
        {"artigo": e["ref_base"], "afirmacao": e["afirmacao"],
         "texto_real": e["texto_real"]}
        for e in existentes
    ])
    vmap = {(v.get("artigo"), v.get("afirmacao", "")[:50]): v for v in verificacoes}

    for e in expanded:
        if e["existe"]:
            # tenta encontrar a verificação correspondente
            v = None
            for (art_ref, _), val in vmap.items():
                if art_ref == e["ref_base"]:
                    v = val
                    break
            v = v or {}
            e["consistente"] = v.get("consistente", True)
            e["problema"] = v.get("problema")
            e["severidade"] = v.get("severidade", "nenhuma")
        else:
            e["consistente"] = False
            e["problema"] = "Artigo NÃO existe no Código do Trabalho."
            e["severidade"] = "alta"

    invalidos = [e for e in expanded
                 if (not e["existe"]) or (e.get("consistente") is False)]

    if invalidos:
        altos = [e for e in invalidos if e.get("severidade") == "alta"]
        resumo = (f"{len(expanded)} referências — {len(invalidos)} com problema "
                  f"({len(altos)} de severidade alta).")
    else:
        resumo = f"{len(expanded)} referências verificadas — todas consistentes."

    print(f"   → {resumo}")
    return {"label": label, "citacoes": expanded,
            "invalidos": invalidos, "resumo": resumo}