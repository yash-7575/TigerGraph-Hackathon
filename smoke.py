"""Verify Savanna connection + NVIDIA NIM endpoint."""

import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

TG_HOST = os.environ["TG_HOST"]
TG_SECRET = os.environ["TG_SECRET"]
TG_GRAPHNAME = os.environ["TG_GRAPHNAME"]
NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")


def check_savanna() -> bool:
    from pyTigerGraph import TigerGraphConnection

    print(f"[savanna] connecting to {TG_HOST} ...")
    try:
        conn = TigerGraphConnection(
            host=TG_HOST,
            graphname=TG_GRAPHNAME,
            gsqlSecret=TG_SECRET,
            restppPort=443,
            gsPort=443,
        )
        token = conn.getToken(TG_SECRET)
        print(f"[savanna] got token: {str(token)[:30]}...")
        version = conn.getVer()
        print(f"[savanna] version: {version}")
        return True
    except Exception as e:
        print(f"[savanna] FAILED: {type(e).__name__}: {e}")
        return False


def check_nvidia_llm() -> bool:
    from openai import OpenAI

    print(f"[nvidia] pinging {NVIDIA_BASE_URL} ...")
    try:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
        r = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL_ORCH", "deepseek-ai/deepseek-v3.1"),
            messages=[{"role": "user", "content": "reply with the single word: pong"}],
            max_tokens=8,
            temperature=0.0,
        )
        print(f"[nvidia] LLM reply: {r.choices[0].message.content!r}")
        return True
    except Exception as e:
        print(f"[nvidia] LLM FAILED: {type(e).__name__}: {e}")
        return False


def check_nvidia_embed() -> bool:
    from openai import OpenAI

    try:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
        r = client.embeddings.create(
            model=os.environ.get("EMBED_MODEL", "nvidia/nv-embedqa-e5-v5"),
            input=["hello world"],
            extra_body={"input_type": "query", "truncate": "END"},
        )
        dim = len(r.data[0].embedding)
        print(f"[nvidia] embedding dim: {dim}")
        return True
    except Exception as e:
        print(f"[nvidia] EMBED FAILED: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    results = {
        "savanna": check_savanna(),
        "nvidia_llm": check_nvidia_llm(),
        "nvidia_embed": check_nvidia_embed(),
    }
    print("\n=== summary ===")
    for k, v in results.items():
        print(f"  {k}: {'OK' if v else 'FAIL'}")
    sys.exit(0 if all(results.values()) else 1)
