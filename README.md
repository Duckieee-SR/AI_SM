# ⚖️ Tribunal LLM - Simulador de Julgamento Laboral Multiagente

Este projeto implementa um sistema multiagente baseado em Large Language Models (LLMs) que simula um debate judicial no âmbito do Direito do Trabalho português. 

O sistema recebe um caso prático em linguagem natural, recupera a legislação aplicável do Código do Trabalho (utilizando uma arquitetura GraphRAG) e coloca cinco agentes de IA a debater o caso antes de um Juiz proferir a sentença final.

### 🤖 Os Agentes
1. **Intérprete:** Analisa os factos e mapeia os requisitos legais de forma neutra.
2. **Advogado de Acusação:** Defende os interesses do Trabalhador.
3. **Advogado de Defesa:** Defende os interesses da Entidade Empregadora.
4. **Fact-Checker:** Valida todas as citações legais usadas pelos advogados contra o texto real da lei.
5. **Juiz:** Analisa o debate, desvaloriza argumentos inválidos (alucinações) e profere a sentença final.

---

## 🛠️ Pré-requisitos

Antes de começares, certifica-te que tens:
* **Python 3.12** instalado (versões mais recentes, como a 3.14, podem causar incompatibilidades com as bibliotecas de IA).
* Chaves de API (API Keys) para os modelos de linguagem. O sistema suporta **DeepSeek**, **Google Gemini** e **Groq** (com fallback automático entre eles).

---

## 🚀 Guia de Instalação

### 1. Clonar o repositório e criar o ambiente virtual
```bash
git clone https://github.com/Duckieee-SR/AI_SM.git
cd AI_SM/tribunal-llm

# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
.\venv\Scripts\activate

# No macOS/Linux:
source venv/bin/activate
```
### 2. Instalar as dependências

```bash
pip install -r Requirements.txt
```

### 3. Configurar as Variáveis de Ambiente
Cria um ficheiro chamado .env na raiz do projeto (tribunal-llm/.env) e adiciona as tuas chaves de API:

```env
DEEPSEEK_API_KEY="a_tua_chave_aqui"
GEMINI_API_KEY="a_tua_chave_aqui"
GROQ_API_KEY="a_tua_chave_aqui"
```
Nota: O sistema tentará usar o DeepSeek primeiro. Se falhar (por falta de saldo ou rate limit), tenta o Gemini e, por fim, o Groq.

### 4. Construir a Base de Dados Jurídica (Ingestão)

Antes de correr o simulador, precisas de processar o Código do Trabalho e guardá-lo na base de dados vetorial (ChromaDB). Certifica-te de que o ficheiro data/codigo_do_trabalho.txt está na pasta data/ e corre:

``` bash
python -m src.rag.ingest
```

Este comando vai fazer o parsing estrutural do Código do Trabalho, criar o grafo de referências cruzadas (data/grafo.json) e gerar os embeddings.

## ▶️ Execução

Cria um ficheiro chamado Caso.txt na raiz do projeto e escreve lá o caso prático que queres julgar.

Para iniciar a simulação, corre:

```bash
python main.py
```

Se quiseres testar vários casos sem apagar o anterior, podes criar outros ficheiros (ex: Caso2.txt) e chamá-los assim:

```bash
python main.py --file Caso2.txt
```

### 📂 Resultados (Outputs)

Após a execução, o sistema irá criar na pasta data/:

sentenca_final.txt: A decisão do Juiz, devidamente estruturada (Factos Provados, Fundamentação, Decisão).

relatorio_completo.json: O registo completo do debate (dossiê do intérprete, argumentos da acusação e defesa, e o relatório do fact-checker). Ideal para debugging.


### 📁 Estrutura do Projeto

tribunal-llm/
├── data/                   # Ficheiros de texto do Código do Trabalho e outputs
├── scripts/                # Scripts de teste isolados (RAG, agentes, etc.)
├── src/
|     ├── agents/           # Prompts e lógica dos 5 agentes
|     |     ├── base.py
|     |     ├── interpreter
|     |     ├── prosecutor.py
|     |     ├── defense.py
|     |     ├── factchecker.py
|     |     └── judge.py
|     └── rag/              # Motor de busca jurídico (GraphRAG + Híbrido)
│          ├── parser.py         # Divisão do texto e extração de referências cruzadas
│          ├── hybrid.py         # Pesquisa Híbrida (BM25 + BGE-M3)
│          ├── reranker.py       # Reordenação de contexto (Cross-Encoder)
│          ├── retriever.py      # Injeção de ontologia e travessia no grafo
│          └── ingest.py         # Script para popular a base de dados
├── config.py               # Configurações de caminhos e modelos
├── main.py                 # Ponto de entrada da aplicação
├── Requirements.txt        # Dependências do projeto
├── .env                    # Documento com as Api Keys 
└── Caso.txt                # O caso prático a julgar
