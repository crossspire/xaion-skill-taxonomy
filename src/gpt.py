import pprint
from time import perf_counter
from typing import Any

from loguru import logger
from openai import AzureOpenAI

from src.schema import GPTArgs


class GPT:
    def __init__(self, gpt_args: GPTArgs) -> None:
        """
        Args:
            gpt_args (GPTArgs): gpt arguments
        """
        self.args = gpt_args.model_dump()
        self.api_key = gpt_args.api_key
        self.azure_endpoint = gpt_args.azure_endpoint
        self.api_version = gpt_args.api_version
        self.model = gpt_args.model
        self.temperature = gpt_args.temperature
        self.max_tokens = gpt_args.max_tokens
        self.timeout = gpt_args.timeout
        self.verbose = gpt_args.verbose

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint,
        )

    def __call__(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[str, dict[str, Any], str]:
        """Request to gpt

        Args:
            messages: Request messages to gpt
                e.g. [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": ask1},
                        {"role": "assistant", "content": good_answer1},
                        {"role": "user", "content": ask2},
                        {"role": "assistant", "content": good_answer2}
                    ]

        Returns:
            gpt_response: GPT response
            log_info: Log information
            error: Error message
        """
        gpt_response: str = ""
        error: str = ""

        used_tokens = None
        start_time = perf_counter()
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
            used_tokens = completion.usage

            if hasattr(completion.choices[0].message, "content"):
                gpt_response = str(completion.choices[0].message.content)
            else:
                finish_reason = completion.choices[0].finish_reason
                error = f"gpt cannot respond because of {finish_reason}"

        except Exception as e:
            error = str(e)

        end_time = perf_counter()

        messages_for_logging = [
            {message["role"]: message["content"].replace("%", "%%")}
            for message in messages
        ]
        log_info = {
            "gpt_args": self.args,
            "gpt_request": messages_for_logging,
            "gpt_response": str(gpt_response).replace("%", "%%"),
            "gpt_used_tokens": used_tokens,
            "gpt_elapsed_time": float(f"{end_time - start_time:.2f}"),
        }

        try:
            if self.verbose:
                logger.info(f"gpt:\n{pprint.pformat(log_info, indent=4)}")
        except TypeError as e:
            logger.info(f"gpt error: {e}")
        return gpt_response, log_info, error
