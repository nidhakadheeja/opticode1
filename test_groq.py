import os
from dotenv import load_dotenv
from groq import Groq

# 🔥 force load .env
load_dotenv(dotenv_path=".env", override=True)

# 🔍 DEBUG
print("ENV KEY =", os.environ.get("GROQ_API_KEY"))

if not os.environ.get("GROQ_API_KEY"):
    raise RuntimeError("API key NOT loaded")

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Optimize this code: x = 2 + 3"}]
)

print(response.choices[0].message.content)
