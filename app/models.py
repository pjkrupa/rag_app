from pydantic import BaseModel
from typing import Literal, Any, TypedDict, List, Optional
from logging import Logger

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
    id: int | None = None

# -----------------------------
# Brings everything together to formulate the LiteLLM request
# -----------------------------
class Parameters(BaseModel):
    model: str
    messages: list[Message]
    tools: list[Tool] | None = None
    stream: bool = False

# -----------------------------
# Models a single result from a ChromaDB query
# -----------------------------
class ChromaDbResult(BaseModel):
    id: str
    document: str
    metadata: dict

# -----------------------------
# Models a message plus the documents from a ChromaDB query, if any
# -----------------------------
class MessageDocuments(BaseModel):
    message: Message
    documents: list[ChromaDbResult] | None = None
    id: int | None = None


class ConfigurationsModel(BaseModel):
    model: str
    api_base: str
    chromadb_host: str
    chromadb_port: int
    embeddings_url: str
    chroma_top_n: int
    rerank_top_n: int
    sqlite_path: str
    system_prompt: str

# -----------------------------
# Models for the API accessed by EmbeddingsClient.rerank
# -----------------------------
class RerankItem(BaseModel):
    id: str
    score: float

class RerankResponse(BaseModel):
    query: str
    results: List[RerankItem]

# -----------------------------
# Model for handling streaming
# -----------------------------
class StreamEvent(BaseModel):
    type: Literal["token", "done", "error"]
    content: Optional[str] = None
