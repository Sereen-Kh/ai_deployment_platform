"""LLM Service for interacting with various language models."""

import time
from typing import Any, AsyncGenerator, Optional

import structlog
import google.generativeai as genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from core.config import settings
from core.redis import cache

logger = structlog.get_logger()


class LLMService:
    """Service for LLM interactions with multiple providers (Gemini, OpenAI, Anthropic)."""

    def __init__(self):
        self.gemini_model = None
        self.openai_client: Optional[AsyncOpenAI] = None
        self.anthropic_client: Optional[AsyncAnthropic] = None
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM clients based on available API keys."""
        # Initialize Gemini (Primary - Free tier)
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(settings.gemini_model)
            logger.info("Gemini client initialized",
                        model=settings.gemini_model)

        # Initialize OpenAI (Optional)
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Initialize Anthropic (Optional)
        if settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(
                api_key=settings.anthropic_api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        cache_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate a response from an LLM.

        Returns dict with: response, model, tokens, latency_ms
        """
        provider = provider or settings.default_llm_provider

        # Check cache
        if cache_key:
            cached = await cache.get(cache_key)
            if cached:
                logger.info("Cache hit", cache_key=cache_key)
                return {**cached, "cached": True}

        start_time = time.time()

        if provider == "gemini":
            result = await self._generate_gemini(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model or settings.gemini_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "openai":
            result = await self._generate_openai(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model or settings.openai_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "anthropic":
            result = await self._generate_anthropic(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model or settings.anthropic_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        latency_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = latency_ms
        result["cached"] = False

        # Cache result
        if cache_key:
            await cache.set(cache_key, result, ttl=settings.redis_cache_ttl)

        return result

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate response using Google Gemini (Free tier available)."""
        if not self.gemini_model:
            raise RuntimeError(
                "Gemini client not initialized. Set GEMINI_API_KEY.")

        # Combine system prompt with user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Configure generation settings
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self.gemini_model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )

        # Estimate tokens (Gemini doesn't always return exact counts)
        prompt_tokens = len(full_prompt.split()) * 1.3  # rough estimate
        completion_tokens = len(response.text.split()) * 1.3

        return {
            "response": response.text,
            "model": model,
            "provider": "gemini",
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(prompt_tokens + completion_tokens),
        }

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate response using OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "response": response.choices[0].message.content,
            "model": model,
            "provider": "openai",
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate response using Anthropic."""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized")

        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "response": response.content[0].text,
            "model": model,
            "provider": "anthropic",
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from LLM."""
        provider = provider or settings.default_llm_provider

        if provider == "gemini":
            async for chunk in self._stream_gemini(
                prompt, system_prompt, model or settings.gemini_model,
                temperature, max_tokens
            ):
                yield chunk
        elif provider == "openai":
            async for chunk in self._stream_openai(
                prompt, system_prompt, model or settings.openai_model,
                temperature, max_tokens
            ):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self._stream_anthropic(
                prompt, system_prompt, model or settings.anthropic_model,
                temperature, max_tokens
            ):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _stream_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream response from Gemini."""
        if not self.gemini_model:
            raise RuntimeError("Gemini client not initialized")

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self.gemini_model.generate_content(
            full_prompt,
            generation_config=generation_config,
            stream=True,
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def _stream_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic."""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized")

        async with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def create_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> list[float]:
        """Create embedding for text using configured provider."""
        provider = provider or settings.default_llm_provider

        if provider == "gemini":
            return await self._create_embedding_gemini(text, model)
        elif provider == "openai":
            return await self._create_embedding_openai(text, model)
        else:
            # Default to Gemini for embeddings
            return await self._create_embedding_gemini(text, model)

    async def _create_embedding_gemini(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> list[float]:
        """Create embedding using Google Gemini (Free tier)."""
        model = model or settings.gemini_embedding_model

        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document",
        )

        return result['embedding']

    async def _create_embedding_openai(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> list[float]:
        """Create embedding using OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        model = model or settings.openai_embedding_model

        response = await self.openai_client.embeddings.create(
            model=model,
            input=text,
        )

        return response.data[0].embedding

    async def create_embeddings_batch(
        self,
        texts: list[str],
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        provider = provider or settings.default_llm_provider

        if provider == "gemini":
            # Gemini batch embeddings
            model = model or settings.gemini_embedding_model
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model=model,
                    content=text,
                    task_type="retrieval_document",
                )
                embeddings.append(result['embedding'])
            return embeddings
        elif provider == "openai":
            if not self.openai_client:
                raise RuntimeError("OpenAI client not initialized")

            model = model or settings.openai_embedding_model

            response = await self.openai_client.embeddings.create(
                model=model,
                input=texts,
            )

            return [item.embedding for item in response.data]
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Global instance
llm_service = LLMService()
