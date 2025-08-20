import os
import logging
from openai import OpenAI, error

USE_DUMMY = os.environ.get("USE_DUMMY_LLM", "false").lower() == "true"

client = None
if not USE_DUMMY:
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except Exception as e:
        logging.error(f"Failed to init OpenAI client: {e}")
        USE_DUMMY = True


def ask_llm(prompt: str) -> str:
    if USE_DUMMY:
        return f"[DUMMY MODE] You asked: '{prompt}'. Since free quota is over, this is a placeholder response."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"]
    except error.RateLimitError:
        return "[ERROR] OpenAI quota exceeded. Enable USE_DUMMY_LLM=true to run in free mode."
    except Exception as e:
        logging.error(f"LLM error: {e}")
        return "[ERROR] LLM service unavailable."
