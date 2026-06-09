"""
Document QA Agent
A LangChain agent with two tools:
  - DocumentRetrieverTool: chunks a PDF and retrieves relevant sections
  - SummarizationTool: summarizes retrieved content

Wrapped with a LangChain callback handler that emits trajectory steps
for drift scoring after each tool call.
"""
import os
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation, LLMResult as CoreLLMResult

import requests
import numpy as np

from backend.config import (
    NVIDIA_API_KEY, NIM_BASE_URL, NIM_LLM_MODEL, NIM_EMBED_MODEL, DRIFT_THRESHOLD
)
from backend.nim_client import complete, embed
from backend.intent.infer import Intent
from backend.detector.drift import DriftDetector, StepScore


# ── PDF chunking ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
    except Exception:
        pass
    return _demo_lease_text()


def _demo_lease_text() -> str:
    return """
    RESIDENTIAL LEASE AGREEMENT State of California
    LANDLORD: Margaret H. Thornton ADDRESS: 4821 Elmwood Drive, San Jose, CA 95128
    TENANT: Jordan A. Reeves PROPERTY: Unit 4B, 220 Crestview Lane, Mountain View, CA 94040
    LEASE TERM: 12 months, commencing August 1, 2025, ending July 31, 2026
    MONTHLY RENT: $3,200.00 SECURITY DEPOSIT: $6,400.00

    1. RENT PAYMENT: Tenant agrees to pay monthly rent of $3,200.00 on or before the FIRST day
    of each month. A late fee of $150.00 will be assessed for rent received after the 5th day.
    Landlord reserves the right to increase rent upon 60 days written notice. Rent increases
    shall not exceed 5% plus local CPI per California AB 1482.

    2. SECURITY DEPOSIT: Tenant shall deposit $6,400.00. Landlord may withhold amounts for
    unpaid rent, damages beyond normal wear and tear, and cleaning costs. Deposit returned
    within 21 days of vacating. Failure to return may entitle Tenant to statutory damages of
    twice the withheld amount under California Civil Code Section 1950.5.

    3. OCCUPANCY AND USE: Premises occupied solely as residential dwelling. No subletting
    without prior written consent. Violation constitutes material breach and grounds for
    immediate termination.

    4. MAINTENANCE AND REPAIRS: Tenant responsible for minor repairs under $150.00. Landlord
    shall complete repairs within 30 days for non-emergency items. Unauthorized alterations
    strictly prohibited.

    5. ENTRY BY LANDLORD: Landlord may enter with 24-hour advance notice for inspection or
    repairs. In emergency, entry without notice permitted.

    6. PETS: No pets permitted without prior written consent. Unauthorized pets constitute
    material breach. If approved, additional pet fee of $500.00 and monthly pet rent of $75.00.

    7. UTILITIES: Tenant responsible for electricity, gas, internet, cable. Water, trash,
    and sewer included in monthly rent.

    8. TERMINATION AND DEFAULT: Lease terminates July 31, 2026. Early termination results in
    forfeiture of security deposit and liability for remaining rent. Habitual late payment
    (3 or more occurrences) constitutes grounds for non-renewal.

    9. INDEMNIFICATION: Tenant agrees to indemnify Landlord from claims arising from Tenant's
    use of premises. Landlord not liable for loss of Tenant's personal property except for
    gross negligence. Landlord's liability limited to rent abatement for period of
    uninhabitability.

    10. GOVERNING LAW: Agreement governed by laws of California. Disputes resolved in Santa
    Clara County courts. Prevailing party entitled to attorney's fees.
    """


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def build_faiss_index(chunks: List[str]):
    """Build a FAISS index from text chunks using NIM embeddings."""
    import faiss
    embeddings = embed(chunks, input_type="passage")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine after normalization)
    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    index.add(normalized)
    return index, normalized


# ── NIM LLM wrapper for LangChain ─────────────────────────────────────────────

class NIMLangChainLLM(LLM):
    """Thin LangChain LLM wrapper around the NIM completions endpoint."""

    model_name: str = NIM_LLM_MODEL
    max_tokens: int = 512
    _token_log: List[dict] = []

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "nim"

    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs) -> str:
        result = complete(prompt=prompt, max_tokens=self.max_tokens, stop=stop)
        self._token_log.append({
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
        })
        text = result["text"]
        # Strip any partial stop-sequence prefix the API returned before halting
        if stop:
            for seq in stop:
                for prefix_len in range(len(seq), 0, -1):
                    if text.endswith(seq[:prefix_len]):
                        text = text[:-prefix_len]
                        break
        return text

    @property
    def _identifying_params(self) -> dict:
        return {"model_name": self.model_name}


# ── Trajectory callback handler ───────────────────────────────────────────────

@dataclass
class TrajectoryStep:
    step_index: int
    tool_name: str
    tool_input: str
    tool_output: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    from_distraction: bool = False


class TrajectoryCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler that captures every tool call
    as a trajectory step for drift scoring.
    """

    def __init__(self):
        super().__init__()
        self.steps: List[TrajectoryStep] = []
        self._step_counter = 0
        self._tool_start_time: Optional[float] = None
        self._current_tool: str = ""
        self._current_input: str = ""

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        self._tool_start_time = time.time()
        self._current_tool = serialized.get("name", "unknown_tool")
        self._current_input = input_str

    def on_tool_end(self, output: str, **kwargs):
        latency = (time.time() - (self._tool_start_time or time.time())) * 1000
        step = TrajectoryStep(
            step_index=self._step_counter,
            tool_name=self._current_tool,
            tool_input=self._current_input,
            tool_output=str(output)[:500],
            latency_ms=round(latency, 2),
        )
        self.steps.append(step)
        self._step_counter += 1

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        latency = (time.time() - (self._tool_start_time or time.time())) * 1000
        step = TrajectoryStep(
            step_index=self._step_counter,
            tool_name=self._current_tool,
            tool_input=self._current_input,
            tool_output=f"ERROR: {str(error)}",
            latency_ms=round(latency, 2),
        )
        self.steps.append(step)
        self._step_counter += 1


# ── Agent tools ───────────────────────────────────────────────────────────────

def build_tools(pdf_path: str):
    """Build the two agent tools using the provided PDF."""
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(raw_text, chunk_size=80, overlap=15)

    try:
        import faiss
        index, chunk_embeddings = build_faiss_index(chunks)
        use_faiss = True
    except Exception:
        use_faiss = False

    def retrieve(query: str) -> str:
        """Retrieve relevant sections from the lease document."""
        if use_faiss:
            import faiss
            q_emb = embed([query])
            q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-8)
            distances, indices = index.search(q_norm, k=3)
            results = [chunks[i] for i in indices[0] if i < len(chunks)]
            return "\n\n---\n\n".join(results)
        else:
            # Fallback: keyword search
            query_words = set(query.lower().split())
            scored = []
            for chunk in chunks:
                score = sum(1 for w in query_words if w in chunk.lower())
                scored.append((score, chunk))
            scored.sort(reverse=True)
            return "\n\n---\n\n".join(c for _, c in scored[:3])

    def summarize(text: str) -> str:
        """Summarize a section of the lease document."""
        result = complete(
            prompt=f"Summarize the following lease clause concisely, highlighting any risks or obligations for the tenant:\n\n{text[:1500]}",
            max_tokens=256,
        )
        return result["text"]

    return [
        Tool(name="DocumentRetriever",
             func=retrieve,
             description="Retrieves relevant sections from the lease agreement given a search query. Use this to find specific clauses."),
        Tool(name="Summarizer",
             func=summarize,
             description="Summarizes a piece of lease text, highlighting risks and obligations. Pass retrieved text to this tool."),
    ]


# ── Main agent runner ─────────────────────────────────────────────────────────

AGENT_PROMPT = PromptTemplate.from_template("""You are a helpful assistant that analyzes lease agreements.

Tools available:
{tools}

Use the following format EXACTLY:
Thought: what I need to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to answer
Final Answer: your complete answer

IMPORTANT: "Final Answer" is NOT a tool. Never write "Action: Final Answer". When you are done, write "Final Answer:" directly after a Thought line.

Question: {input}
{agent_scratchpad}""")


def run_agent(
    user_message: str,
    pdf_path: str,
    intent: Intent,
    detector: DriftDetector,
    distraction_message: Optional[str] = None,
) -> dict:
    """
    Run the document QA agent on the given user message.
    Scores each step for drift as the agent runs.
    Optionally injects a distraction message mid-run to trigger drift.

    Returns a dict with all step scores and the run summary.
    """
    llm = NIMLangChainLLM(max_tokens=2048)
    tools = build_tools(pdf_path)
    callback = TrajectoryCallbackHandler()

    agent = create_react_agent(llm, tools, AGENT_PROMPT)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        callbacks=[callback],
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    # First pass: run the agent on the original message
    try:
        result = executor.invoke({"input": user_message})
        final_answer = result.get("output", "")
        # Extract steps directly from intermediate_steps as fallback
        for i, (action, observation) in enumerate(result.get("intermediate_steps", [])):
            if not any(s.step_index == i for s in callback.steps):
                from backend.agent.doc_qa import TrajectoryStep
                callback.steps.append(TrajectoryStep(
                    step_index=i,
                    tool_name=action.tool,
                    tool_input=str(action.tool_input),
                    tool_output=str(observation)[:500],
                    latency_ms=0,
                ))
    except Exception as e:
        final_answer = f"Agent error: {str(e)}"

    if distraction_message:
        try:
            # Fresh executor so distraction doesn't inherit original-run context
            distraction_callback = TrajectoryCallbackHandler()
            distraction_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                callbacks=[distraction_callback],
                verbose=True,
                max_iterations=4,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )
            result2 = distraction_executor.invoke({"input": distraction_message})
            offset = len(callback.steps)
            seen_exception = False
            for i, (action, observation) in enumerate(result2.get("intermediate_steps", [])):
                # Deduplicate repeated _Exception steps — keep only the first
                if action.tool == "_Exception":
                    if seen_exception:
                        continue
                    seen_exception = True
                callback.steps.append(TrajectoryStep(
                    step_index=offset + i,
                    tool_name=action.tool,
                    tool_input=str(action.tool_input),
                    tool_output=str(observation)[:500],
                    latency_ms=0,
                    from_distraction=True,
                ))
        except Exception:
            pass

    # Score all trajectory steps
    step_scores = []
    for step in callback.steps:
        score = detector.score_step(
            step_index=step.step_index,
            tool_name=step.tool_name,
            tool_input=step.tool_input,
            tool_output=step.tool_output,
            prompt_tokens=step.prompt_tokens,
            completion_tokens=step.completion_tokens,
            from_distraction=step.from_distraction,
        )
        step_scores.append(score)

    return {
        "final_answer": final_answer,
        "step_scores": step_scores,
        "summary": detector.summary(),
    }
