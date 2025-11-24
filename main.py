import requests, os
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from models import *
from logging_setup import get_logger
from litellm import completion
from tools import TOOLS
from functions import handle_tool_call, Chat, LiteLlmClient
from dataclasses import dataclass
from logging import Logger

if __name__ == "__main__":
    
    # set up logging object
    logger = get_logger()

    # get .env variables
    load_dotenv()

    # get configs
    configs = Configurations(
        model=os.getenv("MODEL"),
        ollama_api_base=os.getenv("OLLAMA_URL"),
        system_prompt=os.getenv("SYSTEM_PROMPT"),
        logger=logger,
        chromadb_host=os.getenv("CHROMADB_HOST"),
        chromadb_port=int(os.getenv("CHROMADB_PORT")),
        embeddings_url=os.getenv("EMBEDDINGS_URL"),
        chroma_top_n=int(os.getenv("CHROMA_TOP_N")),
        rerank_top_n=int(os.getenv("RERANK_TOP_N"))
    )
    
    chat = Chat(configs=configs)
    tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
    lite_client = LiteLlmClient(configs=configs, tools=tools)

    while True:
        prompt_message = Message(role="user", content=input("Give me a prompt--> "))
        chat.add_message(prompt_message)
        response = lite_client.request(messages=chat.messages)
        response_message = lite_client.get_messsage(response=response)

        # Check if the model called a tool:
        if response_message.tool_calls:
            # tool_response should be a Message object with "role" set to "tool"
            tool_message = handle_tool_call(response_message, configs)
            chat.add_message(tool_message)
            tool_response = lite_client.request(messages=chat.messages)
            final_response_message = lite_client.get_messsage(response=tool_response)
            print("\nAssistant:", final_response_message.content, "\n")
            chat.add_message(final_response_message)
        else:
            print("\nAssistant:", response_message.content, "\n")
            chat.add_message(response_message)





