# reformatar_codigo_trabalho.py
"""
Reformata o ficheiro 'codigo_do_trabalho.txt' para o formato do 'Secção III.txt'.
- Preserva todo o conteúdo (artigos, notas, hierarquia).
- Normaliza espaços em branco entre artigos (linha em branco entre cada artigo).
- Garante que cada artigo começa com 'Artigo X.º' + título na linha seguinte.
- Normaliza parágrafos numerados para '1 - texto' e alíneas para 'a)\ttexto'.
- Remove linhas em branco espúrias dentro dos artigos.
"""
import re
from pathlib import Path

INPUT  = Path("AI\\tribunal-llm\\data\\codigo_do_trabalho.txt")
OUTPUT = Path("AI\\tribunal-llm\\data\\codigo_do_trabalho_formatado.txt")

# Padrões
RE_ARTIGO   = re.compile(r"^Artigo\s+\d+\.º", re.IGNORECASE)
RE_NUMERO   = re.compile(r"^(\d+)\s*[-–—]\s*(.+)$")            # "1 - texto"
RE_ALINEA   = re.compile(r"^([a-z])\)\s*(.+)$")                # "a) texto"
RE_NOTA     = re.compile(r"^(Alterado|Aditado|Rectificado|Revogado|Suspenso|Notas:)", re.IGNORECASE)

def reformatar(texto: str) -> str:
    linhas = texto.splitlines()
    saida: list[str] = []
    dentro_artigo = False

    for linha_original in linhas:
        linha = linha_original.rstrip()

        # Linha vazia: só mantemos se estivermos fora de artigo (separadores estruturais)
        if not linha.strip():
            if not dentro_artigo:
                # garante apenas uma linha em branco entre blocos estruturais
                if saida and saida[-1].strip() != "":
                    saida.append("")
            continue

        # Cabeçalho de artigo
        if RE_ARTIGO.match(linha.strip()):
            if saida and saida[-1].strip() != "":
                saida.append("")           # linha em branco antes do artigo
            saida.append(linha.strip())
            dentro_artigo = True
            continue

        # Notas de alteração (fim do artigo)
        if RE_NOTA.match(linha.strip()):
            saida.append(linha.strip())
            continue

        # Parágrafo numerado
        m = RE_NUMERO.match(linha.strip())
        if m:
            saida.append(f"{m.group(1)} - {m.group(2)}")
            continue

        # Alínea
        m = RE_ALINEA.match(linha.strip())
        if m:
            saida.append(f"{m.group(1)})\t{m.group(2)}")
            continue

        # Linha de corpo normal
        saida.append(linha.strip() if dentro_artigo else linha)

    return "\n".join(saida).strip() + "\n"


def main():
    texto_original = INPUT.read_text(encoding="utf-8")
    texto_formatado = reformatar(texto_original)
    OUTPUT.write_text(texto_formatado, encoding="utf-8")
    print(f"✅ Documento formatado escrito em: {OUTPUT}")
    print(f"   Linhas: {texto_formatado.count(chr(10))}")


if __name__ == "__main__":
    main()