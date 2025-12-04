import time
from litellm import completion, RateLimitError, APIError
from app.core.config import Configurations
from app.models import Tool, Message, Parameters, MessageDocuments
from app.core.errors import LlmCallFailedError
from requests.exceptions import ConnectionError

TRANSIENT_ERRORS = (ConnectionError, TimeoutError)

class LlmClient:
    def __init__(
            self, 
            configs: Configurations):
        self.configs = configs
        self.logger = configs.logger

    def send_request(
            self, 
            messages: list[MessageDocuments],
            tool: Tool | None = None
        ) -> Message:

        messages = [obj.message for obj in messages]
        max_retries = 5
        backoff = 2

        for attempt in range(1, max_retries+1):
            try:
                params = Parameters(
                        model=self.configs.model, 
                        messages=messages, 
                        api_base=self.configs.ollama_api_base, 
                        tools=[tool] if tool is not None else None,
                        )
                return completion(**params.model_dump(exclude_none=True))
            
            except RateLimitError as e:
                if attempt == max_retries:
                    self.logger.error(f"Rate limit persisted after {attempt} attempts: {e}")
                    raise LlmCallFailedError("Rate-limit exhaustion") from e
                self.logger.warning(
                    f"Rate limited. Attempt {attempt}/{max_retries}. "
                    f"Retrying in {backoff}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

            except APIError as e:
                if getattr(e, "status_code", None) in (500, 502, 503, 504):
                    if attempt == max_retries:
                        self.logger.error(f"Server error {e.status_code} after retries: {e}")
                        raise LlmCallFailedError("Server error retries exhausted") from e

                    self.logger.warning(
                        f"Server error {e.status_code}. Attempt {attempt}/{max_retries}. "
                        f"Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30)
                    continue

                # Everything else is fatal
                self.logger.error(f"Unrecoverable API error: {e}")
                raise LlmCallFailedError("Unrecoverable API error") from e

            except TRANSIENT_ERRORS as e:
                if attempt == max_retries:
                    self.logger.error(f"Network error after {attempt} attempts: {e}")
                    raise LlmCallFailedError("Network retries exhausted") from e

                self.logger.warning(
                    f"Transient network error. Attempt {attempt}/{max_retries}. "
                    f"Retrying in {backoff}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
 
            except Exception as e:
                self.logger.error(f"Unrecoverable LLM error: {e}")
                raise LlmCallFailedError("Unrecoverable LLM error") from e

    
    def get_messsage(self, response):
        lite_msg = response.choices[0].message
        return Message.model_validate(lite_msg.model_dump())