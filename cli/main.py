import os
from app.models import *
from app.core.config import Configurations
from app.core.logging_setup import get_logger
from app.services.orchestrator import Orchestrator

if __name__ == "__main__":
    
    logger = get_logger()
    configs = Configurations.load(logger=logger)

    # start a session
    print("-" * 50)
    print("-" * 50)
    print("***WELCOME TO RAG_APP***")
    print("-" * 50)
    print("-" * 50)
    
    orchestrator = Orchestrator(configs=configs)
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
                orchestrator.cli_get_user_name(user_name=input("Enter your user name>> "))
                break
            case 2:
                orchestrator.cli_create_user(user_name=input("Select a user name>> "))
                break
            case _:
                print("Not a valid selection.")
                continue
    
    print("-" * 50)
    print("-" * 50)
    print("Ready for prompt.\n")
    while True:
        print(f"\nAvailable tools: {orchestrator.tool_client.tool_names}. Attach to end of prompt with --tool_name to call.")
        stream = orchestrator.process_prompt_streaming(prompt=input("\n>> "))
        print(f"Assistant: ")
        for event in stream:
            if event.type == "token":
                print(event.content, end="", flush=True)
            elif event.type == "error":
                print(f"\n[ERROR] {event.content}")
                break
            elif event.type == "done":
                break
        last_message = orchestrator.last_message()
        for doc in last_message.documents:
            print(doc)
