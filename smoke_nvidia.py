"""Quick NVIDIA-only smoke test (skip Savanna)."""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from openai import OpenAI
c = OpenAI(base_url=os.environ["NVIDIA_BASE_URL"], api_key=os.environ["NVIDIA_API_KEY"])

print("[llm]", os.environ["LLM_MODEL_ORCH"])
r = c.chat.completions.create(
    model=os.environ["LLM_MODEL_ORCH"],
    messages=[{"role": "user", "content": "reply with a single word: pong"}],
    max_tokens=8, temperature=0.0,
)
print("  reply:", repr(r.choices[0].message.content))
print("  usage:", r.usage.total_tokens, "tokens")

print("[embed]", os.environ["EMBED_MODEL"])
r = c.embeddings.create(
    model=os.environ["EMBED_MODEL"],
    input=["hello"],
    extra_body={"input_type": "query", "truncate": "END"},
)
print("  dim:", len(r.data[0].embedding))

print("[sub-llm]", os.environ["LLM_MODEL_SUB"])
r = c.chat.completions.create(
    model=os.environ["LLM_MODEL_SUB"],
    messages=[{"role": "user", "content": "reply with a single word: pong"}],
    max_tokens=8, temperature=0.0,
)
print("  reply:", repr(r.choices[0].message.content))
