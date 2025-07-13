from typing import Any
import os
from openai import OpenAI
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Remove load_dotenv() since we're in Kubernetes environment
# Environment variables are set directly in the pod


def get_response_from_openai(
    system_prompt: str, user_prompt: str, model_name: str = "gpt-4o-mini"
) -> str:
    """
    Get response from OpenAI API
    
    Args:
        system_prompt: System prompt for the API
        user_prompt: User prompt for the API
        model_name: OpenAI model name to use
        
    Returns:
        Response content from OpenAI
        
    Raises:
        ValueError: If OpenAI API key is not configured
        Exception: If OpenAI API call fails
    """
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable.")
    
    logger.info(f"Using OpenAI model: {model_name}")
    
    try:
        client = OpenAI(api_key=api_key)
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
        
        # Calculate and log probabilities
        log_probs = 0
        for content in response.choices[0].logprobs.content:
            log_probs += content.logprob
        logger.info(
            f"Linear Probs %: {np.round(np.exp(log_probs / len(response.choices[0].logprobs.content)) * 100, 2)}"
        )
        logger.info(f"System fingerprint: {response.system_fingerprint}")
        logger.info(f"Response: {response.choices[0].message.content}")

        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        raise Exception(f"OpenAI API call failed: {str(e)}")
