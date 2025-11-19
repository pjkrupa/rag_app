import requests, os
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from models import *
from logging_setup import get_logger
from litellm import completion

def send_prompt(prompt: str, messages: list[Message]):
    pass

if __name__ == "__main__":
    
    # get .env variables
    load_dotenv()
    model = os.getenv("MODEL")
    ollama_api_base = os.getenv("OLLAMA_URL")
    system_prompt = os.getenv("SYSTEM_PROMPT")

    # set up logging object
    logger = get_logger()
    
    system = Message(
        role="system",
        content=system_prompt
        )
    messages = [system]
    while True:
        prompt = input("Give me a prompt--> ")
        prompt_message = Message(role="user", content=prompt)
        messages.append(prompt_message)
        params = Parameters(model=model, messages=messages, api_base=ollama_api_base)
        response = completion(**params.model_dump())

        # Takes the Message class object from LiteLLM and converts it to my Message class object
        lite_msg = response.choices[0].message
        response_message = Message.model_validate(lite_msg.model_dump())

        print("\nAssistant:", response_message.content, "\n")
        messages.append(response_message)





