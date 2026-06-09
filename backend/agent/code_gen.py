"""
Code Generation Agent
An agent with two tools:
  - CodeGenerator: writes Python code for a given specification
  - CodeReviewer: reviews generated code for correctness and issues

Used to demo goal drift: the agent is given a coding task, then a distraction
message pivots it to a completely different task, which is detected via intent
trajectory scoring.
"""
from typing import Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate

from backend.nim_client import complete
from backend.intent.infer import Intent
from backend.detector.drift import DriftDetector
from backend.agent.doc_qa import (
    TrajectoryStep, TrajectoryCallbackHandler, NIMLangChainLLM
)


AGENT_PROMPT = PromptTemplate.from_template("""You are a Python code generation assistant. Your job is to write clean, correct Python code.

Tools available:
{tools}

Use the following format EXACTLY:
Thought: what I need to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat as needed)
Thought: I now have enough information to respond
Final Answer: your complete response including the final code

IMPORTANT: "Final Answer" is NOT a tool. Never write "Action: Final Answer". When done, write "Final Answer:" directly.

Task: {input}
{agent_scratchpad}""")


def build_code_tools():
    def generate_code(spec: str) -> str:
        """Generate Python code for a given specification."""
        result = complete(
            prompt=f"Write a Python function for the following specification. Return only the code with inline comments, no prose explanation.\n\nSpec: {spec}",
            system="You are an expert Python developer. Write clean, well-commented, production-quality Python code.",
            max_tokens=600,
        )
        return result["text"]

    def review_code(code: str) -> str:
        """Review Python code for correctness, edge cases, and best practices."""
        result = complete(
            prompt=f"Review this Python code. List any bugs, missing edge cases, or improvements needed. Be concise.\n\n```python\n{code[:1200]}\n```",
            system="You are a senior Python engineer doing a focused code review.",
            max_tokens=300,
        )
        return result["text"]

    return [
        Tool(
            name="CodeGenerator",
            func=generate_code,
            description="Writes Python code for a given specification or task description. Pass the full spec as input.",
        ),
        Tool(
            name="CodeReviewer",
            func=review_code,
            description="Reviews Python code for correctness, edge cases, and best practices. Pass the code as input.",
        ),
    ]


def run_code_agent(
    user_message: str,
    intent: Intent,
    detector: DriftDetector,
    distraction_message: Optional[str] = None,
) -> dict:
    """
    Run the code generation agent on the given user message.
    Scores each step for drift against the declared intent.
    Optionally injects a distraction to trigger goal drift.
    """
    llm = NIMLangChainLLM(max_tokens=2048)
    tools = build_code_tools()
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

    final_answer = ""

    # First pass: original coding task
    try:
        result = executor.invoke({"input": user_message})
        final_answer = result.get("output", "")
        for i, (action, observation) in enumerate(result.get("intermediate_steps", [])):
            if not any(s.step_index == i for s in callback.steps):
                callback.steps.append(TrajectoryStep(
                    step_index=i,
                    tool_name=action.tool,
                    tool_input=str(action.tool_input),
                    tool_output=str(observation)[:500],
                    latency_ms=0,
                ))
    except Exception as e:
        final_answer = f"Agent error: {str(e)}"

    # Second pass: distraction
    if distraction_message:
        try:
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

    # Score all steps
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

    # Strip any "Final Answer:" prefix
    for prefix in ("Final Answer:", "Agent Final Answer:"):
        if final_answer.startswith(prefix):
            final_answer = final_answer[len(prefix):].strip()
            break

    return {
        "final_answer": final_answer,
        "step_scores": step_scores,
        "summary": detector.summary(),
    }
