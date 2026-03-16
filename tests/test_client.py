import pytest
from unittest.mock import patch, MagicMock
from ai.client import call_llm, LLMError


def test_raises_on_unknown_model_key():
    with pytest.raises(LLMError, match="Unknown model_key"):
        call_llm("prompt", "gpt-99", 100)


def test_raises_when_deployment_not_set(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_4O_MINI", raising=False)
    with pytest.raises(LLMError, match="not set"):
        call_llm("prompt", "gpt-4o-mini", 100)


@patch("ai.client.OpenAI")
def test_returns_content_azure_resource_mode(mock_openai, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_4O_MINI", "deploy-mini")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://x.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        "MOVE: e2e4\nOBSERVATION: test"
    )
    result = call_llm("prompt", "gpt-4o-mini", 150)
    assert result == "MOVE: e2e4\nOBSERVATION: test"


@patch("ai.client.OpenAI")
def test_returns_content_global_mode(mock_openai, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_4O_MINI", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "global-key")
    monkeypatch.setenv("USE_GLOBAL_OPENAI", "1")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_KEY", raising=False)
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "MOVE: d2d4\nOBSERVATION: ok"
    result = call_llm("prompt", "gpt-4o-mini", 150)
    assert result == "MOVE: d2d4\nOBSERVATION: ok"


@patch("ai.client.OpenAI")
def test_raises_llm_error_on_api_failure(mock_openai, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_4O_MINI", "deploy-mini")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://x.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API down")
    with pytest.raises(LLMError, match="API call failed"):
        call_llm("prompt", "gpt-4o-mini", 150)
