import asyncio
import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, CommandHandler
from config.settings import get_settings
from handlers.text_handler import TextHandler
from handlers.settings_handler import SettingsHandler
from handlers.group_handler import GroupHandler

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