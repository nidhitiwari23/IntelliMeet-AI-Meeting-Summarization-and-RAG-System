"""
llm_client.py
--------------
A single, shared wrapper around the Groq API.

Why Groq?
    - It gives FREE API access (generous free tier) to powerful open models
      such as Llama-3.1-70B and Mixtral, with very fast inference.
    - Sign up at https://console.groq.com -> API Keys -> create a key.
    - No credit card required for the free tier at the time of writing.

Every agent in this project imports `call_llm()` from here instead of
calling the API directly, so the model name / temperature is configured
in exactly one place.
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Free, high quality instruction model available on Groq
MODEL_NAME ="llama-3.3-70b-versatile"


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """
    Sends a system + user prompt to the Groq-hosted LLM and returns plain text.

    Args:
        system_prompt: instructions that define the agent's role/behavior
        user_prompt:   the actual content/question for this call
        temperature:   lower = more deterministic (good for extraction tasks)

    Returns:
        The model's text response (string).
    """
    response = _client.chat.completions.create(
        model=MODEL_NAME,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def call_llm_json(system_prompt: str, user_prompt: str) -> str:
    """
    Same as call_llm but instructs the model to return ONLY valid JSON.
    Used by agents whose output needs to be parsed programmatically
    (action items, task assignment, decisions).
    """
    json_system_prompt = (
        system_prompt
        + "\n\nIMPORTANT: Respond with ONLY valid JSON. "
        + "No markdown code fences, no explanations, no extra text."
    )
    return call_llm(json_system_prompt, user_prompt, temperature=0.1)
