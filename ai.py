from fastapi import APIRouter, Depends

from app.config import get_settings
from app.schemas import AIHealthResponse, ChatRequest, ChatResponse, LanguageListResponse, SpeechUnavailable
from app.security.rate_limit import rate_limit
from app.services.ai_assistant import LANGUAGES, answer_question, assistant_health, speech_gateway

router = APIRouter(prefix="/api/ai", tags=["AI assistant"])


@router.get("/languages", response_model=LanguageListResponse)
def languages() -> LanguageListResponse:
    return LanguageListResponse(languages=LANGUAGES)


@router.get("/health", response_model=AIHealthResponse)
def health() -> AIHealthResponse:
    return AIHealthResponse(**assistant_health(get_settings()))


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit("ai-chat", limit=20))])
def chat(body: ChatRequest) -> ChatResponse:
    result = answer_question(get_settings(), body.message, body.language)
    return ChatResponse(**result)


@router.post("/speech-to-text", response_model=SpeechUnavailable, status_code=501)
def speech_to_text(language: str = "en") -> SpeechUnavailable:
    code = language if language in {"en", "hi", "bn"} else "en"
    return SpeechUnavailable(**speech_gateway.transcribe(code))


@router.post("/text-to-speech", response_model=SpeechUnavailable, status_code=501)
def text_to_speech(language: str = "en") -> SpeechUnavailable:
    code = language if language in {"en", "hi", "bn"} else "en"
    return SpeechUnavailable(**speech_gateway.synthesize(code))
