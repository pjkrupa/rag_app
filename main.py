import requests, os
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from models import *
from logging_setup import get_logger
from litellm import completion
from tools import TOOLS
from functions import handle_tool_call, litellm_request
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
    
    # set the system message
    system = Message(
        role="system",
        content=configs.system_prompt
        )
    messages = [system]

    # set the tools
    tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
    print(f"Available tools are: {tools}")

    while True:
        prompt = input("Give me a prompt--> ")
        prompt_message = Message(role="user", content=prompt)
        messages.append(prompt_message)
        response = litellm_request(
            configs=configs, 
            messages=messages, 
            tools=tools
            )

        # Takes the Message class object from LiteLLM and converts it to my Message class object
        lite_msg = response.choices[0].message
        response_message = Message.model_validate(lite_msg.model_dump())

        # Check if the model called a tool:
        if response_message.tool_calls:
            # tool_response should be a Message object with "role" set to "tool"
            tool_message = handle_tool_call(response_message, configs)
            messages.append(tool_message)
            tool_response = litellm_request(
                configs=configs,
                messages=messages,
                tools=tools
            )
            # Takes the Message class object from LiteLLM and converts it to my Message class object
            lite_msg = tool_response.choices[0].message
            final_response_message = Message.model_validate(lite_msg.model_dump())
            print("\nAssistant:", final_response_message.content, "\n")
            messages.append(final_response_message)
        else:
            print("\nAssistant:", response_message.content, "\n")
            messages.append(response_message)





