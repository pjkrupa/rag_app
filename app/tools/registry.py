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