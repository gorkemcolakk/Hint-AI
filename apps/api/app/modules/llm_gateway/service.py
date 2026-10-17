"""LLM Gateway Servisi.

Tüm LLM isteklerinin geçtiği tek merkezdir.
- Girdileri otomatik ve zorunlu olarak PII maskelemesinden geçirir.
- Retry / timeout yönetimini üstlenir (yalnızca timeout, 5xx ve 429 için).
- Token ve maliyet hesaplamasını yapar.
- llm_calls tablosuna ve loglara çocuk metni veya prompt ASLA yazılmaz.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.llm_gateway.mask import mask_pii
from app.modules.llm_gateway.models import LLMCall
from app.modules.llm_gateway.providers import (
    BaseLLMProvider,
    HttpLLMProvider,
    LLMClientError,
    LLMError,
    LLMMessage,
    LLMRateLimitError,
    LLMResponse,
    LLMServerError,
    LLMTimeoutError,
    MockLLMProvider,
)

logger = logging.getLogger("llm_gateway")


@dataclass
class LLMGatewayResult:
    content: str
    provider: str
    model: str
    purpose: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    latency_ms: int
    retry_count: int
    pii_detected_types: list[str]
    call_id: uuid.UUID | None = None


class LLMGatewayService:
    """LLM erişimi için tek yetkili servis katmanı."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._custom_provider = provider

    def _resolve_provider(self) -> tuple[BaseLLMProvider, str, str]:
        """Yapılandırmaya göre sağlayıcı, sağlayıcı adı ve modeli çözer."""
        if self._custom_provider is not None:
            return self._custom_provider, "custom", settings.llm_model

        provider_name = settings.llm_provider.lower().strip()
        model_name = settings.llm_model

        if provider_name == "mock":
            return MockLLMProvider(), "mock", model_name
        elif provider_name in ("http", "gemini", "openai"):
            return (
                HttpLLMProvider(
                    base_url=settings.llm_base_url,
                    api_key=settings.llm_api_key,
                    timeout_seconds=settings.llm_timeout_seconds,
                ),
                provider_name,
                model_name,
            )
        else:
            # Bilinmeyen sağlayıcı durumunda mock'a güvenli düşüş
            return MockLLMProvider(), "mock", model_name

    def calculate_cost(self, model: str, token_in: int, token_out: int) -> Decimal:
        """Modele göre token maliyetini USD olarak hesaplar."""
        pricing_table = settings.llm_pricing
        rates = pricing_table.get(model, pricing_table.get("default", {}))
        input_rate = rates.get("input_per_million", 0.0)
        output_rate = rates.get("output_per_million", 0.0)

        cost = (token_in * input_rate + token_out * output_rate) / 1_000_000.0
        return Decimal(str(cost)).quantize(Decimal("0.000001"))

    async def complete(
        self,
        prompt: str,
        purpose: str,
        system_prompt: str | None = None,
        prompt_version: str = "v1",
        child_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
        model_override: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMGatewayResult:
        """Tek bir prompt için maskeleme, retry, çağrı ve kayıt işlemlerini yürütür."""
        # 1. ZORUNLU PII MASKELEME
        # Metin doğrudan sağlayıcıya gidemez; mask_pii çağrılarak MaskedText elde edilir.
        detected_types: list[str] = []

        messages: list[LLMMessage] = []
        if system_prompt:
            sys_mask = mask_pii(system_prompt)
            for dt in sys_mask.detected_types:
                if dt not in detected_types:
                    detected_types.append(dt)
            messages.append(LLMMessage(role="system", content=sys_mask.masked_text))

        user_mask = mask_pii(prompt)
        for dt in user_mask.detected_types:
            if dt not in detected_types:
                detected_types.append(dt)
        messages.append(LLMMessage(role="user", content=user_mask.masked_text))

        provider, provider_name, default_model = self._resolve_provider()
        model_to_use = model_override or default_model

        max_retries = settings.llm_max_retries
        retry_count = 0
        last_error: Exception | None = None
        call_id = uuid.uuid4()
        start_time = time.monotonic()

        response: LLMResponse | None = None

        # 2. ÇAĞRI VE RETRY DÖNGÜSÜ
        for attempt in range(max_retries + 1):
            try:
                response = await provider.generate(
                    messages=messages,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                break
            except (LLMTimeoutError, LLMServerError, LLMRateLimitError) as exc:
                last_error = exc
                if attempt < max_retries:
                    retry_count += 1
                    logger.warning(
                        "LLM çağrısı başarısız, yeniden deneniyor (deneme %d/%d): tip=%s",
                        retry_count,
                        max_retries,
                        exc.__class__.__name__,
                    )
                    await asyncio.sleep(0.05 * (2**attempt))
                else:
                    break
            except LLMClientError as exc:
                # 4xx hatalarında YENİDEN DENEME YAPILMAZ
                last_error = exc
                logger.error("LLM istemci hatası (retry edilmedi): kod=%d", exc.status_code)
                break
            except Exception as exc:
                last_error = exc
                break

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # 3. DURUM VE MALİYET DEĞERLENDİRMESİ
        status = "success" if response is not None else "error"
        error_code = last_error.__class__.__name__ if last_error else None

        token_in = response.input_tokens if response else 0
        token_out = response.output_tokens if response else 0
        cost_usd = self.calculate_cost(model_to_use, token_in, token_out)

        # 4. GİZLİLİK ODAKLI LOGLAMA (Çocuk metni veya prompt ASLA loglanmaz)
        logger.info(
            "LLM çağrısı tamamlandı: call_id=%s provider=%s model=%s purpose=%s "
            "status=%s latency_ms=%d token_in=%d token_out=%d cost_usd=%s retries=%d",
            call_id,
            provider_name,
            model_to_use,
            purpose,
            status,
            elapsed_ms,
            token_in,
            token_out,
            cost_usd,
            retry_count,
        )

        # 5. DB KAYDI (İsteğe bağlı, çocuk metni tutulmaz)
        if db is not None:
            llm_call = LLMCall(
                id=call_id,
                provider=provider_name,
                model=model_to_use,
                purpose=purpose,
                prompt_version=prompt_version,
                token_in=token_in,
                token_out=token_out,
                cost_usd=cost_usd,
                latency_ms=elapsed_ms,
                status=status,
                error_code=error_code,
                retry_count=retry_count,
                child_id=child_id,
            )
            db.add(llm_call)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception("llm_calls tablosuna kayıt yapılamadı")

        if response is None:
            if isinstance(last_error, LLMError):
                raise last_error
            raise LLMError(f"LLM çağrısı başarısız oldu: {last_error}") from last_error

        return LLMGatewayResult(
            content=response.content,
            provider=provider_name,
            model=model_to_use,
            purpose=purpose,
            input_tokens=token_in,
            output_tokens=token_out,
            cost_usd=cost_usd,
            latency_ms=elapsed_ms,
            retry_count=retry_count,
            pii_detected_types=detected_types,
            call_id=call_id,
        )
