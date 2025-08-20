import os
import logging
from genai import genai
from genai import APIError, RateLimitError


USE_DUMMY = os.environ.get("USE_DUMMY_LLM", "false").lower() == "true"

client = None
if not USE_DUMMY:
    try:
        client = genai(api_key=os.environ.get("GEN_API_KEY"))
    except Exception as e:
        logging.error(f"Failed to init genai client: {e}")
        USE_DUMMY = True


def ask_llm(prompt: str) -> str:
    if USE_DUMMY:
        # Dummy response when API is not available
        return f"[DUMMY MODE] You asked: '{prompt}'. Since free quota is over, this is a placeholder response."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except RateLimitError:
        return "[ERROR] OpenAI quota exceeded. Enable USE_DUMMY_LLM=true to run in free mode."
    except APIError as e:
        logging.error(f"OpenAI API error: {e}")
        return "[ERROR] LLM API failed."
    except Exception as e:
        logging.error(f"LLM error: {e}")
        return "[ERROR] LLM service unavailable."

