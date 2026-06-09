"""
Intent Module
Infers declared intent from an initial user message via a NIM LLM call,
then encodes it as an embedding for downstream drift scoring.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from backend.nim_client import complete, embed_single


INTENT_SYSTEM_PROMPT = (
    "You are a concise intent extractor. "
    "Given a user message to an AI agent, respond with exactly one sentence "
    "describing what the agent is being asked to do. "
    "Be specific. Do not add commentary or explanation."
)


@dataclass
class Intent:
    raw_message: str
    inferred_text: str
    embedding: np.ndarray
    prompt_tokens: int = 0
    completion_tokens: int = 0


def infer_intent(user_message: str) -> Intent:
    """
    Infer the agent's declared intent from the initial user message.
    Makes one NIM LLM call to extract a clean intent sentence,
    then one NIM embedding call to encode it.
    """
    result = complete(
        prompt=user_message,
        system=INTENT_SYSTEM_PROMPT,
        max_tokens=128,
    )

    inferred_text = result["text"]
    embedding = embed_single(inferred_text)

    return Intent(
        raw_message=user_message,
        inferred_text=inferred_text,
        embedding=embedding,
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )
