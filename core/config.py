"""Central configuration loaded from .env."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent.parent

# Force .env to win over inherited shell env (which may have empty keys)
load_dotenv(ROOT / ".env", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # TigerGraph
    tg_host: str
    tg_secret: str
    tg_graphname: str = "OlympicsKG"
    tg_restpp_port: int = 443
    tg_gsql_port: int = 443

    # NVIDIA NIM (OpenAI-compatible)
    nvidia_api_key: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    llm_model_orch: str = "openai/gpt-oss-20b"
    llm_model_sub: str = "openai/gpt-oss-20b"
    embed_model: str = "nvidia/nemotron-3-embed-1b"

    # Budgets
    max_agent_steps: int = 8
    agent_token_cap: int = 30_000
    agent_answer_reserve: int = 5_000
    rag_top_k: int = 8
    rag_top_k_aggregation: int = 16


settings = Settings()  # type: ignore[call-arg]
