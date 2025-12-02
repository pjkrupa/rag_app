import os
from dotenv import load_dotenv
from app.models import *
from app.core.config import set_configs
from app.core.logging_setup import get_logger
from app.tools.registry import TOOLS
from app.services.chat import Chat
from app.services.llm_client import LlmClient
from app.services.tool_handler import ToolHandler
from app.services.orchestrator import Orchestrator

if __name__ == "__main__":
    
    logger = get_logger()
    load_dotenv()
    
    # start a session
    print("-" * 50)
    print("-" * 50)
    print("***WELCOME TO RAG_APP***")
    print("-" * 50)
    print("-" * 50)
    
    orchestrator = Orchestrator(configs=set_configs(logger))
    while True:
        print("Please choose: (1) Existing user; (2) Create user")
        selection = input(">> ")
        try:
            selection = int(selection)
        except Exception as e:
            "Not a valid selection."
            continue
        match selection:
            case 1:
                orchestrator.get_user_name(user_name=input("Enter your user name>> "))
                break
            case 2:
                orchestrator.create_user(user_name=input("Select a user name>> "))
                break
            case _:
                print("Not a valid selection.")
                continue
    
    print("-" * 50)
    print("-" * 50)
    print("Ready for prompt.\n")
    while True:
        print(f"\nAvailable tools: {orchestrator.tool_client.tool_names}. Attach to end of prompt with --tool_name to call.")
        response, documents = orchestrator.process_prompt(prompt=input("\n>> "))
        print(f"Assistant: {response.content}")
        if documents:
            logger.info(documents)