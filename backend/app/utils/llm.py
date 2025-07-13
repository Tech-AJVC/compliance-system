from typing import Any
import os
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_response_from_openai(
    system_prompt: str, user_prompt: str, model_name: str = "gpt-4.1-mini"
) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        logprobs=True,
        seed=0,
    )
    log_probs = 0
    for content in response.choices[0].logprobs.content:
        log_probs += content.logprob
    logger.info(
        f"Linear Probs %: {np.round(np.exp(log_probs / len(response.choices[0].logprobs.content)) * 100, 2)}"
    )
    logger.info(f"System fingerprint: {response.system_fingerprint}")
    logger.info(f"Response: {response.choices[0].message.content}")

    return response.choices[0].message.content
