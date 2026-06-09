from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer, SourcePassage
from app.config import get_settings

_INSTRUCTIONS = (Path(__file__).parent / "instructions.md").read_text()


def _search_filings(ctx: RunContext[DocumentAgentDeps], query: str, top_k: int = 10) -> list[SourcePassage]:
    passages = ctx.deps.retriever.retrieve(query, top_n=top_k)
    return [
        SourcePassage(
            chunk_id=str(p.chunk_id),
            content=p.content,
            section=p.section,
            document_id=str(p.document_id),
            ticker=p.ticker,
            company_name=p.company_name,
            filing_type=p.filing_type,
            filing_date=p.filing_date,
            source_url=p.source_url,
        )
        for p in passages
    ]


def _read_chunk(ctx: RunContext[DocumentAgentDeps], chunk_id: str) -> SourcePassage | None:
    passages = ctx.deps.retriever.retrieve(f"chunk:{chunk_id}", top_n=1)
    if not passages:
        return None
    p = passages[0]
    return SourcePassage(
        chunk_id=str(p.chunk_id),
        content=p.content,
        section=p.section,
        document_id=str(p.document_id),
        ticker=p.ticker,
        company_name=p.company_name,
        filing_type=p.filing_type,
        filing_date=p.filing_date,
        source_url=p.source_url,
    )


def _resolve_model() -> Any:
    settings = get_settings()

    match settings.llm_provider:
        # --- Native providers ---
        case "gemini":
            from pydantic_ai.models.google import GoogleModel
            from pydantic_ai.providers.google import GoogleProvider
            return GoogleModel(
                settings.gemini_llm_model,
                provider=GoogleProvider(api_key=settings.gemini_api_key),
            )

        case "anthropic":
            from pydantic_ai.models.anthropic import AnthropicModel
            from pydantic_ai.providers.anthropic import AnthropicProvider
            return AnthropicModel(
                settings.anthropic_llm_model,
                provider=AnthropicProvider(api_key=settings.anthropic_api_key),
            )

        case "groq":
            from pydantic_ai.models.groq import GroqModel
            from pydantic_ai.providers.groq import GroqProvider
            return GroqModel(
                settings.groq_llm_model,
                provider=GroqProvider(api_key=settings.groq_api_key),
            )

        case "mistral":
            from pydantic_ai.models.mistral import MistralModel
            from pydantic_ai.providers.mistral import MistralProvider
            return MistralModel(
                settings.mistral_llm_model,
                provider=MistralProvider(api_key=settings.mistral_api_key),
            )

        case "cohere":
            from pydantic_ai.models.cohere import CohereModel
            from pydantic_ai.providers.cohere import CohereProvider
            return CohereModel(
                settings.cohere_llm_model,
                provider=CohereProvider(api_key=settings.cohere_api_key),
            )

        case "xai":
            from pydantic_ai.models.xai import XaiModel
            from pydantic_ai.providers.xai import XaiProvider
            return XaiModel(
                settings.xai_llm_model,
                provider=XaiProvider(api_key=settings.xai_api_key),
            )

        case "cerebras":
            from pydantic_ai.models.cerebras import CerebrasModel
            from pydantic_ai.providers.cerebras import CerebrasProvider
            return CerebrasModel(
                settings.cerebras_llm_model,
                provider=CerebrasProvider(api_key=settings.cerebras_api_key),
            )

        case "bedrock":
            from pydantic_ai.models.bedrock import BedrockConverseModel
            from pydantic_ai.providers.bedrock import BedrockProvider
            return BedrockConverseModel(
                settings.bedrock_llm_model,
                provider=BedrockProvider(
                    aws_access_key_id=settings.bedrock_aws_access_key_id or None,
                    aws_secret_access_key=settings.bedrock_aws_secret_access_key or None,
                    aws_session_token=settings.bedrock_aws_session_token or None,
                    region_name=settings.bedrock_region_name,
                ),
            )

        # --- OpenAI-compatible providers ---
        case "openrouter":
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.openrouter_llm_model,
                provider=OpenAIProvider(
                    base_url=settings.openrouter_base_url,
                    api_key=settings.openrouter_api_key,
                ),
            )

        case "nvidia":
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.nvidia_llm_model,
                provider=OpenAIProvider(
                    base_url=settings.nvidia_base_url,
                    api_key=settings.nvidia_api_key,
                ),
            )

        case "ollama":
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.ollama_llm_model,
                provider=OpenAIProvider(
                    base_url=settings.ollama_base_url,
                    api_key="ollama",
                ),
            )

        case "lm_studio":
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.lm_studio_llm_model,
                provider=OpenAIProvider(
                    base_url=settings.lm_studio_base_url,
                    api_key="lm-studio",
                ),
            )

        case "huggingface":
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.huggingface_llm_model,
                provider=OpenAIProvider(
                    base_url=settings.huggingface_base_url,
                    api_key=settings.huggingface_api_key,
                ),
            )

        # --- Default: OpenAI ---
        case _:
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider
            return OpenAIModel(
                settings.openai_llm_model,
                provider=OpenAIProvider(api_key=settings.openai_api_key),
            )


def _make_system_prompt(ctx: RunContext[DocumentAgentDeps]) -> str:
    prompt = _INSTRUCTIONS
    if ctx.deps.message_history:
        prompt += "\n\n## Conversation history\n\n" + ctx.deps.message_history
    return prompt


def build_agent() -> Agent[DocumentAgentDeps, GroundedAnswer]:
    agent = Agent[DocumentAgentDeps, GroundedAnswer](
        _resolve_model(),
        output_type=GroundedAnswer,
        system_prompt=_make_system_prompt,
        tool_timeout=120,
    )
    agent.tool(_search_filings)
    agent.tool(_read_chunk)
    return agent
