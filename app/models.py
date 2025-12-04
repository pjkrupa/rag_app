from pydantic import BaseModel
from typing import Literal, Any

# -----------------------------
# Function definition
# -----------------------------
class FunctionDefinition(BaseModel):
    name: str
    description: str = ""
    parameters: dict[str, Any]

class Tool(BaseModel):
    type: str = "function"
    function: FunctionDefinition

# -----------------------------
# Function call
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
# Many of the fields are optional to account for messages that have or don't have tool calls
# -----------------------------
class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
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

# -----------------------------
# Models a message plus the documents from a ChromaDB query, if any
# -----------------------------
class MessageDocuments(BaseModel):
    message: Message
    documents: list[ChromaDbResult] | None = None

# tracks the current state of a conversation
class State(BaseModel):
    tokens: int