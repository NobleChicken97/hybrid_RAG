"""
LLM client supporting multi-backend architectures as per instructions.md.
Supports: ollama_qwen3, ollama_phi4mini, cerebras, groq, gemini, claude.
"""

import time
from functools import lru_cache

from openai import OpenAI
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, retry_if_exception_type

from app.config import get_settings


class CloudAPIError(Exception):
    """Exception for cloud API failures."""
    pass


class NonRetryableCloudAPIError(CloudAPIError):
    """Cloud API failure that will not succeed on retry (auth, bad request, etc.)."""
    pass


class LocalAPIError(Exception):
    """Exception for local API failures."""
    pass


@lru_cache(maxsize=1)
def _get_ollama_client():
    settings = get_settings()
    # Ollama provides an OpenAI-compatible endpoint at /v1
    return OpenAI(
        base_url=f"{settings.ollama_host.rstrip('/')}/v1",
        api_key="ollama", # required by client, but ignored by ollama
    )


@lru_cache(maxsize=1)
def _get_cerebras_client():
    settings = get_settings()
    if not settings.cerebras_api_key:
        raise ValueError("CEREBRAS_API_KEY is not set.")
    return OpenAI(
        base_url=settings.cerebras_base_url,
        api_key=settings.cerebras_api_key,
    )


@lru_cache(maxsize=1)
def _get_groq_client():
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set.")
    return OpenAI(
        base_url=settings.groq_base_url,
        api_key=settings.groq_api_key,
    )


@lru_cache(maxsize=1)
def _get_gemini_client():
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    # Gemini exposes a first-party OpenAI-compatible endpoint.
    # Explicit short timeout so hung requests fail fast and tenacity can retry.
    return OpenAI(
        base_url=settings.gemini_base_url,
        api_key=settings.gemini_api_key,
        timeout=90.0,
        max_retries=1,
    )


@lru_cache(maxsize=1)
def _get_anthropic_client():
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _generate_ollama(prompt: str, model: str, system_prompt: str = "", max_tokens: int = 1024, temperature: float = 0.1) -> str:
    settings = get_settings()
    if settings.environment == "production":
        raise LocalAPIError("Local model unavailable in this environment")

    client = _get_ollama_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = response.usage
        if usage:
            print(f"[LLM] Ollama ({model}) | Input tokens: {usage.prompt_tokens} | Output tokens: {usage.completion_tokens}")
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise LocalAPIError(f"Local model unavailable in this environment. Detail: {e}") from e


def _is_retryable_cloud_error(e: Exception) -> bool:
    """Retry transient cloud failures; fail fast on 4xx (except 429)."""
    if not isinstance(e, CloudAPIError):
        return False
    if isinstance(e, NonRetryableCloudAPIError):
        return False
    return True


# Long eval runs (1h+) hit transient free-tier connection drops, so retries
# use more attempts and a longer backoff ceiling than a single request needs.
_RETRY_KWARGS = dict(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception(_is_retryable_cloud_error),
)


@retry(**_RETRY_KWARGS)
def _generate_openai_compatible(client: OpenAI, model: str, prompt: str, system_prompt: str = "", max_tokens: int = 1024, temperature: float = 0.1) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = response.usage
        if usage:
            print(f"[LLM] {model} | Input tokens: {usage.prompt_tokens} | Output tokens: {usage.completion_tokens}")
        return response.choices[0].message.content.strip()
    except Exception as e:
        status = getattr(e, "status_code", None)
        print(f"[LLM] Error calling {model}: {e}")
        if isinstance(status, int) and 400 <= status < 500 and status != 429:
            raise NonRetryableCloudAPIError(f"Non-retryable cloud API error ({status}): {e}") from e
        raise CloudAPIError(f"Failed to generate from cloud API: {e}") from e


@retry(**_RETRY_KWARGS)
def _generate_anthropic(prompt: str, system_prompt: str = "", max_tokens: int = 1024, temperature: float = 0.1) -> str:
    client = _get_anthropic_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    try:
        response = client.messages.create(**kwargs)
        result = "".join(block.text for block in response.content if block.type == "text")
        usage = response.usage
        print(f"[LLM] Claude Haiku | Input tokens: {usage.input_tokens} | Output tokens: {usage.output_tokens}")
        return result.strip()
    except Exception as e:
        status = getattr(e, "status_code", None)
        print(f"[LLM] Error calling Claude: {e}")
        if isinstance(status, int) and 400 <= status < 500 and status != 429:
            raise NonRetryableCloudAPIError(f"Non-retryable Anthropic API error ({status}): {e}") from e
        raise CloudAPIError(f"Failed to generate from Anthropic API: {e}") from e


def generate(prompt: str, system_prompt: str = "", backend: str = None, max_tokens: int = 1024, temperature: float = 0.1) -> str:
    """
    Generate a response using the configured LLM provider.
    """
    settings = get_settings()
    backend = backend or settings.llm_backend

    if backend == "ollama_qwen3":
        return _generate_ollama(prompt, model=settings.ollama_model_primary, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    elif backend == "ollama_phi4mini":
        return _generate_ollama(prompt, model=settings.ollama_model_secondary, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    elif backend == "cerebras":
        client = _get_cerebras_client()
        return _generate_openai_compatible(client, model=settings.cerebras_model, prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    elif backend == "groq":
        client = _get_groq_client()
        return _generate_openai_compatible(client, model=settings.groq_model, prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    elif backend == "gemini":
        client = _get_gemini_client()
        return _generate_openai_compatible(client, model=settings.gemini_model, prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    elif backend == "claude":
        return _generate_anthropic(prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    else:
        raise ValueError(f"Unknown LLM backend: {backend!r}. Supported: ollama_qwen3, ollama_phi4mini, cerebras, groq, gemini, claude")
