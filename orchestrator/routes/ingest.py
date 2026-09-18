"""POST /ingest-screen endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from orchestrator.models.action import IngestScreenResponse
from orchestrator.models.observation import ObservationRequest
from orchestrator.providers.base import LLMProvider, LLMProviderError
from orchestrator.providers.mock import MockLLMProvider
from orchestrator.services.screen_ingestion import ingest_screen
from orchestrator.services.session import session_store
from orchestrator.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exploration"])


def _get_provider() -> LLMProvider:
    """Return the configured LLM provider instance.

    Supports: 'mock', 'gemini'.
    Config switch: LLM_PROVIDER env var or settings.llm_provider.
    """
    provider_name = settings.llm_provider

    if provider_name == "mock":
        return MockLLMProvider()

    if provider_name == "gemini":
        from orchestrator.providers.gemini import GeminiProvider

        return GeminiProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
        )

    raise HTTPException(
        status_code=500,
        detail=f"Unknown LLM provider: {provider_name}. Available: ['mock', 'gemini']",
    )


@router.post("/ingest-screen", response_model=IngestScreenResponse)
async def handle_ingest_screen(request: ObservationRequest) -> IngestScreenResponse:
    """Accept an Android observation and return screen understanding + next action.

    Shared contract: §4.1 of the execution plan.

    If the primary provider fails, falls back to mock provider.
    """
    session = session_store.get_or_create(request.session_id)
    provider = _get_provider()

    try:
        response = await ingest_screen(request, session, provider)
    except LLMProviderError as exc:
        # Fallback to mock provider if the primary provider fails
        if provider.name != "mock":
            logger.warning(
                "Provider '%s' failed, falling back to mock: %s",
                provider.name, exc,
            )
            mock = MockLLMProvider()
            response = await ingest_screen(request, session, mock)
        else:
            raise HTTPException(status_code=500, detail=str(exc))

    return response
