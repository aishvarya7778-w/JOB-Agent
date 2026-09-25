import os
import json
import time
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def get_api_config():
    """
    Detects and returns API configuration for Grok (xAI) or Groq.
    Supports:
    1. xAI Grok: GROK_API_KEY or XAI_API_KEY (https://api.x.ai/v1)
    2. Groq Cloud: GROQ_API_KEY (https://api.groq.com/openai/v1)
    """
    grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if grok_key and not grok_key.startswith("gsk_"):
        return {
            "provider": "xAI (Grok)",
            "api_key": grok_key,
            "endpoint": "https://api.x.ai/v1/chat/completions",
            "default_model": os.getenv("GROK_MODEL", "grok-2-latest")
        }
    elif groq_key:
        return {
            "provider": "Groq",
            "api_key": groq_key,
            "endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "default_model": os.getenv("GROK_MODEL", "qwen/qwen3.8-27b")
        }
    elif grok_key:
        return {
            "provider": "xAI/Groq",
            "api_key": grok_key,
            "endpoint": "https://api.x.ai/v1/chat/completions",
            "default_model": "grok-2-latest"
        }
    else:
        raise ValueError(
            "No API key found! Please set GROK_API_KEY (or XAI_API_KEY) for xAI, "
            "or GROQ_API_KEY in your .env file or environment variables."
        )

def call_grok(messages, model=None, temperature=0.2, max_tokens=1000, max_retries=5):
    """
    Sends an API call to Grok / LLM with automatic retry on rate limits (429).
    
    :param messages: List of dicts with 'role' ('system', 'user', 'assistant') and 'content'
    :param model: Optional model override
    :param temperature: Sampling temperature (0.0 to 1.0)
    :param max_tokens: Maximum tokens in completion
    :param max_retries: Number of retries for rate limits
    :return: Generated text response
    """
    config = get_api_config()
    model = model or config["default_model"]
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(config["endpoint"], headers=headers, json=payload, timeout=60)
            
            # Handle rate limiting (429) with smart backoff
            if response.status_code == 429:
                err_text = response.text
                wait_time = 6.0
                match = re.search(r'try again in (\d+(?:\.\d+)?)s', err_text, re.IGNORECASE)
                if match:
                    wait_time = float(match.group(1)) + 1.0
                else:
                    wait_time = 2.0 ** attempt + 3.0
                    
                print(f"    [Rate limit 429] Waiting {wait_time:.1f}s before retry (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                continue
                
            if response.status_code != 200:
                raise RuntimeError(
                    f"API Error ({config['provider']}) [{response.status_code}]: {response.text}"
                )
                
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Network error calling {config['provider']} API: {e}")
            print(f"    [Network retry] Connection error ({e}). Waiting 5s before retry (attempt {attempt + 1}/{max_retries})...")
            time.sleep(5)
            
    raise RuntimeError(f"Rate limit exceeded after {max_retries} retries.")

if __name__ == "__main__":
    print("Testing API connection...")
    try:
        config = get_api_config()
        print(f"Using Provider: {config['provider']}, Model: {config['default_model']}")
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Reply with 'Grok API connection successful!'."}
        ]
        reply = call_grok(test_messages)
        print("Response:", reply)
    except Exception as err:
        print("Error:", err)
