from enum import Enum

# defines the tools available to the model
TOOLS = [
    {"name": "gdpr_query",
     "description": "Sends a query related to the GDPR to a vector database, returns relevant results.",
     "parameters": {
        "type": "object",
        "properties": {
            "query_text": {
                "type": "string",
                "description": "query string goes here."
            }
        },
    "required": ["query_text"]
}
    },
]

# convert tool names into enum for model
def make_enum(name: str, values: list[str]):
    return Enum(name, {v: v for v in values})

tools = [tool["name"] for tool in TOOLS]
ToolName = make_enum("ToolName", tools)
print(type(ToolName))