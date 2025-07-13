from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.database_service import DatabaseService
from utils.keyboard import SettingsKeyboard
import re

class SettingsHandler:
    def __init__(self):
        self.db_service = DatabaseService()
        self.user_states = {}  # Для отслеживания состояния пользователя
    
    async def handle_settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /settings"""
        user_id = update.effective_user.id
        
        # Получаем или создаем пользователя
        await self.db_service.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Получаем текущие настройки пользователя
        settings = await self.db_service.get_user_settings(user_id)
        
        # Создаем сообщение с текущими настройками
        message = self._format_settings_message(settings)
        
        # Отправляем клавиатуру настроек
        keyboard = SettingsKeyboard.get_main_settings_keyboard()
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def _format_settings_message(self, settings: dict) -> str:
        """Форматирует сообщение с настройками"""
        ai_status = "✅ Включен" if settings.get('use_ai_assistant') else "❌ Выключен"
        
        message = f"""
<b>⚙️ Настройки бота</b>

🤖 <b>Модель:</b> {settings.get('model', 'gpt-3.5-turbo')}
🌡️ <b>Температура:</b> {settings.get('temperature', 0.7):.1f}
📏 <b>Макс. токены:</b> {settings.get('max_tokens', 1000)}
🔗 <b>Base URL:</b> {settings.get('openai_base_url', 'https://api.openai.com/v1')}
🤖 <b>AI-ассистент:</b> {ai_status}

<i>Выберите параметр для изменения:</i>
        """
        return message.strip()
    
    async def handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback-ов от кнопок настроек"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        if data == "settings_model":
            await self._handle_model_selection(query)
        elif data == "settings_temperature":
            await self._handle_temperature_selection(query, user_id)
        elif data == "settings_max_tokens":
            await self._handle_max_tokens_selection(query, user_id)
        elif data == "settings_base_url":
            await self._handle_base_url_selection(query, user_id)
        elif data == "settings_ai_assistant":
            await self._handle_ai_assistant_selection(query, user_id)
        elif data == "settings_close":
            await query.edit_message_text("Настройки закрыты")
        elif data == "settings_back":
            await self._show_main_settings(query, user_id)
        elif data.startswith("model_"):
            await self._handle_model_change(query, user_id, data)
        elif data.startswith("temp_"):
            await self._handle_temperature_change(query, user_id, data)
        elif data.startswith("tokens_"):
            await self._handle_tokens_change(query, user_id, data)
        elif data.startswith("ai_assistant_"):
            await self._handle_ai_assistant_change(query, user_id, data)
    
    async def _show_main_settings(self, query, user_id: int):
        """Показать главное меню настроек"""
        settings = await self.db_service.get_user_settings(user_id)
        message = self._format_settings_message(settings)
        keyboard = SettingsKeyboard.get_main_settings_keyboard()
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def _handle_model_selection(self, query):
        """Обработка выбора модели"""
        keyboard = SettingsKeyboard.get_model_selection_keyboard()
        await query.edit_message_text(
            "🤖 Выберите модель GPT:",
            reply_markup=keyboard
        )
    
    async def _handle_model_change(self, query, user_id: int, data: str):
        """Обработка изменения модели"""
        model = data.replace("model_", "")
        
        if model == "custom":
            # Запрашиваем ввод модели вручную
            self.user_states[user_id] = {"state": "waiting_model_input"}
            await query.edit_message_text(
                "✏️ Введите название модели (например: gpt-4-custom):"
            )
        else:
            # Сохраняем выбранную модель
            await self.db_service.update_user_setting(user_id, "model", model)
            await query.edit_message_text(f"✅ Модель изменена на: {model}")
    
    async def _handle_temperature_selection(self, query, user_id: int):
        """Обработка выбора температуры"""
        settings = await self.db_service.get_user_settings(user_id)
        current_temp = settings.get('temperature', 0.7)
        
        keyboard = SettingsKeyboard.get_temperature_keyboard(current_temp)
        await query.edit_message_text(
            "🌡️ Настройте температуру (креативность):",
            reply_markup=keyboard
        )
    
    async def _handle_temperature_change(self, query, user_id: int, data: str):
        """Обработка изменения температуры"""
        settings = await self.db_service.get_user_settings(user_id)
        current_temp = settings.get('temperature', 0.7)
        
        if data == "temp_decrease":
            new_temp = max(0.0, current_temp - 0.1)
        elif data == "temp_increase":
            new_temp = min(1.0, current_temp + 0.1)
        else:
            return
        
        await self.db_service.update_user_setting(user_id, "temperature", new_temp)
        
        # Обновляем клавиатуру
        keyboard = SettingsKeyboard.get_temperature_keyboard(new_temp)
        await query.edit_message_reply_markup(keyboard)
    
    async def _handle_max_tokens_selection(self, query, user_id: int):
        """Обработка выбора максимальных токенов"""
        keyboard = SettingsKeyboard.get_max_tokens_keyboard()
        await query.edit_message_text(
            "📏 Выберите максимальное количество токенов:",
            reply_markup=keyboard
        )
    
    async def _handle_tokens_change(self, query, user_id: int, data: str):
        """Обработка изменения токенов"""
        if data == "tokens_custom":
            self.user_states[user_id] = {"state": "waiting_tokens_input"}
            await query.edit_message_text(
                "✏️ Введите количество токенов (минимум 150):"
            )
        else:
            tokens = int(data.replace("tokens_", ""))
            await self.db_service.update_user_setting(user_id, "max_tokens", tokens)
            await query.edit_message_text(f"✅ Максимальные токены установлены: {tokens}")
    
    async def _handle_base_url_selection(self, query, user_id: int):
        """Обработка выбора Base URL"""
        self.user_states[user_id] = {"state": "waiting_base_url_input"}
        await query.edit_message_text(
            "🔗 Введите Base URL для OpenAI API (например: https://api.openai.com/v1):"
        )
    
    async def _handle_ai_assistant_selection(self, query, user_id: int):
        """Обработка выбора AI-ассистента"""
        settings = await self.db_service.get_user_settings(user_id)
        is_enabled = settings.get('use_ai_assistant', False)
        
        keyboard = SettingsKeyboard.get_ai_assistant_keyboard(is_enabled)
        await query.edit_message_text(
            "🤖 Настройки AI-ассистента:",
            reply_markup=keyboard
        )
    
    async def _handle_ai_assistant_change(self, query, user_id: int, data: str):
        """Обработка изменения AI-ассистента"""
        if data == "ai_assistant_toggle":
            settings = await self.db_service.get_user_settings(user_id)
            current_status = settings.get('use_ai_assistant', False)
            new_status = not current_status
            
            await self.db_service.update_user_setting(user_id, "use_ai_assistant", new_status)
            
            keyboard = SettingsKeyboard.get_ai_assistant_keyboard(new_status)
            await query.edit_message_reply_markup(keyboard)
            
        elif data == "ai_assistant_url":
            self.user_states[user_id] = {"state": "waiting_ai_url_input"}
            await query.edit_message_text(
                "🔗 Введите URL API эндпоинта AI-ассистента:"
            )
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода для настроек"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]["state"]
        
        if state == "waiting_model_input":
            await self._save_custom_model(update, user_id, text)
        elif state == "waiting_tokens_input":
            await self._save_custom_tokens(update, user_id, text)
        elif state == "waiting_base_url_input":
            await self._save_base_url(update, user_id, text)
        elif state == "waiting_ai_url_input":
            await self._save_ai_assistant_url(update, user_id, text)
        
        # Очищаем состояние
        del self.user_states[user_id]
    
    async def _save_custom_model(self, update, user_id: int, model: str):
        """Сохранение пользовательской модели"""
        await self.db_service.update_user_setting(user_id, "model", model)
        await update.message.reply_text(f"✅ Модель установлена: {model}")
    
    async def _save_custom_tokens(self, update, user_id: int, tokens_text: str):
        """Сохранение пользовательских токенов"""
        try:
            tokens = int(tokens_text)
            if tokens < 150:
                await update.message.reply_text("❌ Минимальное количество токенов: 150")
                return
            
            await self.db_service.update_user_setting(user_id, "max_tokens", tokens)
            await update.message.reply_text(f"✅ Максимальные токены установлены: {tokens}")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число")
    
    async def _save_base_url(self, update, user_id: int, url: str):
        """Сохранение Base URL"""
        # Простая валидация URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Введите корректный URL")
            return
        
        await self.db_service.update_user_setting(user_id, "openai_base_url", url)
        await update.message.reply_text(f"✅ Base URL установлен: {url}")
    
    async def _save_ai_assistant_url(self, update, user_id: int, url: str):
        """Сохранение URL AI-ассистента"""
        # Простая валидация URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Введите корректный URL")
            return
        
        await self.db_service.update_user_setting(user_id, "ai_assistant_url", url)
        await self.db_service.update_user_setting(user_id, "use_ai_assistant", True)
        await update.message.reply_text(f"✅ URL AI-ассистента установлен: {url}") 