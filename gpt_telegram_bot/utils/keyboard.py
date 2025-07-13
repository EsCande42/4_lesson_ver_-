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