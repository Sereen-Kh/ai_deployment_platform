from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, AsyncGenerator
import json
import asyncio
import time

from core.database import get_db
from api.dependencies import get_current_user
from api.models.user import User
from services.llm_service import LLMService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/playground", tags=["playground"])


class PlaygroundMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class PlaygroundRequest(BaseModel):
    messages: list[PlaygroundMessage]
    model: str = Field(default="gemini-1.5-flash", description="Model to use")
    provider: str = Field(
        default="gemini", description="Provider: gemini, openai, anthropic")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    stream: bool = Field(default=True)
    system_prompt: Optional[str] = None


class PlaygroundResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[int] = None


@router.post("/chat", response_model=PlaygroundResponse)
async def chat(
    request: PlaygroundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Non-streaming chat endpoint for playground
    """
    try:
        llm_service = LLMService()

        # Convert messages to proper format
        messages = [{"role": msg.role, "content": msg.content}
                    for msg in request.messages]

        # Add system prompt if provided
        if request.system_prompt:
            messages.insert(
                0, {"role": "system", "content": request.system_prompt})

        # Generate response
        import time
        start_time = time.time()

        response = await llm_service.generate(
            messages=messages,
            model=request.model,
            provider=request.provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return PlaygroundResponse(
            content=response,
            model=request.model,
            provider=request.provider,
            latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat
    """
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)

            # Validate request
            request = PlaygroundRequest(**request_data)

            llm_service = LLMService()

            # Convert messages
            messages = [{"role": msg["role"], "content": msg["content"]}
                        for msg in request_data["messages"]]

            if request.system_prompt:
                messages.insert(
                    0, {"role": "system", "content": request.system_prompt})

            # Stream response
            full_response = ""
            import time
            start_time = time.time()

            async for chunk in llm_service.stream(
                messages=messages,
                model=request.model,
                provider=request.provider,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                full_response += chunk

                # Send chunk to client
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                    "done": False
                })

            # Send completion message
            latency_ms = int((time.time() - start_time) * 1000)
            await websocket.send_json({
                "type": "complete",
                "content": full_response,
                "done": True,
                "latency_ms": latency_ms,
                "model": request.model,
                "provider": request.provider
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
        await websocket.close()


@router.get("/models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    """
    Get list of available models
    """
    return {
        "models": [
            {
                "provider": "gemini",
                "models": [
                    {"id": "gemini-1.5-flash",
                        "name": "Gemini 1.5 Flash", "context": 1000000},
                    {"id": "gemini-1.5-pro",
                        "name": "Gemini 1.5 Pro", "context": 2000000},
                    {"id": "gemini-pro", "name": "Gemini Pro", "context": 32000}
                ]
            },
            {
                "provider": "openai",
                "models": [
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": 128000},
                    {"id": "gpt-4", "name": "GPT-4", "context": 8192},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": 16385}
                ]
            },
            {
                "provider": "anthropic",
                "models": [
                    {"id": "claude-3-opus-20240229",
                        "name": "Claude 3 Opus", "context": 200000},
                    {"id": "claude-3-sonnet-20240229",
                        "name": "Claude 3 Sonnet", "context": 200000},
                    {"id": "claude-3-haiku-20240307",
                        "name": "Claude 3 Haiku", "context": 200000}
                ]
            }
        ]
    }


@router.get("/presets")
async def get_prompt_presets(current_user: User = Depends(get_current_user)):
    """
    Get prompt presets/templates
    """
    return {
        "presets": [
            {
                "id": "general",
                "name": "General Assistant",
                "system_prompt": "You are a helpful AI assistant. Provide clear, accurate, and concise responses.",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            {
                "id": "code",
                "name": "Code Assistant",
                "system_prompt": "You are an expert programmer. Write clean, efficient, and well-documented code. Explain your reasoning.",
                "temperature": 0.3,
                "max_tokens": 4096
            },
            {
                "id": "creative",
                "name": "Creative Writer",
                "system_prompt": "You are a creative writer. Use vivid language, metaphors, and engaging storytelling.",
                "temperature": 1.2,
                "max_tokens": 3000
            },
            {
                "id": "data_analyst",
                "name": "Data Analyst",
                "system_prompt": "You are a data analyst. Provide insights based on data, use statistical reasoning, and explain trends clearly.",
                "temperature": 0.5,
                "max_tokens": 2048
            },
            {
                "id": "teacher",
                "name": "Patient Teacher",
                "system_prompt": "You are a patient teacher. Explain concepts clearly, use examples, and break down complex topics into simple parts.",
                "temperature": 0.6,
                "max_tokens": 2048
            }
        ]
    }
