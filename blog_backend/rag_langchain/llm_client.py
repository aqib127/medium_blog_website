"""
rag_langchain/llm_client.py

LLM client for function calling.
Primary: Azure OpenAI
Fallback: Ollama (local dev, with tool calling support)
"""

import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# HELPERS

def _azure_is_configured() -> bool:
    """
    Check if Azure OpenAI is REALLY configured (not placeholder values).
    
    Returns False if:
      - endpoint or key is empty
      - endpoint/key contains placeholder text like "your-openai-resource"
      - endpoint doesn't look like a real Azure OpenAI URL
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()

    if not endpoint or not key:
        return False

    # Reject placeholder values
    placeholders = [
        "your-openai-resource",
        "your-real-key-here",
        "your-azure-openai-api-key",
        "placeholder",
        "example.com",
    ]
    endpoint_lower = endpoint.lower()
    key_lower = key.lower()
    for ph in placeholders:
        if ph in endpoint_lower or ph in key_lower:
            logger.debug(f"Azure OpenAI placeholder detected: '{ph}'")
            return False

    # Must be a real Azure OpenAI endpoint
    if not endpoint.startswith("https://"):
        return False
    if ".openai.azure.com" not in endpoint:
        return False

    # Key must be reasonably long (real Azure keys are 32+ chars)
    if len(key) < 20:
        return False

    return True

# AZURE OPENAI CLIENT

class AzureOpenAIClient:
    def __init__(self):
        from openai import AzureOpenAI

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

        if not endpoint or not api_key:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY required")

        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.3,
    ):
        kwargs = {
            "model": self.deployment,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        return self.client.chat.completions.create(**kwargs)

# OLLAMA CLIENT (with real tool calling)

class OllamaClient:
    """
    Ollama client with native tool-calling support.
    Requires qwen2.5:7b+ or llama3.1:8b+ (7B models support tools).
    """

    def __init__(self):
        import ollama
        self.client = ollama.Client(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        # Prefer OLLAMA_MODEL; fallback to OLLAMA_CHAT_MODEL; then default
        self.model = (
            os.getenv("OLLAMA_MODEL")
            or os.getenv("OLLAMA_CHAT_MODEL")
            or "qwen2.5:3b"
        )
        logger.info(f"OllamaClient initialized with model: {self.model}")

    def chat_with_tools(self, messages, tools=None, tool_choice="auto", temperature=0.3):
        from types import SimpleNamespace

        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": temperature},
            }
            if tools:
                kwargs["tools"] = tools

            resp = self.client.chat(**kwargs)
            msg = resp.get("message", {})
            content = msg.get("content", "") or ""
            raw_tool_calls = msg.get("tool_calls") or []

            # Normalize Ollama tool_calls → OpenAI shape
            tool_calls = None
            if raw_tool_calls:
                tool_calls = []
                for i, tc in enumerate(raw_tool_calls):
                    fn = tc.get("function", {}) or {}
                    args = fn.get("arguments", {})
                    # Ollama sometimes returns dict, sometimes JSON string
                    if isinstance(args, dict):
                        args = json.dumps(args)
                    tool_calls.append(SimpleNamespace(
                        id=f"call_{i}",
                        type="function",
                        function=SimpleNamespace(
                            name=fn.get("name", ""),
                            arguments=args,
                        )
                    ))

            message = SimpleNamespace(content=content, tool_calls=tool_calls)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

        except Exception as e:
            logger.warning(f"Ollama tool calling failed: {e}. Falling back to text.")
            resp = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature},
            )
            content = resp.get("message", {}).get("content", "") or ""
            message = SimpleNamespace(content=content, tool_calls=None)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])


# FACTORY

def get_llm_client():
    """
    Return Azure OpenAI client if properly configured,
    otherwise fall back to Ollama.
    """
    if _azure_is_configured():
        try:
            client = AzureOpenAIClient()
            logger.info("✅ Using Azure OpenAI client")
            return client
        except Exception as e:
            logger.error(f"Azure OpenAI init failed: {e}. Falling back to Ollama.")

    logger.info("⚠️  Using Ollama client (Azure OpenAI not configured)")
    return OllamaClient()