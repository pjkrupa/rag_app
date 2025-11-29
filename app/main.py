import os
from dotenv import load_dotenv
from models import *
from core.config import Configurations
from core.logging_setup import get_logger
from tools.registry import TOOLS
from services.chat import Chat
from services.llm_client import LlmClient
from services.tool_handler import ToolHandler

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
    
    # instantiate the chat, tools, and clients
    chat = Chat(configs=configs)
    tools = [Tool(type="function", function=FunctionDefinition.model_validate(tool)) for tool in TOOLS]
    llm_client = LlmClient(configs=configs, tools=tools)
    tool_client = ToolHandler(configs=configs, tools=tools)

    while True:
        prompt_message = Message(role="user", content=input("Give me a prompt--> "))
        chat.add_message(prompt_message)
        response = llm_client.send_request(messages=chat.messages)
        response_message = llm_client.get_messsage(response=response)

        # Check if the model called a tool:
        if response_message.tool_calls:
            # call the tool and get the result as a Message...
            tool_message = tool_client.handle(response_message)
            # ... add the message to the chat
            chat.add_message(tool_message)
            # ... and resend the chat to the LLM:
            tool_response = llm_client.send_request(messages=chat.messages)

            # then pull the message from the response, add it to the chat, and deliver it to the user.
            final_response_message = llm_client.get_messsage(response=tool_response)
            chat.add_message(final_response_message)
            logger.info(f"\nAssistant: {final_response_message.content}\n")
        else:
            chat.add_message(response_message)
            logger.info(f"\nAssistant: {response_message.content}\n")
            





