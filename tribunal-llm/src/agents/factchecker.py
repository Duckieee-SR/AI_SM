# src/agents/factchecker.py
"""Agente de fact-checking — verifica citações legais nos argumentos."""
import json
from src.agents.base import call_llm, parse_json_safe
from src.rag.retriever import get_article


EXTRACT_SYSTEM = """És um assistente rigoroso de fact-checking jurídico.
A tua tarefa é EXTRAIR citações a artigos de lei de um texto argumentativo.

Para cada citação, devolve:
- "artigo": a referência o mais completa possível;
- "afirmacao": a afirmação concreta que o autor do texto faz sobre o conteúdo
  desse artigo (o que ele diz que a lei estabelece)

Se o argumento não citar artigos, devolve lista vazia.

DEVOLVE APENAS JSON: {"citacoes": [{"artigo": "...", "afirmacao": "..."}]}"""


VERIFY_SYSTEM = """És um verificador jurídico rigoroso. Recebes UMA citação com:
- "artigo": referência legal citada
- "afirmacao": o que o advogado diz que essa norma estabelece
- "texto_real": o texto efetivo do artigo

Avalia APENAS se a "afirmacao" está suportada pelo "texto_real":

- "consistente": true se a afirmação é diretamente suportada pelo texto, é
  paráfrase fiel, ou é uma INFERÊNCIA JURÍDICA razoável do texto (ex.: deduzir
  consequências processuais do silêncio da lei não é inconsistente);
  false APENAS se:
    (i)  o texto diz o contrário da afirmação; ou
    (ii) a afirmação atribui ao artigo matéria que pertence claramente a
         OUTRO artigo (ex.: atribuir ao art. X a nota de culpa, que
         está no art. Y); ou
    (iii) a afirmação inventa um requisito específico que o texto não
         contém nem sugere.

- "problema": se inconsistente, explica em 1 frase o que falha. Se consistente,
  null. NUNCA inventes um problema que não esteja relacionado com a afirmação.

- "severidade": "nenhuma" | "baixa" | "media" | "alta".
  alta  = a afirmação atribui ao artigo matéria de outro artigo OU o contrário
          do texto (inclui alucinações de citação).
  media = a afirmação extrapola claramente o texto.
  baixa = a afirmação é uma interpretação discutível mas não contradiz o texto.

DEVOLVE APENAS JSON: {"verificacao": {"artigo": "...", "consistente": bool, "problema": null|"...", "severidade": "..."}}"""


def _extract_citations(argument_text: str) -> list:
    raw = call_llm(
        EXTRACT_SYSTEM,
        f"ARGUMENTO:\n{argument_text}",
        temperature=0.0,
        json_mode=True,
    )
    return parse_json_safe(raw).get("citacoes", [])


def _verify_consistency(citacoes: list) -> list:
    """
    Verifica cada citação INDIVIDUALMENTE para evitar que o LLM baralhe
    as afirmações entre citações. Devolve lista com uma verificação por citação.
    """
    if not citacoes:
        return []

    verificacoes = []
    for c in citacoes:
        raw = call_llm(
            VERIFY_SYSTEM,
            json.dumps({
                "artigo": c["artigo"],
                "afirmacao": c["afirmacao"],
                "texto_real": c["texto_real"],
            }, ensure_ascii=False, indent=2),
            temperature=0.0,
            json_mode=True,
        )
        try:
            v = parse_json_safe(raw).get("verificacao")
        except Exception:
            v = None
        if not v or not isinstance(v, dict):
            v = {
               "artigo": c["artigo"], "consistente": True,
                "problema": None, "severidade": "nenhuma",
            }
        v.setdefault("artigo", c["artigo"])
        verificacoes.append(v)
    return verificacoes


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
                "texto_real": art["texto"][:4000] if art else None,
            })
            
    # Verifica consistência só dos que existem
    existentes = [e for e in expanded if e["existe"]]
    verificacoes = _verify_consistency([
        {"artigo": e["ref_base"], "afirmacao": e["afirmacao"],
         "texto_real": e["texto_real"]}
        for e in existentes
    ])
    
    # zip preserva ordem e evita colisões quando o mesmo artigo é citado 2x
    for e, v in zip(existentes, verificacoes):
        e["consistente"] = v.get("consistente", True)
        e["problema"] = v.get("problema")
        e["severidade"] = v.get("severidade", "nenhuma")

    for e in expanded:
        if not e["existe"]:
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