TOOLS = [
    {
        "name": "gdpr_query",
        "description": (
            "Runs a semantic vector search against a database of vector embeddings of the full text of the General Data Protection Regulation (GDPR). "
            "Takes a natural-language query and returns the most relevant passages."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query_text": {
                    "type": "string",
                    "description": (
                        "Natural-language query sent to the vector database.\n"
                        "Example: 'What does the GDPR say about data minimization?'"
                    )
                }
            },
            "required": ["query_text"]
        },
    },

    {
        "name": "gdpr_get",
        "description": (
            "Queries a database containing the full text of the General Data Protection Regulation (GDPR) using metadata filtering to retreive a full article, chapter, or section."
            "Use this when you want all passages that belong to a specific article, chapter, or section."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "metadata_filter": {
                    "type": "object",
                    "description": (
                        "A single metadata filter specifying an article, chapter, or section.\n\n"
                        "Examples:\n"
                        "- {\"article\": 9}\n"
                        "- {\"chapter\": 2}\n"
                        "- {\"section\": 1}\n\n"
                        "Use only one metadata key:value pair. Combining multiple metadata keys is not supported."
                    ),
                    "properties": {
                        "article": {"type": "integer"},
                        "chapter": {"type": "integer"},
                        "section": {"type": "integer"}
                    },
                    "additionalProperties": False
                }
            },
            "required": ["metadata_filter"]
        },
    },

    {
        "name": "edpb_query",
        "description": (
            "Runs a semantic vector search against a database of vector embeddings of all the recommendations and guidance issued by the European Data Protection Board. "
            "Takes a natural-language query and returns the most relevant passages."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query_text": {
                    "type": "string",
                    "description": (
                        "Natural-language query sent to the vector database.\n"
                        "Example: 'What guidance has the EDPB issued with regard to data minimization?'"
                    )
                }
            },
            "required": ["query_text"]
        },
    },

]
