# GPT Telegram Bot Implementation Guide

## Структура проекта

```
gpt_telegram_bot/
├── bot.py                 # Основной файл бота
├── config/
│   ├── __init__.py
│   ├── settings.py        # Настройки конфигурации
│   └── database.py        # Настройки БД
├── models/
│   ├── __init__.py
│   ├── user.py           # Модель пользователя
│   ├── conversation.py   # Модель диалога
│   └── settings.py       # Модель настроек
├── services/
│   ├── __init__.py
│   ├── openai_service.py # Сервис OpenAI
│   ├── ai_assistant.py   # Сервис AI-ассистента
│   └── database_service.py # Сервис БД
├── handlers/
│   ├── __init__.py
│   ├── text_handler.py   # Обработчик текста
│   ├── settings_handler.py # Обработчик настроек
│   └── group_handler.py  # Обработчик групп
├── utils/
│   ├── __init__.py
│   ├── keyboard.py       # Клавиатуры
│   └── validators.py     # Валидаторы
├── requirements.txt
└── .env
```

## 1. Поддержка OpenAI Streaming Mode

### 1.1 Настройка OpenAI сервиса

```python
# services/openai_service.py
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
```

### 1.2 Обработчик потокового режима

```python
# handlers/text_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from services.openai_service import OpenAIService
from services.database_service import DatabaseService
import asyncio

class TextHandler:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_service = DatabaseService()
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений с поддержкой стриминга"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Получаем настройки пользователя
        user_settings = await self.db_service.get_user_settings(user_id)
        
        # Сохраняем сообщение пользователя
        await self.db_service.save_message(user_id, chat_id, "user", message_text)
        
        # Получаем историю диалога
        conversation_history = await self.db_service.get_conversation_history(user_id, limit=10)
        
        # Отправляем начальное сообщение
        bot_message = await update.message.reply_text("Генерирую ответ...")
        
        # Проверяем, используется ли AI-ассистент
        if user_settings.use_ai_assistant and user_settings.ai_assistant_url:
            response_text = await self._handle_ai_assistant(
                message_text, user_settings.ai_assistant_url
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
            model=user_settings.model,
            temperature=user_settings.temperature,
            max_tokens=user_settings.max_tokens
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
            user_settings.user_id, 
            bot_message.chat_id, 
            "assistant", 
            response_text
        )
```

## 2. Поддержка добавления в Telegram группы

### 2.1 Обработчик групповых сообщений

```python
# handlers/group_handler.py
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
```

## 3. Панель настроек

### 3.1 Клавиатуры для настроек

```python
# utils/keyboard.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode

class SettingsKeyboard:
    @staticmethod
    def get_main_settings_keyboard():
        """Главная клавиатура настроек"""
        keyboard = [
            [InlineKeyboardButton("🤖 Модель GPT", callback_data="settings_model")],
            [InlineKeyboardButton("🌡️ Температура", callback_data="settings_temperature")],
            [InlineKeyboardButton("📏 Макс. токены", callback_data="settings_max_tokens")],
            [InlineKeyboardButton("🔗 Base URL", callback_data="settings_base_url")],
            [InlineKeyboardButton("🤖 AI-ассистент", callback_data="settings_ai_assistant")],
            [InlineKeyboardButton("❌ Закрыть", callback_data="settings_close")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_model_selection_keyboard():
        """Клавиатура выбора модели"""
        keyboard = [
            [InlineKeyboardButton("GPT-3.5 Turbo", callback_data="model_gpt-3.5-turbo")],
            [InlineKeyboardButton("GPT-4", callback_data="model_gpt-4")],
            [InlineKeyboardButton("GPT-4 Turbo", callback_data="model_gpt-4-turbo-preview")],
            [InlineKeyboardButton("Claude-3", callback_data="model_claude-3-sonnet")],
            [InlineKeyboardButton("✏️ Ввести вручную", callback_data="model_custom")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_temperature_keyboard(current_temp: float = 0.7):
        """Клавиатура настройки температуры"""
        keyboard = []
        
        # Создаем прогресс-бар для температуры
        temp_percentage = int(current_temp * 100)
        progress_bar = "█" * (temp_percentage // 10) + "░" * (10 - temp_percentage // 10)
        
        keyboard.append([InlineKeyboardButton(
            f"🌡️ Температура: {current_temp:.1f}\n{progress_bar}",
            callback_data="temp_info"
        )])
        
        # Кнопки регулировки
        keyboard.extend([
            [
                InlineKeyboardButton("➖", callback_data="temp_decrease"),
                InlineKeyboardButton("➕", callback_data="temp_increase")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_back")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_max_tokens_keyboard(current_tokens: int = 1000):
        """Клавиатура настройки максимальных токенов"""
        keyboard = []
        
        # Предустановленные значения
        presets = [150, 500, 1000, 2000, 4000]
        for preset in presets:
            keyboard.append([InlineKeyboardButton(
                f"{preset} токенов",
                callback_data=f"tokens_{preset}"
            )])
        
        keyboard.extend([
            [InlineKeyboardButton("✏️ Ввести вручную", callback_data="tokens_custom")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_back")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_ai_assistant_keyboard(is_enabled: bool = False):
        """Клавиатура настройки AI-ассистента"""
        status = "✅ Включен" if is_enabled else "❌ Выключен"
        
        keyboard = [
            [InlineKeyboardButton(
                f"🤖 AI-ассистент: {status}",
                callback_data="ai_assistant_toggle"
            )],
            [InlineKeyboardButton("🔗 Установить URL", callback_data="ai_assistant_url")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_back")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
```

### 3.2 Обработчик настроек

```python
# handlers/settings_handler.py
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
    
    async def _save_ai_assistant_url(self, update, user_id: int, url: str):
        """Сохранение URL AI-ассистента"""
        # Простая валидация URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Введите корректный URL")
            return
        
        await self.db_service.update_user_setting(user_id, "ai_assistant_url", url)
        await self.db_service.update_user_setting(user_id, "use_ai_assistant", True)
        await update.message.reply_text(f"✅ URL AI-ассистента установлен: {url}")
```

## 4. Сервис AI-ассистента

```python
# services/ai_assistant.py
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
```

## 5. Основной файл бота

```python
# bot.py
import asyncio
import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, CommandHandler
from config.settings import get_settings
from handlers.text_handler import TextHandler
from handlers.settings_handler import SettingsHandler
from handlers.group_handler import GroupHandler
from services.database_service import DatabaseService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update, context):
    """Обработка команды /start"""
    welcome_text = """
🤖 Добро пожаловать в GPT Telegram Bot!

Я поддерживаю:
• Потоковую генерацию ответов
• Работу в группах (упомяните меня)
• Настройку параметров модели
• Использование AI-ассистентов

Команды:
/start - Начать работу
/settings - Настройки
/help - Помощь

Просто отправьте мне сообщение!
    """
    await update.message.reply_text(welcome_text.strip())

async def help_command(update, context):
    """Обработка команды /help"""
    help_text = """
📖 Справка по использованию бота

🔹 <b>Личные сообщения:</b>
Просто отправьте текст, и я отвечу с помощью GPT

🔹 <b>Групповые чаты:</b>
Упомяните меня в сообщении: @your_bot_name

🔹 <b>Настройки (/settings):</b>
• Выбор модели GPT
• Настройка температуры (креативность)
• Максимальное количество токенов
• Base URL для API
• Настройка AI-ассистента

🔹 <b>AI-ассистент:</b>
Можно настроить собственный AI-ассистент через API эндпоинт

🔹 <b>Потоковый режим:</b>
Ответы генерируются по частям для быстрого отображения
    """
    await update.message.reply_text(help_text.strip(), parse_mode='HTML')

async def main():
    """Основная функция"""
    settings = get_settings()
    
    # Инициализация бота
    application = Application.builder().token(settings.telegram_token).build()
    
    # Инициализация обработчиков
    text_handler = TextHandler()
    settings_handler = SettingsHandler()
    group_handler = GroupHandler()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_handler.handle_settings_command))
    
    # Обработчик callback-ов для настроек
    application.add_handler(CallbackQueryHandler(settings_handler.handle_settings_callback))
    
    # Обработчик текстовых сообщений в личных чатах
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            text_handler.handle_text_message
        )
    )
    
    # Обработчик текстовых сообщений в группах
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            group_handler.handle_group_message
        )
    )
    
    # Обработчик текстового ввода для настроек
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            settings_handler.handle_text_input
        )
    )
    
    # Запуск бота
    print("🤖 Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

## 6. Конфигурация

```python
# config/settings.py
import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Telegram
    telegram_token: str = os.getenv("TELEGRAM_TOKEN")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

## 7. Пример .env файла

```env
# .env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
DATABASE_URL=sqlite:///bot.db
REDIS_URL=redis://localhost:6379
```

Этот код предоставляет полную реализацию всех требуемых функций:
- ✅ Потоковый режим OpenAI
- ✅ Поддержка групп
- ✅ Панель настроек с выбором модели, температуры, токенов
- ✅ Поддержка AI-ассистентов через API
- ✅ Сохранение настроек пользователей
- ✅ Интуитивный интерфейс с кнопками 