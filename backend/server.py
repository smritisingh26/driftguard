"""
DriftGuard FastAPI Backend
Exposes endpoints for the React dashboard to:
  - Run an agent session and get drift results
  - Retrieve stored run results for comparison
  - Health check
"""
import json
import os
import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import FRONTEND_URL, DRIFT_THRESHOLD
from backend.intent.infer import infer_intent
from backend.detector.drift import DriftDetector
from backend.agent.doc_qa import run_agent
from backend.agent.code_gen import run_code_agent

app = FastAPI(title="DriftGuard API", version="1.0.0")

_frontend_origin = FRONTEND_URL.rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

PDF_PATH = Path("demo/lease_agreement.pdf")


# ── Request / Response models ─────────────────────────────────────────────────

class RunRequest(BaseModel):
    user_message: str
    distraction_message: Optional[str] = None
    run_label: Optional[str] = None
    scenario: str = "lease_qa"  # "lease_qa" | "code_gen"


class StepScoreOut(BaseModel):
    step_index: int
    tool_name: str
    tool_input: str
    tool_output: str
    per_step_score: float
    trajectory_score: float
    is_drift: bool
    is_recovery: bool
    prompt_tokens: int
    completion_tokens: int
    from_distraction: bool = False


class RunResult(BaseModel):
    run_id: str
    run_label: str
    user_message: str
    inferred_intent: str
    distraction_message: Optional[str]
    drift_threshold: float
    steps: List[StepScoreOut]
    summary: dict
    final_answer: str
    created_at: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/run", response_model=RunResult)
def run(req: RunRequest):
    """
    Run a full agent session:
    1. Infer intent from user message
    2. Run agent with drift detection
    3. Store and return results
    """
    if req.scenario == "lease_qa" and not PDF_PATH.exists():
        raise HTTPException(status_code=404,
            detail="Lease PDF not found. Run demo/generate_lease.py first.")

    # Step 1: Infer intent
    try:
        intent = infer_intent(req.user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent inference failed: {e}")

    # Step 2: Run agent with drift detection
    # Code gen tasks have smaller inter-task embedding distances than doc QA,
    # so use a lower threshold calibrated to the observed score distribution.
    drift_threshold = 0.38 if req.scenario == "code_gen" else DRIFT_THRESHOLD
    detector = DriftDetector(intent_embedding=intent.embedding, threshold=drift_threshold)
    try:
        if req.scenario == "code_gen":
            agent_result = run_code_agent(
                user_message=req.user_message,
                intent=intent,
                detector=detector,
                distraction_message=req.distraction_message,
            )
        else:
            agent_result = run_agent(
                user_message=req.user_message,
                pdf_path=str(PDF_PATH),
                intent=intent,
                detector=detector,
                distraction_message=req.distraction_message,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}")

    # Step 3: Build result
    run_id = str(uuid.uuid4())[:8]

    # Strip any "Final Answer:" / "Agent Final Answer:" prefix the LLM may have emitted
    raw_answer = agent_result["final_answer"]
    for prefix in ("Agent Final Answer:", "Final Answer:", "Agent Final Answer :", "Final Answer :"):
        if raw_answer.startswith(prefix):
            raw_answer = raw_answer[len(prefix):].strip()
            break

    result = RunResult(
        run_id=run_id,
        run_label=req.run_label or f"Run {run_id}",
        user_message=req.user_message,
        inferred_intent=intent.inferred_text,
        distraction_message=req.distraction_message,
        drift_threshold=drift_threshold,
        steps=[StepScoreOut(**{
            "step_index": s.step_index,
            "tool_name": s.tool_name,
            "tool_input": s.tool_input,
            "tool_output": s.tool_output,
            "per_step_score": s.per_step_score,
            "trajectory_score": s.trajectory_score,
            "is_drift": s.is_drift,
            "is_recovery": s.is_recovery,
            "prompt_tokens": s.prompt_tokens,
            "completion_tokens": s.completion_tokens,
            "from_distraction": s.from_distraction,
        }) for s in agent_result["step_scores"]],
        summary=agent_result["summary"],
        final_answer=raw_answer,
        created_at=time.time(),
    )

    # Persist run
    run_path = RUNS_DIR / f"{run_id}.json"
    with open(run_path, "w") as f:
        json.dump(result.dict(), f, indent=2)

    return result


@app.get("/runs", response_model=List[RunResult])
def list_runs():
    """Return all stored runs, newest first."""
    runs = []
    for path in RUNS_DIR.glob("*.json"):
        with open(path) as f:
            try:
                runs.append(RunResult(**json.load(f)))
            except Exception:
                continue
    runs.sort(key=lambda r: r.created_at, reverse=True)
    return runs


@app.get("/runs/{run_id}", response_model=RunResult)
def get_run(run_id: str):
    """Return a specific run by ID."""
    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    with open(path) as f:
        return RunResult(**json.load(f))


@app.delete("/runs")
def clear_runs():
    """Clear all stored runs."""
    for path in RUNS_DIR.glob("*.json"):
        path.unlink()
    return {"cleared": True}
