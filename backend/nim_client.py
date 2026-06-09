"""
NIM Client
Wraps all calls to NVIDIA NIM endpoints:
  - LLM completions (llama-3.1-8b-instruct)
  - Embeddings (nv-embed-v2)
"""
import requests
import numpy as np
from typing import List
from backend.config import NVIDIA_API_KEY, NIM_BASE_URL, NIM_LLM_MODEL, NIM_EMBED_MODEL


def _headers():
    return {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }


def complete(prompt: str, system: str = "", max_tokens: int = 512, stop: list = None) -> dict:
    """
    Call the NIM LLM endpoint.
    Returns dict with 'text', 'prompt_tokens', 'completion_tokens'.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": NIM_LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    if stop:
        payload["stop"] = stop

    resp = requests.post(
        f"{NIM_BASE_URL}/chat/completions",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "text": data["choices"][0]["message"]["content"].strip(),
        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
    }


def embed(texts: List[str], input_type: str = "query") -> np.ndarray:
    """
    Call the NIM embedding endpoint.
    Use input_type="passage" for document chunks, "query" for search queries.
    Returns a 2D numpy array of shape (len(texts), embedding_dim).
    """
    payload = {
        "model": NIM_EMBED_MODEL,
        "input": texts,
        "input_type": input_type,
        "encoding_format": "float",
    }

    resp = requests.post(
        f"{NIM_BASE_URL}/embeddings",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    vectors = [item["embedding"] for item in data["data"]]
    return np.array(vectors, dtype=np.float32)


def embed_single(text: str) -> np.ndarray:
    """Convenience wrapper for a single text."""
    return embed([text])[0]
