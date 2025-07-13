import aiohttp
import json
from typing import Dict, Any

class AIAssistantService:
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Получение HTTP сессии"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_message(self, url: str, message: str, context: Dict[str, Any] = None) -> str:
        """Отправка сообщения AI-ассистенту"""
        session = await self._get_session()
        
        payload = {
            "message": message,
            "context": context or {}
        }
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "Нет ответа от ассистента")
                else:
                    return f"Ошибка API: {response.status}"
        except Exception as e:
            return f"Ошибка соединения: {str(e)}"
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None 