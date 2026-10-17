"""LLM Gateway Entegrasyon ve Birim Testleri.

Sağlayıcı soyutlaması, retry/timeout, maliyet hesaplama, DB kaydı ve
maskelemenin zorunlu olduğunu doğrular.
"""

from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.auth_consent.models import ChildProfile, Consent, User
from app.modules.llm_gateway.mask import MaskedText
from app.modules.llm_gateway.models import LLMCall
from app.modules.llm_gateway.providers import (
    ConsentRequiredError,
    DailyLimitExceededError,
    HttpLLMProvider,
    LLMClientError,
    LLMMessage,
    LLMRateLimitError,
    LLMServerError,
    LLMTimeoutError,
    MockLLMProvider,
)
from app.modules.llm_gateway.service import LLMGatewayService
from evals.run_pii_eval import run_pii_eval


def test_provider_rejects_unmasked_content() -> None:
    """Sağlayıcıya maskelenmemiş ham metin doğrudan verilemez."""
    # 1. LLMMessage'a str verilmesi engellenir
    with pytest.raises(TypeError, match="MaskedText tipinde olmak zorundadır"):
        LLMMessage(role="user", content="ham metin")  # type: ignore[arg-type]

    # 2. MaskedText ile oluşturulan mesaj kabul edilir
    safe_text = MaskedText("Bu güvenli ve maskeli bir metindir.")
    msg = LLMMessage(role="user", content=safe_text)
    assert msg.content == safe_text

    # 3. Provider generate çağrısında kontrol
    mock = MockLLMProvider()
    with pytest.raises(TypeError, match="MaskedText zorunludur"):
        # Sahte bir nesne ile atlatılmaya çalışılsa bile
        class FakeMsg:
            role = "user"
            content = "maskelenmemis"

        import asyncio
        import typing

        fake_list = typing.cast(list[LLMMessage], [FakeMsg()])
        asyncio.run(mock.generate(fake_list, model="test"))


@pytest.mark.asyncio
async def test_service_automatically_masks_pii() -> None:
    """Service katmanı girdi metnini otomatik maskeleyip sağlayıcıya iletir."""
    mock_provider = MockLLMProvider()
    service = LLMGatewayService(provider=mock_provider)

    raw_input = (
        "Merhaba, benim adım Ahmet. Telefonum 0532 111 22 33. "
        "Bu kesir sorusunda payda eşitlemeyi anlamadım."
    )

    result = await service.complete(
        prompt=raw_input,
        purpose="hint",
        prompt_version="hint_v1",
    )

    # Provider'a giden mesajı kontrol et
    sent_messages = mock_provider.calls[0]
    sent_content = str(sent_messages[0].content)

    assert "Ahmet" not in sent_content
    assert "0532 111 22 33" not in sent_content
    assert "[ISIM]" in sent_content
    assert "[TELEFON]" in sent_content
    assert "Bu kesir sorusunda payda eşitlemeyi anlamadım." in sent_content

    assert "ISIM" in result.pii_detected_types
    assert "TELEFON" in result.pii_detected_types


@pytest.mark.asyncio
async def test_cost_calculation() -> None:
    """Token sayılarına ve model fiyat tablosuna göre maliyet doğru hesaplanır."""
    service = LLMGatewayService()

    # gemini-2.5-flash: 0.075 input / 1M, 0.30 output / 1M
    cost = service.calculate_cost("gemini-2.5-flash", token_in=100_000, token_out=100_000)
    # (100_000 * 0.075 + 100_000 * 0.30) / 1_000_000 = (7500 + 30000) / 1M = 0.037500 USD
    assert cost == Decimal("0.037500")

    # mock sağlayıcı için 0.0 USD
    mock_cost = service.calculate_cost("mock", token_in=5000, token_out=2000)
    assert mock_cost == Decimal("0.000000")


@pytest.mark.asyncio
async def test_retry_on_timeout_and_server_errors() -> None:
    """Timeout veya 5xx hatasında en fazla max_retries kadar yeniden dener."""
    # İlk çağrıda hata veren, ikinci çağrıda başarı dönen bir sağlayıcı
    class FlakyProvider(MockLLMProvider):
        def __init__(self) -> None:
            super().__init__()
            self.attempts = 0

        async def generate(self, messages, model, temperature=0.7, max_tokens=1000):  # type: ignore[no-untyped-def]
            self._validate_messages(messages)
            self.attempts += 1
            if self.attempts == 1:
                raise LLMTimeoutError("Geçici zaman aşımı")
            return await super().generate(messages, model, temperature, max_tokens)

    flaky = FlakyProvider()
    service = LLMGatewayService(provider=flaky)

    result = await service.complete(prompt="Soru metni", purpose="hint")
    assert result.retry_count == 1
    assert flaky.attempts == 2
    assert result.content == "Bu bir test ipucudur."


@pytest.mark.asyncio
async def test_no_retry_on_client_error() -> None:
    """4xx istemci hatalarında (429 hariç) yeniden deneme yapılmaz."""
    mock = MockLLMProvider(exception_to_raise=LLMClientError("Bad Request", status_code=400))
    service = LLMGatewayService(provider=mock)

    with pytest.raises(LLMClientError):
        await service.complete(prompt="Soru", purpose="hint")

    # Sadece 1 kez çağrıldı, retry yapılmadı
    assert mock.call_count == 1


@pytest.mark.asyncio
async def test_db_persistence_llm_calls_privacy(db_session: AsyncSession) -> None:
    """llm_calls tablosuna kayıt yapılır; çocuk metni veya prompt tutulmaz."""
    # Veli ve çocuk profili oluştur
    guardian = User(
        email="veli_gateway@example.com",
        role="guardian",
        full_name="Gateway Veli",
    )
    db_session.add(guardian)
    await db_session.flush()

    child = ChildProfile(
        guardian_id=guardian.id,
        nickname="Can",
        birth_year=2015,
        grade=4,
        age_band="7-10",
    )
    db_session.add(child)
    await db_session.flush()

    db_session.add(
        Consent(
            child_id=child.id,
            guardian_id=guardian.id,
            purpose="llm_processing",
            policy_version="v0-draft",
            granted=True,
        )
    )
    await db_session.flush()

    mock = MockLLMProvider(input_tokens=120, output_tokens=80)
    service = LLMGatewayService(provider=mock)

    raw_child_prompt = "Benim adım Can, 12 ile 15'in EKOK'u nedir?"
    result = await service.complete(
        prompt=raw_child_prompt,
        purpose="solve",
        prompt_version="solve_v2",
        child_id=child.id,
        db=db_session,
    )

    assert result.call_id is not None

    # DB kaydını sorgula
    stmt = select(LLMCall).where(LLMCall.id == result.call_id)
    record = (await db_session.execute(stmt)).scalar_one_or_none()

    assert record is not None
    assert record.purpose == "solve"
    assert record.prompt_version == "solve_v2"
    assert record.token_in == 120
    assert record.token_out == 80
    assert record.status == "success"
    assert record.child_id == child.id
    assert record.retry_count == 0

    # Model alanlarını doğrula: Prompt veya yanıt içeriği tutan hiçbir sütun olmamalı
    column_names = {col.name for col in LLMCall.__table__.columns}
    assert "prompt" not in column_names
    assert "content" not in column_names
    assert "raw_input" not in column_names
    assert "response" not in column_names
    assert "raw_response" not in column_names


@pytest.mark.asyncio
async def test_http_llm_provider_success() -> None:
    """HttpLLMProvider OpenAI formatındaki yanıtı düzgün ayrıştırır."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/openai/chat/completions"
        assert request.headers.get("Authorization") == "Bearer test-key"
        import json
        body = json.loads(request.content)
        assert body["model"] == "gemini-2.5-flash"
        assert body["messages"][0]["role"] == "user"

        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "İpucu yanıtı"}}],
                "usage": {"prompt_tokens": 40, "completion_tokens": 20},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = HttpLLMProvider(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key="test-key",
            client=client,
        )
        msg = LLMMessage(role="user", content=MaskedText("Soru metni"))
        resp = await provider.generate([msg], model="gemini-2.5-flash")

        assert resp.content == "İpucu yanıtı"
        assert resp.input_tokens == 40
        assert resp.output_tokens == 20


@pytest.mark.asyncio
async def test_http_llm_provider_error_mapping() -> None:
    """HTTP durum kodlarının doğru LLM istisnalarına dönüştüğünü doğrular."""
    # 429 Testi
    t_429 = httpx.MockTransport(lambda r: httpx.Response(429, text="Rate limit"))
    async with httpx.AsyncClient(transport=t_429) as client:
        p_429 = HttpLLMProvider(base_url="http://test", api_key="", client=client)
        with pytest.raises(LLMRateLimitError):
            await p_429.generate([LLMMessage(role="user", content=MaskedText("a"))], model="m")

    # 500 Testi
    t_500 = httpx.MockTransport(lambda r: httpx.Response(500, text="Internal Server Error"))
    async with httpx.AsyncClient(transport=t_500) as client:
        p_500 = HttpLLMProvider(base_url="http://test", api_key="", client=client)
        with pytest.raises(LLMServerError):
            await p_500.generate([LLMMessage(role="user", content=MaskedText("a"))], model="m")

    # 400 Testi
    t_400 = httpx.MockTransport(lambda r: httpx.Response(400, text="Bad Request"))
    async with httpx.AsyncClient(transport=t_400) as client:
        p_400 = HttpLLMProvider(base_url="http://test", api_key="", client=client)
        with pytest.raises(LLMClientError) as exc_info:
            await p_400.generate([LLMMessage(role="user", content=MaskedText("a"))], model="m")
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_provider_not_called_when_ai_consent_missing(db_session: AsyncSession) -> None:
    """Çocuğun ai_processing rızası yoksa sağlayıcı çağrılmaz ve hata fırlatılır."""
    guardian = User(email="veli_noconsent@example.com", role="guardian")
    db_session.add(guardian)
    await db_session.flush()

    child = ChildProfile(
        guardian_id=guardian.id,
        nickname="Elif",
        birth_year=2016,
        grade=3,
        age_band="7-10",
    )
    db_session.add(child)
    await db_session.flush()

    # Yalnızca service rızası var (ai_processing / llm_processing YOK)
    db_session.add(
        Consent(
            child_id=child.id,
            guardian_id=guardian.id,
            purpose="service",
            policy_version="v0-draft",
            granted=True,
        )
    )
    await db_session.commit()

    mock = MockLLMProvider()
    service = LLMGatewayService(provider=mock)

    with pytest.raises(ConsentRequiredError, match="ai_processing"):
        await service.complete(
            prompt="7 ile 8'i çarpar mısın?",
            purpose="hint",
            child_id=child.id,
            db=db_session,
        )

    # Sağlayıcı çağrılmamış olmalı!
    assert mock.call_count == 0


@pytest.mark.asyncio
async def test_provider_called_when_ai_consent_granted(db_session: AsyncSession) -> None:
    """Çocuğun aktif ai_processing / llm_processing rızası varsa sağlayıcı çağrılır."""
    guardian = User(email="veli_withconsent@example.com", role="guardian")
    db_session.add(guardian)
    await db_session.flush()

    child = ChildProfile(
        guardian_id=guardian.id,
        nickname="Mert",
        birth_year=2015,
        grade=4,
        age_band="7-10",
    )
    db_session.add(child)
    await db_session.flush()

    db_session.add(
        Consent(
            child_id=child.id,
            guardian_id=guardian.id,
            purpose="llm_processing",
            policy_version="v0-draft",
            granted=True,
        )
    )
    await db_session.commit()

    mock = MockLLMProvider(canned_response="Aferin, ipucu!")
    service = LLMGatewayService(provider=mock)

    result = await service.complete(
        prompt="Soru",
        purpose="hint",
        child_id=child.id,
        db=db_session,
    )

    assert mock.call_count == 1
    assert result.content == "Aferin, ipucu!"


@pytest.mark.asyncio
async def test_provider_not_called_when_daily_limit_exceeded(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Günlük limit aşıldığında sağlayıcı ASLA çağrılmaz ve DailyLimitExceededError fırlatılır."""
    monkeypatch.setattr(settings, "llm_daily_call_limit_per_child", 2)

    guardian = User(email="veli_limit@example.com", role="guardian")
    db_session.add(guardian)
    await db_session.flush()

    child = ChildProfile(
        guardian_id=guardian.id,
        nickname="Bora",
        birth_year=2014,
        grade=5,
        age_band="11-13",
    )
    db_session.add(child)
    await db_session.flush()

    db_session.add(
        Consent(
            child_id=child.id,
            guardian_id=guardian.id,
            purpose="llm_processing",
            policy_version="v0-draft",
            granted=True,
        )
    )
    await db_session.commit()

    mock = MockLLMProvider()
    service = LLMGatewayService(provider=mock)

    # 1. Çağrı (Başarılı)
    await service.complete("Soru 1", purpose="hint", child_id=child.id, db=db_session)
    # 2. Çağrı (Başarılı, limite ulaşıldı)
    await service.complete("Soru 2", purpose="hint", child_id=child.id, db=db_session)
    assert mock.call_count == 2

    # 3. Çağrı (Limit aşıldı, sağlayıcı çağrılmamalı)
    with pytest.raises(DailyLimitExceededError, match="günlük LLM çağrı limiti"):
        await service.complete("Soru 3", purpose="hint", child_id=child.id, db=db_session)

    # Provider çağrı sayısı hâlâ 2 olmalı!
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_pii_eval_runner_zero_leaks() -> None:
    """Eval çalıştırıcısı sahte veri setini test eder ve sızan PII sayısının 0 olduğunu doğrular."""
    report = await run_pii_eval()
    assert report["leaked_pii_count"] == 0
    assert report["leak_rate_percent"] == 0.0
    assert report["passed"] is True
    assert report["total_cases"] >= 4

