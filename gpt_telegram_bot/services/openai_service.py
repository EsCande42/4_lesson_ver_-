import openai
import asyncio
from typing import AsyncGenerator, Dict, Any
from config.settings import get_settings

class OpenAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url
        )
    
    async def stream_chat_completion(
        self, 
        messages: list, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Потоковая генерация ответа от OpenAI"""
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Ошибка при генерации ответа: {str(e)}"
    
    async def generate_text(
        self, 
        messages: list, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Обычная генерация текста (не потоковая)"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при генерации ответа: {str(e)}" 