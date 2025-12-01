from litellm import completion
from app.core.config import Configurations
from app.models import Tool, Message, Parameters

class LlmClient:
    def __init__(
            self, 
            configs: Configurations):
        self.configs = configs

    # TODO: need to add error handling and retries for this.
    def send_request(
            self, 
            messages: list[Message],
            tool: Tool | None = None
        ) -> Message:

        params = Parameters(
                model=self.configs.model, 
                messages=messages, 
                api_base=self.configs.ollama_api_base, 
                tools=[tool] if tool is not None else None,
                )
        return completion(**params.model_dump(exclude_none=True))
    
    def get_messsage(self, response):
        lite_msg = response.choices[0].message
        return Message.model_validate(lite_msg.model_dump())