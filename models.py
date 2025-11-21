from pydantic import BaseModel
from enum import Enum
from typing import Literal, Dict, Any
from tools import ToolName

def make_enum(name: str, values: list[str]):
    return Enum(name, {v: v for v in values})

# -----------------------------
# Function definition (for sending TO the model)
# -----------------------------
class FunctionDefinition(BaseModel):
    name: Literal[ToolName]
    description: str = ""
    parameters: dict[str, Any]

class Tool(BaseModel):
    type: str = "function"
    function: FunctionDefinition

# -----------------------------
# Function call (returned FROM the model)
# -----------------------------
class FunctionCall(BaseModel):
    name: str | None = None
    arguments: str | None = None

class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: FunctionCall

# -----------------------------
# Standard message model that works for both sent and received messages
# -----------------------------
class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    function_call: FunctionCall | None = None
    provider_specific_fields: dict | None = None

# -----------------------------
# Brings everything together to formulate the LiteLLM request
# -----------------------------
class Parameters(BaseModel):
    model: str
    messages: list[Message]
    tools: list[Tool] | None = None
    stream: bool = False
    api_base: str | None = None

# -----------------------------
# Models a single result from a ChromaDB query
# -----------------------------
class ChromaDbResult(BaseModel):
    id: str
    document: str
    metadata: dict
    distance: float


# tracks the current state of a conversation
class State(BaseModel):
    tokens: int