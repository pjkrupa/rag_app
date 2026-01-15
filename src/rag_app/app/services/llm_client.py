import time
from collections.abc import Iterator
from litellm import completion, RateLimitError, APIError
from rag_app.app.core.config import Configurations
from rag_app.app.models import Tool, Message, Parameters, MessageDocuments
from rag_app.app.core.errors import LlmCallFailedError
from requests.exceptions import ConnectionError

TRANSIENT_ERRORS = (ConnectionError, TimeoutError)

class LlmClient:
    def __init__(
            self, 
            configs: Configurations):
        self.configs = configs
        self.logger = configs.logger

    def send_request_stream(
            self, 
            messages: list[MessageDocuments],
            tools: list[Tool] | None = None
        ) -> Iterator[dict]:

        start = time.time()
        self.logger.info(f"Sending streaming request to {self.configs.model}...")
        messages = [obj.message for obj in messages]

        params = Parameters(
            model=self.configs.model,
            messages=messages,
            tools=tools if tools is not None else None,
            stream=True,
        )

        try:
            stream = completion(**params.model_dump(exclude_none=True))

            for chunk in stream:
                yield chunk

            self.logger.info(
                f"Streaming completed in {time.time() - start:.3f}s"
            )

        except Exception as e:
            self.logger.error(f"Streaming LLM error: {e}")
            raise LlmCallFailedError("Streaming LLM error") from e


    def send_request(
            self, 
            messages: list[MessageDocuments],
            tools: list[Tool] | None = None
        ) -> Message:

        start = time.time()
        self.logger.info(f"Sending request to {self.configs.model}...")

        messages = [obj.message for obj in messages]
        max_retries = 5
        backoff = 2

        for attempt in range(1, max_retries+1):
            try:
                params = Parameters(
                        model=self.configs.model, 
                        messages=messages,
                        tools=tools if tools is not None else None,
                        )
                response = completion(**params.model_dump(exclude_none=True))
                self.logger.info(f"Successfully queried {self.configs.model}.")
                self.logger.info(f"RESPONSE TIME: {time.time() - start:.3f}s")
                return response
            
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