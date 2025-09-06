# app/services/prompt_optimizer.py

import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def optimize_prompt(user_prompt: str, style: str) -> str:
    """
    Optimize a raw prompt with style using OpenAI API.
    Fallback to mock response if no API key available.
    """
    if not user_prompt:
        return "Prompt cannot be empty."

    if not OPENAI_API_KEY:
        # Fallback mock output
        return f"[Optimized Mock] A polished {style} style prompt based on: {user_prompt}"

    try:
        
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Prompt Engineering expert who rewrites prompts for AI video generation."},
                {"role": "user", "content": f"Prompt: {user_prompt}\nStyle: {style}\n\nPlease optimize this prompt for best video generation results."}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        return f"[Fallback due to error] Optimized {style} style prompt: {user_prompt}"
