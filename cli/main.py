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
    
    print("-" * 50)
    print("-" * 50)
    print("Ready for prompt.\n")
    while True:
        response = orchestrator.process_prompt(prompt=input("\n>> "))
        logger.info(f"Assistant: {response}")

    # chat = Chat(configs=configs)
    # tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
    # llm_client = LlmClient(configs=configs, tools=tools)
    # tool_client = ToolHandler(configs=configs, tools=tools)

    # while True:
    #     prompt_message = Message(role="user", content=input("Give me a prompt--> "))
    #     logger.info(f"\nUser: {prompt_message}")
    #     chat.add_message(prompt_message)
    #     response = llm_client.send_request(messages=chat.messages)
    #     response_message = llm_client.get_messsage(response=response)

    #     # Check if the model called a tool:
    #     if response_message.tool_calls:
    #         # call the tool and get the result as a Message...
    #         tool_message = tool_client.handle(response_message)
    #         # ... add the message to the chat
    #         chat.add_message(tool_message)
    #         # ... and resend the chat to the LLM:
    #         tool_response = llm_client.send_request(messages=chat.messages)

    #         # then pull the message from the response, add it to the chat, and deliver it to the user.
    #         final_response_message = llm_client.get_messsage(response=tool_response)
    #         chat.add_message(final_response_message)
    #         logger.info(f"\nAssistant: {final_response_message.content}\n")
    #     else:
    #         chat.add_message(response_message)
    #         logger.info(f"\nAssistant: {response_message.content}\n")