# src/state.py
from typing import TypedDict, List


class CourtState(TypedDict, total=False):
    """Estado partilhado do 'tribunal' multiagente — matéria laboral."""

    # Entrada
    case_description: str                     # Descrição do caso laboral

    # Agente 1 — Intérprete da Lei
    law_context: str                          # Artigos recuperados pelo RAG
    interpreter_dossier: str                  # JSON com a análise estruturada

    # Agente 2 — Acusação 
    prosecution_argument: str                 # Argumento da acusação (com citações a artigos relevantes)

    # Agente 3 — Defesa 
    defense_argument: str                     # Argumento da defesa (com citações a artigos relevantes)
    
    # Fact-checker
    factcheck_report: str                     # JSON com validação das citações

    # Agente 4 — Juiz
    verdict: str                              # Sentença/sentença arbitral fundamentada

    # Metadados
    log: List[str]