from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import DatabaseService

class GroupHandler:
    def __init__(self):
        self.db_service = DatabaseService()
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений в группах"""
        chat = update.effective_chat
        user = update.effective_user
        message_text = update.message.text
        
        # Проверяем, что это группа
        if chat.type not in ['group', 'supergroup']:
            return
        
        # Проверяем, упоминается ли бот
        bot_username = context.bot.username
        if not self._is_bot_mentioned(message_text, bot_username):
            return
        
        # Извлекаем сообщение без упоминания бота
        clean_message = self._remove_bot_mention(message_text, bot_username)
        
        # Обрабатываем сообщение как обычный текст
        await self._handle_group_text(update, context, clean_message, user.id)
    
    def _is_bot_mentioned(self, message_text: str, bot_username: str) -> bool:
        """Проверяет, упоминается ли бот в сообщении"""
        mentions = [
            f"@{bot_username}",
            f"/start@{bot_username}",
            f"/settings@{bot_username}",
            f"/help@{bot_username}"
        ]
        return any(mention in message_text for mention in mentions)
    
    def _remove_bot_mention(self, message_text: str, bot_username: str) -> str:
        """Удаляет упоминание бота из сообщения"""
        mentions = [
            f"@{bot_username}",
            f"/start@{bot_username}",
            f"/settings@{bot_username}",
            f"/help@{bot_username}"
        ]
        
        for mention in mentions:
            message_text = message_text.replace(mention, "").strip()
        
        return message_text
    
    async def _handle_group_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                message_text: str, user_id: int):
        """Обработка текста в группе"""
        # Используем тот же обработчик, что и для личных сообщений
        from handlers.text_handler import TextHandler
        text_handler = TextHandler()
        
        # Создаем фейковый update для обработки
        fake_update = Update(0)
        fake_update.message = update.message
        fake_update.message.text = message_text
        fake_update.effective_user = update.effective_user
        fake_update.effective_chat = update.effective_chat
        
        await text_handler.handle_text_message(fake_update, context) 