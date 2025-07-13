# GPT Telegram Bot

Мощный Telegram бот с поддержкой GPT моделей, потоковой генерации, работы в группах и настраиваемых AI-ассистентов.

## 🚀 Возможности

- ✅ Потоковая генерация ответов от OpenAI
- ✅ Работа в группах (с упоминанием бота)
- ✅ Панель настроек с выбором модели, температуры, токенов
- ✅ Поддержка AI-ассистентов через API
- ✅ Сохранение настроек пользователей
- ✅ Интуитивный интерфейс с кнопками

## 📦 Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd gpt_telegram_bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `env_template.txt`:
```bash
cp env_template.txt .env
```

4. Заполните переменные окружения в `.env`:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
DATABASE_URL=sqlite:///bot.db
REDIS_URL=redis://localhost:6379
```

5. Запустите бота:
```bash
python bot.py
```

## 🌐 Деплой на Vercel

### Подготовка

1. Убедитесь, что у вас есть аккаунт на [Vercel](https://vercel.com)
2. Установите Vercel CLI:
```bash
npm i -g vercel
```

### Деплой

1. Войдите в Vercel:
```bash
vercel login
```

2. Деплойте проект:
```bash
vercel
```

3. Настройте переменные окружения в Vercel Dashboard:
   - Перейдите в настройки проекта
   - Добавьте все переменные из `.env` файла

### Настройка Telegram Webhook

После деплоя получите URL вашего приложения (например: `https://your-app.vercel.app`) и настройте webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.vercel.app/api/bot"}'
```

## 🛠 Структура проекта

```
gpt_telegram_bot/
├── api/
│   └── bot.py              # Serverless function для Vercel
├── config/
│   ├── __init__.py
│   └── settings.py         # Конфигурация приложения
├── handlers/
│   ├── __init__.py
│   ├── text_handler.py     # Обработчик текстовых сообщений
│   ├── settings_handler.py # Обработчик настроек
│   └── group_handler.py    # Обработчик групповых сообщений
├── services/
│   ├── __init__.py
│   ├── openai_service.py   # Сервис OpenAI
│   ├── ai_assistant.py     # Сервис AI-ассистента
│   └── database_service.py # Сервис базы данных
├── utils/
│   ├── __init__.py
│   └── keyboard.py         # Клавиатуры
├── bot.py                  # Основной файл бота
├── requirements.txt        # Зависимости
├── vercel.json            # Конфигурация Vercel
├── runtime.txt            # Версия Python
└── README.md              # Документация
```

## 📝 Использование

### Команды бота:
- `/start` - Начать работу с ботом
- `/settings` - Открыть панель настроек
- `/help` - Показать справку

### Настройки:
- **Модель GPT**: Выбор из популярных моделей или ручной ввод
- **Температура**: Настройка креативности (0.0 - 1.0)
- **Макс. токены**: Ограничение длины ответа
- **Base URL**: Настройка API эндпоинта
- **AI-ассистент**: Переключение на внешний AI-сервис

## 🔧 Разработка

### Добавление новых функций:
1. Создайте обработчик в `handlers/`
2. Добавьте сервис в `services/` (если нужно)
3. Зарегистрируйте обработчик в `bot.py`
4. Обновите документацию

### Тестирование:
```bash
python -m pytest tests/
```

## 📄 Лицензия

MIT License

## 🤝 Поддержка

Если у вас есть вопросы или предложения, создайте Issue в репозитории. 