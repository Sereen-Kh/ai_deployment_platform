"""LLM Service for interacting with various language models."""

import asyncio
import random
import time
from typing import Any, AsyncGenerator, Optional

import structlog

from core.config import settings
from core.redis import cache

logger = structlog.get_logger()

# Lazy imports for optional providers
try:
    import google.genai
    from google.genai import Client as GeminiClient
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    GeminiClient = None

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AsyncAnthropic = None


# =============================================================================
# MOCK RESPONSES (for testing without API keys)
# =============================================================================

MOCK_RESPONSES = [
    "Based on my analysis, I can provide you with a comprehensive answer to your question. The key points to consider are: first, understanding the context is essential; second, we should evaluate the available options; and third, implementing a solution requires careful planning.",
    "That's an interesting question! Let me break it down for you. There are several factors at play here, and I'll walk you through each one to give you a complete picture.",
    "I'd be happy to help with that. Here's what I found: the solution involves a multi-step approach that addresses both the immediate concerns and long-term considerations.",
    "Great question! The answer depends on a few variables, but generally speaking, the best approach would be to start with the fundamentals and then build upon them systematically.",
    "Let me analyze this for you. From what I can see, there are three main aspects to consider. I'll explain each one and then provide my recommendation.",
]


class LLMService:
    """Service for LLM interactions with multiple providers (Gemini, OpenAI, Anthropic, Mock)."""

    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM clients based on available API keys."""
        # Initialize Gemini (Primary - Free tier)
        if HAS_GEMINI and settings.gemini_api_key:
            self.gemini_client = GeminiClient(api_key=settings.gemini_api_key)
            logger.info("Gemini client initialized",
                        model=settings.gemini_model)

        # Initialize OpenAI (Optional)
        if HAS_OPENAI and settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")

        # Initialize Anthropic (Optional)
        if HAS_ANTHROPIC and settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(
                api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")

        # Log mock provider availability
        logger.info("Mock provider always available for testing")

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

        if provider == "mock":
            result = await self._generate_mock(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model or "mock-model-v1",
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "gemini":
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

    async def _generate_mock(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate mock response for testing without API keys."""
        # Simulate network latency (50-200ms)
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Pick a random mock response
        response_text = random.choice(MOCK_RESPONSES)

        # Add context-aware prefix based on prompt
        if "?" in prompt:
            response_text = f"Regarding your question: {response_text}"
        elif any(word in prompt.lower() for word in ["create", "generate", "write"]):
            response_text = f"Here's what I've created for you: {response_text}"
        elif any(word in prompt.lower() for word in ["explain", "describe", "what is"]):
            response_text = f"Let me explain: {response_text}"

        # Simulate token counts
        prompt_tokens = len(prompt.split()) + \
            (len(system_prompt.split()) if system_prompt else 0)
        completion_tokens = len(response_text.split())

        logger.info("Mock response generated",
                    prompt_length=len(prompt),
                    response_length=len(response_text))

        return {
            "response": response_text,
            "model": model,
            "provider": "mock",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate response using Google Gemini (Free tier available)."""
        if not self.gemini_client:
            raise RuntimeError(
                "Gemini client not initialized. Set GEMINI_API_KEY.")

        # Build contents list
        contents = []
        if system_prompt:
            contents.append(
                {"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [
                            {"text": "Understood. I'll follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Configure generation settings
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        response = self.gemini_client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # Extract text from response
        response_text = response.text

        # Estimate tokens (Gemini provides usage metadata)
        prompt_tokens = getattr(response, 'usage_metadata', {}).get(
            'prompt_token_count', len(prompt.split()) * 1.3)
        completion_tokens = getattr(response, 'usage_metadata', {}).get(
            'candidates_token_count', len(response_text.split()) * 1.3)

        return {
            "response": response_text,
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
