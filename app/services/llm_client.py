from litellm import completion
from app.core.config import Configurations
from app.models import Tool, Message, Parameters

class LlmClient:
    def __init__(
            self, 
            configs: Configurations, 
            tools: list[Tool]):
        self.configs = configs
        self.tools = tools

    # TODO: need to add error handling and retries for this.
    # TODO: also need to add an optional tools parameter for if user wants to call tools
    def send_request(self, messages: list[Message]
        ) -> Message:
        params = Parameters(
                model=self.configs.model, 
                messages=messages, 
                api_base=self.configs.ollama_api_base, 
                tools=self.tools
                )
        return completion(**params.model_dump())
    
    def get_messsage(self, response):
        lite_msg = response.choices[0].message
        return Message.model_validate(lite_msg.model_dump())