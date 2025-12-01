import os
from dotenv import load_dotenv
from app.models import *
from app.core.config import Configurations
from app.core.logging_setup import get_logger
from app.tools.registry import TOOLS
from app.services.chat import Chat
from app.services.llm_client import LlmClient
from app.services.tool_handler import ToolHandler
from app.services.orchestrator import Orchestrator

if __name__ == "__main__":
    
    # set up logging object
    logger = get_logger()

    # get .env variables
    load_dotenv()

    # set configs
    configs = Configurations(
        model=os.getenv("MODEL"),
        ollama_api_base=os.getenv("OLLAMA_URL"),
        system_prompt=os.getenv("SYSTEM_PROMPT"),
        logger=logger,
        chromadb_host=os.getenv("CHROMADB_HOST"),
        chromadb_port=int(os.getenv("CHROMADB_PORT")),
        embeddings_url=os.getenv("EMBEDDINGS_URL"),
        chroma_top_n=int(os.getenv("CHROMA_TOP_N")),
        rerank_top_n=int(os.getenv("RERANK_TOP_N")),
        sqlite_path=os.getenv("SQLITE_PATH")
    )
    
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
        print(f"Available tools: {orchestrator.tool_client.tool_names}. Attach to end of prompt with --tool_name to call.")
        response = orchestrator.process_prompt(prompt=input("\n>> "))
        logger.info(f"Assistant: {response}")