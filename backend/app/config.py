from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # If CWD doesn't have .env, try the project root
    def __init__(self, **kwargs):
        if not Path(".env").exists():
            root = Path(__file__).resolve().parent.parent.parent
            dotenv = root / ".env"
            if dotenv.exists():
                kwargs.setdefault("_env_file", str(dotenv))
        super().__init__(**kwargs)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    allowed_origins: str = "http://localhost:5173"

    # --- Provider selection ---
    llm_provider: str = "openai"
    # Embedding provider — decoupled from LLM provider.
    # Empty means "use the same as llm_provider".
    # Set to a different value to pair an LLM without embedding APIs
    # (anthropic, groq, xai, cerebras) with any embedding provider.
    embedding_provider: str = ""

    # ========================
    # LLM provider settings
    # ========================

    # -- OpenAI --
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o"

    # -- Gemini --
    gemini_api_key: str = ""
    gemini_llm_model: str = "gemini-2.0-flash"

    # -- Anthropic --
    anthropic_api_key: str = ""
    anthropic_llm_model: str = "claude-sonnet-4-20250514"

    # -- OpenRouter (OpenAI-compatible) --
    openrouter_api_key: str = ""
    openrouter_llm_model: str = "anthropic/claude-sonnet-4-20250514"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # -- NVIDIA (OpenAI-compatible) --
    nvidia_api_key: str = ""
    nvidia_llm_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    # -- Ollama (OpenAI-compatible) --
    ollama_llm_model: str = "llama3.2"
    ollama_api_key: str = "ollama"
    ollama_base_url: str = "http://localhost:11434/v1"

    # -- LM Studio (OpenAI-compatible) --
    lm_studio_llm_model: str = "local-model"
    lm_studio_base_url: str = "http://localhost:1234/v1"

    # -- Hugging Face (OpenAI-compatible) --
    huggingface_api_key: str = ""
    huggingface_llm_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    huggingface_base_url: str = "https://api-inference.huggingface.co/v1"

    # -- Groq (dedicated) --
    groq_api_key: str = ""
    groq_llm_model: str = "llama-3.3-70b-versatile"

    # -- Mistral (dedicated) --
    mistral_api_key: str = ""
    mistral_llm_model: str = "mistral-large-latest"

    # -- Cohere (dedicated) --
    cohere_api_key: str = ""
    cohere_llm_model: str = "command-a-08-2025"

    # -- xAI / Grok (dedicated) --
    xai_api_key: str = ""
    xai_llm_model: str = "grok-4.3"

    # -- Cerebras (dedicated) --
    cerebras_api_key: str = ""
    cerebras_llm_model: str = "llama-3.3-70b"

    # -- AWS Bedrock (dedicated) --
    bedrock_aws_access_key_id: str = ""
    bedrock_aws_secret_access_key: str = ""
    bedrock_aws_session_token: str = ""
    bedrock_region_name: str = "us-east-1"
    bedrock_llm_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # ===========================
    # Embedding provider settings
    # ===========================

    # -- OpenAI embeddings --
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # -- Gemini embeddings --
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = 3072

    # -- Cohere embeddings --
    cohere_embedding_model: str = "embed-english-v3.0"
    cohere_embedding_input_type: str = "search_document"

    # -- VoyageAI embeddings --
    voyageai_api_key: str = ""
    voyageai_embedding_model: str = "voyage-3-lite"

    # -- Sentence-Transformers (local) --
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    sentence_transformer_dimensions: int = 384

    # -- Bedrock embeddings --
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"

    # -- Hugging Face embeddings (OpenAI-compatible) --
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # -- OpenRouter embeddings (OpenAI-compatible) --
    openrouter_embedding_model: str = "openai/text-embedding-3-small"

    # -- NVIDIA embeddings (OpenAI-compatible) --
    nvidia_embedding_model: str = "nvidia/nv-embedqa-e5-v5"

    # -- Ollama embeddings (OpenAI-compatible, local) --
    ollama_embedding_model: str = "nomic-embed-text:v1.5"

    # -- LM Studio embeddings (OpenAI-compatible, local) --
    lm_studio_embedding_model: str = "nomic-embed-text-v1.5"

    # -- Mistral embeddings (native SDK) --
    mistral_embedding_model: str = "mistral-embed"

    # -- Together AI embeddings (OpenAI-compatible) --
    together_api_key: str = ""
    together_base_url: str = "https://api.together.xyz/v1"
    together_embedding_model: str = "togethercomputer/m2-bert-80M-8k-retrieval"

    # -- Fireworks AI embeddings (OpenAI-compatible) --
    fireworks_api_key: str = ""
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    fireworks_embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"

    # -- Perplexity embeddings (OpenAI-compatible endpoint, base64-encoded) --
    perplexity_api_key: str = ""
    perplexity_base_url: str = "https://api.perplexity.ai"
    perplexity_embedding_model: str = "pplx-embed-v1-4b"


@lru_cache
def get_settings() -> Settings:
    return Settings()
