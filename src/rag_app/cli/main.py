from dotenv import load_dotenv
import argparse
from rag_app.app.models import *
from rag_app.app.core.config import Configurations
from rag_app.app.core.logging_setup import get_logger
from rag_app.app.services.session import Session

#########################################
# The CLI entrypoint is mainly used for development. 
# To launch it, once the rag_app package is installed:
#    
#     rag-app-cli
#
# This launches the CLI with the "default" user.
# To launch it with a specific user:
#    
#     rag-app-cli -u <user_name>
#########################################

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-u",
    "--user",
    default="default"
)

def main():    
    logger = get_logger()
    configs = Configurations.load(logger=logger)
    args = parser.parse_args()

    # start a session
    print("-" * 50)
    print("-" * 50)
    print("***WELCOME TO RAG_APP***")
    print("-" * 50)
    print("-" * 50)
    
    orchestrator = Session(configs=configs)
    orchestrator.load_user(args.user)
    orchestrator.logger.info(f"User loaded: {args.user}")

    while True:
        print(f"\n\nAvailable tools: {orchestrator.tool_client.tool_names}. Attach to end of prompt with --tool_name to call.\n")

        raw_prompt = input("\n>> ")
        prompt, tool_names = orchestrator.cli_parse_prompt(raw_prompt)
        response = orchestrator.process_prompt(prompt=prompt, tool_names=tool_names)
        print(f"Assistant: ")
        print(response.message.content)
    
    # for streaming responses (this doesn't work currently because the chat/completions endpoint doesn't stream.)
    # while True:
    #     print(f"\n\nAvailable tools: {orchestrator.tool_client.tool_names}. Attach to end of prompt with --tool_name to call.\n")
    #     raw_prompt = input("\n>> ")
    #     prompt, tool_names = orchestrator.cli_parse_prompt(raw_prompt)
    #     stream = orchestrator.process_prompt_streaming(prompt=prompt, tool_names=tool_names)
    #     print(f"Assistant: ")
    #     for event in stream:
    #         if event.type == "token":
    #             print(event.content, end="", flush=True)
    #         elif event.type == "error":
    #             print(f"\n[ERROR] {event.content}")
    #             break
    #         elif event.type == "done":
    #             break