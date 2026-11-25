# src/rag/parser.py
import re
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

RE_ARTIGO = re.compile(r"^Artigo\s+(\d+)\.?\s*º(?:-([A-Z]))?", re.IGNORECASE)
RE_NUMERO = re.compile(r"^(\d+)\s*[-–—]\s*(.+)$")
RE_ALINEA = re.compile(r"^([a-z])\)\s*(.+)$")
RE_REF_NUM = re.compile(r"(\d+)\.?\s*º(?:-([A-Z]))?")
RE_REF_ANTERIOR = re.compile(r"artigo\s+anterior", re.IGNORECASE)

# Dicionário de conceitos para referências implícitas
CONCEITOS_JURIDICOS = {
    # O tema central puxa o bloco todo (noção, procedimento, decisão, efeitos)
    "despedimento": ["351", "353", "354", "355", "356", "357", "358", "361", "382"],
    "insubordinação": ["351", "356"],
    "justa causa": ["351"],
    "nota de culpa": ["353"],
    "resposta à nota de culpa": ["354"],
    "parecer da comissão de trabalhadores": ["355"],
    "processo disciplinar": ["353", "354", "355", "356"],
    
    # Outros temas
    "trabalho suplementar": ["226", "227", "231"],
    "prescrição de créditos laborais": ["337"],
    "contraordenação grave": ["554"],
    "representante sindical": ["445"],
    "assédio": ["29"],
    "acidente de trabalho": ["281"],
    "greve": ["530", "531", "532"],
}

@dataclass
class No:
    id: str
    tipo: str                  # "artigo" | "numero" | "alinea"
    artigo_base: str           # "Artigo 356.º"
    texto: str
    pai: Optional[str] = None
    filhos: list[str] = field(default_factory=list)
    referencias: list[str] = field(default_factory=list)

def _slug_artigo(num: str, letra: Optional[str]) -> str:
    return f"art_{num}" + (f"_{letra.lower()}" if letra else "")

def _resolver_referencias(texto: str, artigo_atual: str, num_atual: int) -> list[str]:
    refs = set()
    for m in RE_REF_NUM.finditer(texto):
        refs.add(_slug_artigo(m.group(1), m.group(2)))
    if RE_REF_ANTERIOR.search(texto):
        refs.add(_slug_artigo(str(num_atual - 1), None))
    texto_lower = texto.lower()
    for conceito, artigos in CONCEITOS_JURIDICOS.items():
        if conceito in texto_lower:
            for num in artigos:
                refs.add(_slug_artigo(num, None))
    refs.discard(artigo_atual)
    return sorted(refs)

def consolidar_artigos(nos: dict[str, No]) -> dict[str, No]:
    """
    Junta o texto de todos os filhos no nó 'artigo' para indexação no Chroma,
    e agrega todas as referências dos filhos para o nó pai.
    """
    for no in nos.values():
        if no.tipo == "artigo":
            partes = [no.texto]
            refs = set(no.referencias)
            
            # Função recursiva para apanhar netos (alíneas)
            def recolher_texto_e_refs(node_id):
                n = nos[node_id]
                partes.append(n.texto)
                refs.update(n.referencias)
                for f_id in n.filhos:
                    recolher_texto_e_refs(f_id)
            
            for filho_id in no.filhos:
                recolher_texto_e_refs(filho_id)
                
            # Atualiza o nó pai com o texto completo e as referências agregadas
            no.texto = "\n".join(partes)
            no.referencias = sorted(list(refs))
            
    return nos

def parse_codigo(texto_completo: str) -> dict[str, No]:
    nos: dict[str, No] = {}
    artigo_atual_id = None
    artigo_atual_base = None
    numero_atual_id = None
    num_artigo = 0

    for linha in texto_completo.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        m_art = RE_ARTIGO.match(linha)
        if m_art:
            num = m_art.group(1)
            letra = m_art.group(2)
            num_artigo = int(num)
            artigo_atual_id = _slug_artigo(num, letra)
            artigo_atual_base = f"Artigo {num}.º" + (f"-{letra}" if letra else "")
            numero_atual_id = None
            nos[artigo_atual_id] = No(
                id=artigo_atual_id, tipo="artigo", artigo_base=artigo_atual_base,
                texto=linha, referencias=_resolver_referencias(linha, artigo_atual_id, num_artigo),
            )
            continue

        m_num = RE_NUMERO.match(linha)
        if m_num and artigo_atual_id:
            n = m_num.group(1)
            numero_atual_id = f"{artigo_atual_id}_n{n}"
            nos[numero_atual_id] = No(
                id=numero_atual_id, tipo="numero", artigo_base=artigo_atual_base,
                texto=linha, pai=artigo_atual_id,
                referencias=_resolver_referencias(linha, artigo_atual_id, num_artigo),
            )
            nos[artigo_atual_id].filhos.append(numero_atual_id)
            continue

        m_al = RE_ALINEA.match(linha)
        if m_al and artigo_atual_id and numero_atual_id:
            letra = m_al.group(1)
            al_id = f"{numero_atual_id}_{letra}"
            nos[al_id] = No(
                id=al_id, tipo="alinea", artigo_base=artigo_atual_base,
                texto=linha, pai=numero_atual_id,
                referencias=_resolver_referencias(linha, artigo_atual_id, num_artigo),
            )
            nos[numero_atual_id].filhos.append(al_id)
            continue

        alvo = numero_atual_id or artigo_atual_id
        if alvo and alvo in nos:
            nos[alvo].texto += "\n" + linha
            for r in _resolver_referencias(linha, artigo_atual_id, num_artigo):
                if r not in nos[alvo].referencias:
                    nos[alvo].referencias.append(r)

    return consolidar_artigos(nos)

def guardar_grafo(nos: dict[str, No], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {k: asdict(v) for k, v in nos.items()}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Grafo guardado em {path} ({len(nos)} nós)")

def carregar_grafo(path: Path) -> dict[str, No]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: No(**v) for k, v in data.items()}