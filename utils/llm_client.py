import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Gemini'ning OpenAI bilan mos endpointi — shu tufayli mavjud kod o'zgarmaydi
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# gemini-flash-latest "thinking" tokenlarini yeydi — "low" bilan minimallashtiramiz
GEMINI_REASONING_EFFORT = os.getenv("GEMINI_REASONING_EFFORT", "low")


class LLMClient:
    """
    LLM klienti: avval Gemini'ga uradi, xato bo'lsa avtomatik OpenAI GPT'ga o'tadi.

    AsyncOpenAI bilan bir xil interfeys beradi: `client.chat.completions.create(...)`.
    Shu tufayli generatorlardagi mavjud kod o'zgarmaydi — faqat klient almashadi.

    Chaqiruvdagi `model=...` e'tiborga olinmaydi; har bir provayder uchun
    o'zining modeli ishlatiladi (Gemini uchun gemini_model, GPT uchun openai_model).
    """

    def __init__(
        self,
        api_key: str = None,
        gemini_key: str = None,
        gemini_model: str = None,
        openai_model: str = None,
    ):
        # api_key = OpenAI kaliti (eski konstruktorlar shuni pozitsion beradi)
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")

        self.gemini_model = gemini_model or DEFAULT_GEMINI_MODEL
        self.openai_model = openai_model or DEFAULT_OPENAI_MODEL

        self._gemini = (
            AsyncOpenAI(api_key=gemini_key, base_url=GEMINI_BASE_URL)
            if gemini_key
            else None
        )
        self._openai = AsyncOpenAI(api_key=openai_key) if openai_key else None

        if not self._gemini:
            logger.warning("⚠️ GEMINI_API_KEY topilmadi — faqat OpenAI ishlaydi")
        if not self._openai:
            logger.warning("⚠️ OPENAI_API_KEY topilmadi — zaxira yo'q")

        self.chat = _Chat(self)


class _Chat:
    def __init__(self, parent: "LLMClient"):
        self.completions = _Completions(parent)


class _Completions:
    def __init__(self, parent: "LLMClient"):
        self._p = parent

    async def create(self, **kwargs):
        # Kirayotgan modelni tashlaymiz — har provayder o'z modelini ishlatadi
        kwargs.pop("model", None)
        p = self._p
        errors = []

        # 1) Asosiy: Gemini
        if p._gemini is not None:
            try:
                gemini_kwargs = dict(kwargs)
                if GEMINI_REASONING_EFFORT:
                    gemini_kwargs["reasoning_effort"] = GEMINI_REASONING_EFFORT
                resp = await p._gemini.chat.completions.create(
                    model=p.gemini_model, **gemini_kwargs
                )
                # Token tugab yarim qolgan javob (masalan buzuq JSON) — zaxiraga o'tamiz
                finish = resp.choices[0].finish_reason if resp.choices else None
                if finish == "length":
                    raise RuntimeError("Gemini javobi token tugab yarim qoldi (finish_reason=length)")
                return resp
            except Exception as e:
                logger.warning(f"Gemini xato ({p.gemini_model}), GPT'ga o'tyapmiz: {e}")
                errors.append(("gemini", e))

        # 2) Zaxira: OpenAI GPT
        if p._openai is not None:
            try:
                return await p._openai.chat.completions.create(
                    model=p.openai_model, **kwargs
                )
            except Exception as e:
                logger.error(f"OpenAI zaxira ham xato ({p.openai_model}): {e}")
                errors.append(("openai", e))

        raise RuntimeError(f"Barcha LLM provayderlar ishlamadi: {errors}")
