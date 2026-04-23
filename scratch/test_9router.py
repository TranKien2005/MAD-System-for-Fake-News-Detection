import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("NINEROUTER_API_KEY")
base_url = "http://localhost:20128/v1"

print(f"Key: {api_key[:5]}...")
print(f"Base: {base_url}")

try:
    import requests
    print("Pinging endpoint...")
    response = requests.get(base_url.replace("/v1", "/"), timeout=5)
    print(f"Status Code: {response.status_code}")
except Exception as e:
    print(f"Ping failed: {e}")

llm = ChatOpenAI(
    model="text-processing",
    api_key=api_key,
    base_url=base_url
)

from prompts.templates import DEFENDER_ROUND1_PROMPT

news_text = "Nghiên cứu mới cho thấy uống nước chanh vào buổi sáng giúp chữa khỏi hoàn toàn bệnh ung thư."
kb_text = "[S1] Nguồn từ blog sức khỏe: Chanh có chứa vitamin C. [S2] Wikipedia: Ung thư là bệnh lý phức tạp."

prompt = DEFENDER_ROUND1_PROMPT.format(
    original_news=news_text,
    knowledge_base_with_scores=kb_text
)

print("--- PROMPT START ---")
print(prompt[:200] + "...")
print("--- PROMPT END ---")

import openai

client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url
)

print("--- RAW OPENAI TEST ---")
try:
    response = client.chat.completions.create(
        model="text-processing",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    print(f"Full response: {response}")
    print(f"Choices: {response.choices}")
    print(f"Content: [{response.choices[0].message.content}]")
except Exception as e:
    print(f"Raw test failed: {e}")
