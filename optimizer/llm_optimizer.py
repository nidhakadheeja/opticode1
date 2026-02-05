import os
import re
from groq import Groq


# ---------- LLM CALL ----------
def optimize_with_groq(code: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
You are a Python code optimizer.

STRICT RULES:
- Return ONLY plain text
- DO NOT use markdown
- DO NOT use ``` or python tags
- Follow the exact format below

FORMAT:

OPTIMIZED_CODE:
<only optimized python code>

EXPLANATION:
- point 1
- point 2

Code to optimize:
{code}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content


# ---------- CLEANING ----------
def _clean_code(code: str) -> str:
    if not code:
        return ""
    # Remove markdown/code fences if LLM sneaks them in
    code = re.sub(r"```[a-zA-Z]*", "", code)
    code = code.replace("```", "")
    return code.strip()


# ---------- PARSER ----------
def parse_llm_response(text: str):
    try:
        if "OPTIMIZED_CODE:" not in text or "EXPLANATION:" not in text:
            raise ValueError("Invalid LLM format")

        optimized_part = text.split("OPTIMIZED_CODE:")[1].split("EXPLANATION:")[0]
        explanation_part = text.split("EXPLANATION:")[1]

        optimized_code = _clean_code(optimized_part)

        explanation_lines = explanation_part.strip().split("\n")
        explanation = [
            line.strip("- ").strip()
            for line in explanation_lines
            if line.strip()
        ]

        return optimized_code, explanation

    except Exception as e:
        return "", [f"LLM parsing failed: {str(e)}"]
