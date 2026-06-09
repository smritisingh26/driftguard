"""
Drift Detector
Computes per-step and trajectory-level drift scores against a declared intent.

Per-step score:   cosine distance between intent embedding and step embedding
Trajectory score: cosine distance between intent embedding and the mean of
                  a rolling window of recent step embeddings

Recovery detection: a step is flagged as a recovery event when its per-step
score drops back below threshold after one or more steps above threshold.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from backend.config import DRIFT_THRESHOLD, TRAJECTORY_WINDOW
from backend.nim_client import embed_single


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Returns cosine distance (1 - cosine similarity). Range [0, 2]."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    similarity = np.dot(a, b) / (norm_a * norm_b)
    # Clamp to [0, 1] for interpretability as a drift score
    return float(np.clip(1.0 - similarity, 0.0, 1.0))


@dataclass
class StepScore:
    step_index: int
    step_description: str          # Human-readable label for the dashboard
    tool_name: str
    tool_input: str
    tool_output: str
    per_step_score: float
    trajectory_score: float
    is_drift: bool                  # Per-step score exceeds threshold
    is_recovery: bool               # Per-step score dropped back below threshold
    prompt_tokens: int = 0
    completion_tokens: int = 0
    from_distraction: bool = False


class DriftDetector:
    """
    Stateful drift detector for a single agent run.
    Call .score_step() after each agent step.
    """

    def __init__(self, intent_embedding: np.ndarray, threshold: float = DRIFT_THRESHOLD):
        self.intent_embedding = intent_embedding
        self.threshold = threshold
        self.step_embeddings: List[np.ndarray] = []
        self.scores: List[StepScore] = []
        self._prev_was_drift = False

    def score_step(
        self,
        step_index: int,
        tool_name: str,
        tool_input: str,
        tool_output: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        from_distraction: bool = False,
    ) -> StepScore:
        """
        Score a single agent step against the declared intent.
        Embeds a description of the step, computes per-step and trajectory scores.
        """
        # Build a step description for embedding
        step_description = f"Tool: {tool_name}. Input: {tool_input[:200]}. Output: {tool_output[:200]}"
        step_emb = embed_single(step_description)
        self.step_embeddings.append(step_emb)

        # Per-step drift score
        per_step = cosine_distance(self.intent_embedding, step_emb)

        # Trajectory score: cosine distance between intent and mean of rolling window
        window = self.step_embeddings[-TRAJECTORY_WINDOW:]
        trajectory_mean = np.mean(window, axis=0)
        trajectory = cosine_distance(self.intent_embedding, trajectory_mean)

        is_drift = per_step > self.threshold

        # Recovery: was drifting last step, now back below threshold
        is_recovery = self._prev_was_drift and not is_drift

        self._prev_was_drift = is_drift

        score = StepScore(
            step_index=step_index,
            step_description=step_description,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            per_step_score=round(per_step, 4),
            trajectory_score=round(trajectory, 4),
            is_drift=is_drift,
            is_recovery=is_recovery,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            from_distraction=from_distraction,
        )
        self.scores.append(score)
        return score

    def unrecovered_drift(self) -> bool:
        """True if the run ended with unrecovered drift."""
        if not self.scores:
            return False
        return self.scores[-1].is_drift

    def summary(self) -> dict:
        """Return a summary dict for the dashboard."""
        if not self.scores:
            return {}
        drift_steps = [s for s in self.scores if s.is_drift]
        recovery_steps = [s for s in self.scores if s.is_recovery]
        total_prompt = sum(s.prompt_tokens for s in self.scores)
        total_completion = sum(s.completion_tokens for s in self.scores)

        return {
            "total_steps": len(self.scores),
            "drift_steps": len(drift_steps),
            "recovery_steps": len(recovery_steps),
            "unrecovered_drift": self.unrecovered_drift(),
            "max_per_step_score": round(max(s.per_step_score for s in self.scores), 4),
            "mean_trajectory_score": round(
                sum(s.trajectory_score for s in self.scores) / len(self.scores), 4
            ),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
        }
