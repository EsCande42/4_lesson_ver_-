from telegram import Update
from telegram.ext import ContextTypes
from services.openai_service import OpenAIService
from services.database_service import DatabaseService
from services.ai_assistant import AIAssistantService
import asyncio

class TextHandler:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_service = DatabaseService()
        self.ai_assistant_service = AIAssistantService()
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений с поддержкой стриминга"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Получаем или создаем пользователя
        await self.db_service.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Получаем настройки пользователя
        user_settings = await self.db_service.get_user_settings(user_id)
        
        # Сохраняем сообщение пользователя
        await self.db_service.save_message(user_id, chat_id, "user", message_text)
        
        # Получаем историю диалога
        conversation_history = await self.db_service.get_conversation_history(user_id, limit=10)
        
        # Отправляем начальное сообщение
        bot_message = await update.message.reply_text("Генерирую ответ...")
        
        # Проверяем, используется ли AI-ассистент
        if user_settings['use_ai_assistant'] and user_settings['ai_assistant_url']:
            response_text = await self._handle_ai_assistant(
                message_text, user_settings['ai_assistant_url']
            )
            await bot_message.edit_text(response_text)
        else:
            # Используем OpenAI с потоковым режимом
            await self._stream_openai_response(
                bot_message, 
                conversation_history, 
                user_settings
            )
    
    async def _stream_openai_response(
        self, 
        bot_message, 
        conversation_history: list, 
        user_settings: dict
    ):
        """Потоковая генерация ответа от OpenAI"""
        response_text = ""
        
        async for chunk in self.openai_service.stream_chat_completion(
            messages=conversation_history,
            model=user_settings['model'],
            temperature=user_settings['temperature'],
            max_tokens=user_settings['max_tokens']
        ):
            response_text += chunk
            
            # Обновляем сообщение каждые 50 символов для плавности
            if len(response_text) % 50 == 0:
                try:
                    await bot_message.edit_text(response_text)
                except Exception:
                    pass
        
        # Финальное обновление сообщения
        await bot_message.edit_text(response_text)
        
        # Сохраняем ответ бота
        await self.db_service.save_message(
            user_settings['user_id'], 
            bot_message.chat_id, 
            "assistant", 
            response_text
        )
    
    async def _handle_ai_assistant(self, message_text: str, ai_assistant_url: str) -> str:
        """Обработка сообщения через AI-ассистент"""
        try:
            response = await self.ai_assistant_service.send_message(
                url=ai_assistant_url,
                message=message_text
            )
            return response
        except Exception as e:
            return f"Ошибка при обращении к AI-ассистенту: {str(e)}" 