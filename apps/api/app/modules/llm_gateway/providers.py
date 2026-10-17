"""LLM Sağlayıcı Soyutlama ve Adaptörleri.

OpenAI uyumlu /v1/chat/completions formatında genel HTTP istemcisi ve
testler için Mock sağlayıcı içerir.
Tüm sağlayıcılar YALNIZCA MaskedText kabul eder.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.modules.llm_gateway.mask import MaskedText


class LLMError(Exception):
    """Tüm LLM sağlayıcı hatalarının tabanı."""

    pass


class LLMTimeoutError(LLMError):
    """Zaman aşımı hatası (yeniden denenebilir)."""

    pass


class LLMRateLimitError(LLMError):
    """429 Hız sınırı hatası (yeniden denenebilir)."""

    pass


class LLMServerError(LLMError):
    """5xx Sunucu hatası (yeniden denenebilir)."""

    pass


class LLMClientError(LLMError):
    """4xx İstemci hatası (yeniden denenemez)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class ConsentRequiredError(LLMError):
    """Çocuğun ai_processing rızası olmadığında fırlatılır."""

    pass


class DailyLimitExceededError(LLMError):
    """Günlük çocuk başına LLM çağrı limiti aşıldığında fırlatılır."""

    pass


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: MaskedText

    def __post_init__(self) -> None:
        if not isinstance(self.content, MaskedText):
            raise TypeError(
                "LLMMessage içeriği MaskedText tipinde olmak zorundadır. "
                "Maskelenmemiş ham metin sağlayıcıya gönderilemez."
            )


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class BaseLLMProvider(ABC):
    """LLM sağlayıcıları için ortak soyut taban sınıf."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Maskelenmiş mesajları modele gönderir ve yanıt döner."""
        pass

    def _validate_messages(self, messages: list[LLMMessage]) -> None:
        """Tüm mesajların MaskedText olduğunu garanti eder."""
        if not messages:
            raise ValueError("Mesaj listesi boş olamaz.")
        for msg in messages:
            if not isinstance(msg.content, MaskedText):
                raise TypeError("Sağlayıcıya maskelenmemiş metin verilemez. MaskedText zorunludur.")


class MockLLMProvider(BaseLLMProvider):
    """Birim ve entegrasyon testleri için Mock sağlayıcı."""

    def __init__(
        self,
        canned_response: str = "Bu bir test ipucudur.",
        input_tokens: int = 50,
        output_tokens: int = 30,
        exception_to_raise: Exception | None = None,
        latency_ms: int = 25,
    ) -> None:
        self.canned_response = canned_response
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.exception_to_raise = exception_to_raise
        self.latency_ms = latency_ms
        self.call_count = 0
        self.calls: list[list[LLMMessage]] = []

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self._validate_messages(messages)
        self.call_count += 1
        self.calls.append(messages)

        if self.exception_to_raise:
            raise self.exception_to_raise

        return LLMResponse(
            content=self.canned_response,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            latency_ms=self.latency_ms,
        )


class HttpLLMProvider(BaseLLMProvider):
    """OpenAI uyumlu /chat/completions HTTP sağlayıcısı (Google Gemini vb.)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        # base_url sonundaki eğik çizgiyi kaldır
        clean_url = base_url.rstrip("/")
        if not clean_url.endswith("/chat/completions"):
            self.endpoint = f"{clean_url}/chat/completions"
        else:
            self.endpoint = clean_url

        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._client = client

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self._validate_messages(messages)

        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": str(m.content)} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.monotonic()

        client_to_use = self._client
        owns_client = False
        if client_to_use is None:
            client_to_use = httpx.AsyncClient(timeout=self.timeout_seconds)
            owns_client = True

        try:
            resp = await client_to_use.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"LLM isteği zaman aşımına uğradı: {exc}") from exc
        except httpx.RequestError as exc:
            raise LLMServerError(f"LLM bağlantı hatası: {exc}") from exc
        finally:
            if owns_client:
                await client_to_use.aclose()

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        if resp.status_code == 429:
            raise LLMRateLimitError(f"LLM hız sınırı aşıldı (429): {resp.text}")
        if resp.status_code >= 500:
            raise LLMServerError(f"LLM sunucu hatası ({resp.status_code}): {resp.text}")
        if 400 <= resp.status_code < 500:
            raise LLMClientError(
                f"LLM istemci hatası ({resp.status_code}): {resp.text}",
                status_code=resp.status_code,
            )

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMServerError(f"LLM yanıt formatı geçersiz: {resp.text}") from exc

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=elapsed_ms,
        )
