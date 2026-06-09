from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        ...


class OpenAIEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        from openai import OpenAI

        settings = get_settings()
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
            dimensions=settings.openai_embedding_dimensions,
        )
        return response.data[0].embedding


class GeminiEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        from google import genai

        settings = get_settings()
        client = genai.Client(api_key=settings.gemini_api_key)
        result = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
        )
        return list(result.embeddings[0].values)


class CohereEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        import cohere

        settings = get_settings()
        client = cohere.Client(api_key=settings.cohere_api_key)
        response = client.embed(
            texts=[text],
            model=settings.cohere_embedding_model,
            input_type=settings.cohere_embedding_input_type,
        )
        return response.embeddings[0]


class VoyageAIEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        import voyageai

        settings = get_settings()
        client = voyageai.Client(api_key=settings.voyageai_api_key)
        result = client.embed(
            texts=[text],
            model=settings.voyageai_embedding_model,
        )
        return result.embeddings[0]


class SentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        self._model = SentenceTransformer(settings.sentence_transformer_model)

    def generate_embedding(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()


class BedrockEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        import boto3
        import json

        settings = get_settings()
        session = boto3.Session(
            aws_access_key_id=settings.bedrock_aws_access_key_id or None,
            aws_secret_access_key=settings.bedrock_aws_secret_access_key or None,
            aws_session_token=settings.bedrock_aws_session_token or None,
            region_name=settings.bedrock_region_name,
        )
        client = session.client("bedrock-runtime")
        response = client.invoke_model(
            modelId=settings.bedrock_embedding_model,
            body=json.dumps({"inputText": text}),
        )
        body = json.loads(response["body"].read())
        return body["embedding"]


class HuggingFaceEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        from openai import OpenAI

        settings = get_settings()
        client = OpenAI(
            api_key=settings.huggingface_api_key,
            base_url=settings.huggingface_base_url,
        )
        response = client.embeddings.create(
            model=settings.huggingface_embedding_model,
            input=text,
        )
        return response.data[0].embedding


class OpenAICompatibleEmbeddings(EmbeddingProvider):
    def __init__(self, provider: str) -> None:
        self._provider = provider

    def generate_embedding(self, text: str) -> list[float]:
        from openai import OpenAI

        settings = get_settings()
        match self._provider:
            case "openrouter":
                base_url = settings.openrouter_base_url
                api_key = settings.openrouter_api_key
                model = settings.openrouter_embedding_model
            case "nvidia":
                base_url = settings.nvidia_base_url
                api_key = settings.nvidia_api_key
                model = settings.nvidia_embedding_model
            case "ollama":
                base_url = settings.ollama_base_url
                api_key = settings.ollama_api_key
                model = settings.ollama_embedding_model
            case "lm_studio" | "lm-studio":
                base_url = settings.lm_studio_base_url
                api_key = settings.lm_studio_api_key
                model = settings.lm_studio_embedding_model
            case "together":
                base_url = settings.together_base_url
                api_key = settings.together_api_key
                model = settings.together_embedding_model
            case "fireworks":
                base_url = settings.fireworks_base_url
                api_key = settings.fireworks_api_key
                model = settings.fireworks_embedding_model
            case _:
                raise ValueError(f"Unknown OpenAI-compatible provider: {self._provider}")
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.embeddings.create(model=model, input=text)
        return response.data[0].embedding


class MistralEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        from mistralai import Mistral

        settings = get_settings()
        client = Mistral(api_key=settings.mistral_api_key)
        response = client.embeddings.create(
            model=settings.mistral_embedding_model,
            inputs=[text],
        )
        return response.data[0].embedding


class PerplexityEmbeddings(EmbeddingProvider):
    def generate_embedding(self, text: str) -> list[float]:
        import base64
        import struct

        import httpx

        settings = get_settings()
        response = httpx.post(
            f"{settings.perplexity_base_url}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.perplexity_embedding_model,
                "input": text,
                "encoding_format": "base64_int8",
            },
        )
        response.raise_for_status()
        data = response.json()
        encoded = data["data"][0]["embedding"]
        decoded = base64.b64decode(encoded)
        return list(struct.unpack(f"{len(decoded)}b", decoded))


def _resolve_embedding_provider_name() -> str:
    settings = get_settings()
    if settings.embedding_provider:
        return settings.embedding_provider
    return settings.llm_provider


_NO_EMBEDDING_LLM_PROVIDERS = frozenset({
    "anthropic",
    "groq",
    "xai",
    "cerebras",
})


def get_embedding_provider() -> EmbeddingProvider:
    provider = _resolve_embedding_provider_name()

    if provider in _NO_EMBEDDING_LLM_PROVIDERS:
        raise ValueError(
            f"'{provider}' has no embedding API. "
            f"Set EMBEDDING_PROVIDER to a different provider "
            f"(e.g. EMBEDDING_PROVIDER=openai or EMBEDDING_PROVIDER=gemini)."
        )
    match provider:
        case "gemini":
            return GeminiEmbeddings()
        case "cohere":
            return CohereEmbeddings()
        case "voyageai":
            return VoyageAIEmbeddings()
        case "sentence_transformers" | "sentence-transformer":
            return SentenceTransformerEmbeddings()
        case "bedrock":
            return BedrockEmbeddings()
        case "huggingface":
            return HuggingFaceEmbeddings()
        case "openrouter":
            return OpenAICompatibleEmbeddings("openrouter")
        case "nvidia":
            return OpenAICompatibleEmbeddings("nvidia")
        case "ollama":
            return OpenAICompatibleEmbeddings("ollama")
        case "lm_studio" | "lm-studio":
            return OpenAICompatibleEmbeddings("lm_studio")
        case "mistral":
            return MistralEmbeddings()
        case "together" | "together-ai":
            return OpenAICompatibleEmbeddings("together")
        case "fireworks":
            return OpenAICompatibleEmbeddings("fireworks")
        case "perplexity":
            return PerplexityEmbeddings()
        case _:
            return OpenAIEmbeddings()
