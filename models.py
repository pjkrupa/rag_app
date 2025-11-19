from pydantic import BaseModel
from typing import Literal

class Function(BaseModel):
    name: str
    description: str = ""
    parameters: dict

class Tool(BaseModel):
    type: str = "function"
    function: Function

class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: dict  # {"name": str, "arguments": json-string}

class FunctionCall(BaseModel):
    name: str | None = None
    arguments: str | None = None

class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    function_call: FunctionCall | None = None
    provider_specific_fields: dict | None = None

class Tools(BaseModel):
    tools: list[Tool]

class Parameters(BaseModel):
    model: str
    messages: list[Message]
    tools: list[Tool] | None = None
    stream: bool = False
    api_base: str | None = None

# tracks the current state of a conversation
class State(BaseModel):
    tokens: int 