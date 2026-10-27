# scripts/test_interpreter.py
"""Testa o agente intérprete com um caso laboral."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from src.agents.interpreter import interpret_case


CASO = """
Maria Santos trabalhou como programadora na TechLda, S.A., entre Janeiro de 2019
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
indicação de prazo de impugnação.
"""


def main():
    dossier = interpret_case(CASO, top_k=10)
    print("\n" + "=" * 60)
    print("DOSSIÊ JURÍDICO-LABORAL")
    print("=" * 60)
    print(json.dumps(dossier, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()