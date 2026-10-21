import time
from dataclasses import dataclass

from openai import APIError, AuthenticationError, OpenAI, RateLimitError

from verithra.config import Settings, VerithraError


@dataclass
class Generation:
    text: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    model: str = ""


class LLMClient:
    def __init__(self, settings: Settings, sdk=None):
        self.model = settings.llm_model
        self.sdk = sdk or OpenAI(api_key=settings.require_api_key(), timeout=45, max_retries=2)

    def generate(
        self, instructions: str, user_input: str, schema: dict | None = None
    ) -> Generation:
        options = {}
        if schema:
            options["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "resolution",
                    "strict": True,
                    "schema": schema,
                }
            }
        started = time.perf_counter()
        try:
            response = self.sdk.responses.create(
                model=self.model,
                instructions=instructions,
                input=user_input,
                max_output_tokens=1600,
                store=False,
                **options,
            )
        except AuthenticationError as exc:
            raise VerithraError("OpenAI authentication failed. Check your local API key.") from exc
        except RateLimitError as exc:
            raise VerithraError(
                "OpenAI quota/rate limit reached. Check billing or retry later."
            ) from exc
        except APIError as exc:
            raise VerithraError(
                "OpenAI request failed. Check connectivity and model access."
            ) from exc
        if not response.output_text.strip():
            raise VerithraError("The model returned no usable text. Retry with a shorter question.")
        usage = response.usage
        return Generation(
            text=response.output_text,
            latency_ms=(time.perf_counter() - started) * 1000,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            model=self.model,
        )
