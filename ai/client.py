from __future__ import annotations
import os
from openai import OpenAI


class LLMError(Exception):
    pass


_DEPLOYMENT_ENV_MAP = {
    "gpt-4o":      "AZURE_OPENAI_DEPLOYMENT_4O",
    "gpt-4o-mini": "AZURE_OPENAI_DEPLOYMENT_4O_MINI",
}


def _create_client() -> OpenAI:
    """Return an OpenAI-compatible client for Azure resource or global endpoint.

    Selection precedence (mirrors your existing integration):
      1. USE_GLOBAL_OPENAI=1  → global endpoint (requires OPENAI_API_KEY)
      2. AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY  → Azure resource endpoint
      3. OPENAI_API_KEY alone  → global endpoint
    """
    use_global = os.environ.get("USE_GLOBAL_OPENAI", "").lower() in {"1", "true", "yes"}
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
    global_endpoint = os.environ.get("OPENAI_ENDPOINT", "https://models.inference.azure.com")
    global_key = os.environ.get("OPENAI_API_KEY")

    if use_global and global_key:
        return OpenAI(base_url=global_endpoint, api_key=global_key)

    if azure_endpoint and azure_key:
        return OpenAI(base_url=azure_endpoint, api_key=azure_key)

    if global_key:
        return OpenAI(base_url=global_endpoint, api_key=global_key)

    raise LLMError(
        "No valid Azure OpenAI configuration found. "
        "Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_KEY in your .env file."
    )


def call_llm(prompt: str, model_key: str, max_tokens: int) -> str:
    """Call the LLM and return the response text.

    Args:
        prompt:     The user prompt to send.
        model_key:  'gpt-4o' or 'gpt-4o-mini' — resolved to deployment/model name via env.
        max_tokens: Maximum tokens for the response.

    Raises:
        LLMError: On unknown model_key, missing env vars, or API failure.
    """
    env_var = _DEPLOYMENT_ENV_MAP.get(model_key)
    if not env_var:
        raise LLMError(f"Unknown model_key: '{model_key}'")

    model_name = os.getenv(env_var)
    if not model_name:
        raise LLMError(f"Env var '{env_var}' is not set. Check your .env file.")

    try:
        client = _create_client()
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"API call failed: {e}") from e
