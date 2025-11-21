from enum import Enum

TOOLS = [
    {"name": "gdpr_query",
     "description": "Sends a query related to the GDPR to a vector database, returns relevant results.",
     "parameters": {
         "query_text": "query string goes here."
         }
    },
]

# convert tool names into enum for model
def make_enum(name: str, values: list[str]):
    return Enum(name, {v: v for v in values})

tools = [tool["name"] for tool in TOOLS]
ToolName = make_enum("ToolName", tools)
print(type(ToolName))