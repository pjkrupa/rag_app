from pydantic import BaseModel
from enum import Enum
from typing import Literal, Dict, Any
from tools import ToolName
from logging import Logger
from dataclasses import dataclass

@dataclass
class Configurations:
    model: str
    ollama_api_base: str
    system_prompt: str
    logger: Logger
    chromadb_host: str
    chromadb_port: int
    embeddings_url: str
    chroma_top_n: int
    rerank_top_n: int

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
    name: Literal["gdpr_query"] | None = None
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

# tracks the current state of a conversation
class State(BaseModel):
    tokens: int