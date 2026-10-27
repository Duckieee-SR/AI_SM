# src/agents/base.py
"""Wrapper unificado para chamadas a LLMs (Gemini com fallback para Groq)."""
import json
import time
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import (
    GEMINI_API_KEY,
    GROQ_API_KEY,
    GEMINI_MODEL,
    GROQ_MODEL,
)


class LLMError(RuntimeError):
    pass


def _get_llm(provider: str, temperature: float, json_mode: bool):
    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=temperature,
        )
        # Gemini não usa response_format (OpenAI); usa response_mime_type
        if json_mode:
            llm = llm.bind(response_mime_type="application/json")
    elif provider == "groq":
        llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=temperature,
        )
        if json_mode:
            llm = llm.bind(response_format={"type": "json_object"})
    else:
        raise ValueError(f"Provider desconhecido: {provider}")
    return llm


def _normalize_content(content) -> str:
    """
    Normaliza a saída do LLM para uma string.
    - Gemini pode devolver lista de blocos: [{'type': 'text', 'text': '...'}]
    - Pode devolver dict em alguns casos
    - Pode devolver None em falhas silenciosas
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if "text" in block:
                    parts.append(str(block["text"]))
                elif "content" in block:
                    parts.append(str(block["content"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    json_mode: bool = False,
    providers: Optional[list] = None,
    max_retries: int = 2,
) -> str:
    """Chama o LLM com fallback automático entre providers."""
    providers = providers or ["gemini", "groq"]
    errors = []

    for provider in providers:
        for attempt in range(max_retries + 1):
            try:
                llm = _get_llm(provider, temperature, json_mode)
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = llm.invoke(messages)
                content = _normalize_content(response.content)

                if not content.strip():
                    raise LLMError(f"[{provider}] resposta vazia do LLM")

                return content

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate" in err_str.lower():
                    if attempt < max_retries:
                        wait = 15 * (attempt + 1)
                        print(f"  ⏳ Rate limit em {provider}, aguardando {wait}s...")
                        time.sleep(wait)
                        continue
                errors.append(f"[{provider}] {err_str[:200]}")
                break

    raise LLMError("Todos os providers falharam:\n" + "\n".join(errors))


def parse_json_safe(raw) -> dict:
    """Faz parse de JSON tolerando markdown fences e tipos inesperados."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"Resposta do LLM vazia ou inválida: {raw!r}")

    raw = raw.strip()

    # Remove ```json ... ```
    if raw.startswith("```"):
        lines = raw.split("\n")
        if len(lines) > 2:
            raw = "\n".join(lines[1:-1])

    # Remove eventuais prefixos antes do primeiro '{'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido do LLM: {e}\n---\n{raw[:800]}")