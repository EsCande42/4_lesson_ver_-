import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from config.settings import get_settings

class DatabaseService:
    def __init__(self):
        self.settings = get_settings()
        self.db_path = self.settings.database_url.replace("sqlite:///", "")
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создание таблицы настроек пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                model TEXT DEFAULT 'gpt-3.5-turbo',
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 1000,
                openai_base_url TEXT DEFAULT 'https://api.openai.com/v1',
                use_ai_assistant BOOLEAN DEFAULT 0,
                ai_assistant_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Создание таблицы сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def get_or_create_user(self, user_id: int, username: str = None, 
                                first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Получение или создание пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            
            # Создаем настройки по умолчанию
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            
            # Получаем созданного пользователя
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
        
        conn.close()
        
        return {
            'id': user[0],
            'user_id': user[1],
            'username': user[2],
            'first_name': user[3],
            'last_name': user[4],
            'created_at': user[5]
        }
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получение настроек пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        
        settings = cursor.fetchone()
        conn.close()
        
        if settings is None:
            # Создаем настройки по умолчанию
            await self.get_or_create_user(user_id)
            return await self.get_user_settings(user_id)
        
        return {
            'id': settings[0],
            'user_id': settings[1],
            'model': settings[2],
            'temperature': settings[3],
            'max_tokens': settings[4],
            'openai_base_url': settings[5],
            'use_ai_assistant': bool(settings[6]),
            'ai_assistant_url': settings[7],
            'created_at': settings[8],
            'updated_at': settings[9]
        }
    
    async def update_user_setting(self, user_id: int, setting_name: str, value: Any):
        """Обновление настройки пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, что настройки существуют
        cursor.execute('SELECT id FROM user_settings WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            await self.get_or_create_user(user_id)
        
        # Обновляем настройку
        cursor.execute(f'''
            UPDATE user_settings 
            SET {setting_name} = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (value, user_id))
        
        conn.commit()
        conn.close()
    
    async def save_message(self, user_id: int, chat_id: int, role: str, content: str):
        """Сохранение сообщения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (user_id, chat_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (user_id, chat_id, role, content))
        
        conn.commit()
        conn.close()
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Получение истории диалога"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content FROM messages 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit * 2))  # Получаем больше сообщений для правильного порядка
        
        messages = cursor.fetchall()
        conn.close()
        
        # Преобразуем в формат для OpenAI API
        conversation = []
        for role, content in reversed(messages):  # Разворачиваем порядок
            conversation.append({
                'role': role,
                'content': content
            })
        
        return conversation[-limit:]  # Возвращаем последние limit сообщений 