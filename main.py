from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated, TypedDict, List, Dict, Optional
import os

import aerospike
from langgraph.graph import StateGraph, END, add_messages
from langgraph.checkpoint.aerospike import AerospikeSaver
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


app = FastAPI()

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    intermediate: Optional[Dict[str, str]]


def math_tool(query: str) -> str:
    """Very dumb math parser just for demo."""
    try:
        expr = query.replace("plus", "+").replace("minus", "-")
        return str(eval(expr))
    except Exception:
        return "Sorry, I could not compute that."


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
)


def route(state: State) -> str:
    """Return which path to take: 'math' or 'chat'."""
    last_msg = state["messages"][-1]
    content = last_msg.content.lower()

    if any(x in content for x in ["add", "plus", "sum", "multiply", "times"]):
        return "math"
    return "chat"


def decide_route(state: State) -> State:
    """No-op node: just passes state through; routing is done by `route`."""
    return state


def math_node(state: State) -> State:
    user_msg = state["messages"][-1].content
    result = math_tool(user_msg)
    state["intermediate"] = {"math_result": result}
    return state


def llm_node(state: State) -> State:
    """Call LLM with full message history + optional math result."""
    system = SystemMessage(
        content="You are a helpful assistant. If a math_result is provided, use it in your answer."
    )

    msgs: List[BaseMessage] = [system] + state["messages"]

    if state.get("intermediate") and "math_result" in state["intermediate"]:
        msgs.append(
            SystemMessage(
                content=f"Math tool result: {state['intermediate']['math_result']}"
            )
        )

    resp = llm.invoke(msgs)
    state["messages"].append(resp)
    return state

builder = StateGraph(State)

builder.add_node("decide_route", decide_route)
builder.add_node("math_node", math_node)
builder.add_node("llm_node", llm_node)

builder.set_entry_point("decide_route")

builder.add_conditional_edges(
    "decide_route",
    route,
    {
        "math": "math_node",
        "chat": "llm_node",
    },
)

builder.add_edge("math_node", "llm_node")
builder.add_edge("llm_node", END)


host = os.getenv("AEROSPIKE_HOST", "127.0.0.1")
port = int(os.getenv("AEROSPIKE_PORT", "3000"))

cfg = {"hosts": [(host, port)]}
client = aerospike.client(cfg).connect()

aero_saver = AerospikeSaver(
    client=client,
    namespace="test"
)

graph = builder.compile(checkpointer=aero_saver)

class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    state: State = {
        "messages": [HumanMessage(content=req.message)],
        "intermediate": None,
    }

    result: State = graph.invoke(
        state,
        config={"configurable": {"thread_id": req.thread_id, "checkpoint_ns": "default"}},
    )

    last_msg = result["messages"][-1]
    reply = last_msg.content
    return ChatResponse(reply=reply)
