"""
MAX Messenger Bot Module for OptFM AI Bot

Этот модуль содержит основной класс для работы с MAX мессенджером.
Переиспользует логику обработки сообщений из Telegram бота.
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import sys
import os

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
from faq.enhanced_faq_manager import EnhancedFAQManager

logger = logging.getLogger(__name__)

class OptFMMaxBot:
    """Основной класс MAX бота для OptFM"""
    
    def __init__(self, api_key: str, base_url: str = "https://max-api.chat/api"):
        """
        Инициализация MAX бота
        
        Args:
            api_key: API ключ для MAX
            base_url: Базовый URL для MAX API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.faq_manager = EnhancedFAQManager()
        self.session = None
        
        logger.info("OptFM MAX Bot initialized")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Получение HTTP сессии с правильными заголовками
        
        Returns:
            aiohttp.ClientSession: Настроенная сессия
        """
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "OptFM-Bot/1.0"
            }
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
        
    async def send_message(self, chat_id: str, text: str, parse_mode: str = None) -> bool:
        """
        Отправка сообщения в MAX
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
            parse_mode: Режим парсинга (если поддерживается)
            
        Returns:
            bool: Успех отправки
        """
        try:
            session = await self._get_session()
            
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Message sent to MAX chat {chat_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send MAX message: {response.status} - {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("Timeout sending message to MAX")
            return False
        except Exception as e:
            logger.error(f"Error sending MAX message: {e}")
            return False
            
    async def handle_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Обработка входящего сообщения от MAX
        
        Args:
            message_data: Данные сообщения в формате MAX webhook
            
        Returns:
            str: Ответ для отправки пользователю или None при ошибке
        """
        try:
            # Извлекаем данные сообщения
            user_message = message_data.get("text", "")
            user_data = message_data.get("from", {})
            user_name = user_data.get("first_name", "Пользователь")
            user_id = user_data.get("id", "unknown")
            chat_data = message_data.get("chat", {})
            chat_id = chat_data.get("id", "")
            
            logger.info(f"Processing MAX message from user {user_id} ({user_name}): {user_message[:50]}...")
            
            # Обрабатываем сообщение
            response = await self._process_user_message(user_message, user_name)
            
            # Отправляем ответ
            if response and chat_id:
                success = await self.send_message(chat_id, response)
                if success:
                    logger.info(f"Response sent to MAX user {user_id}")
                    return response
                else:
                    logger.error(f"Failed to send response to MAX user {user_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling MAX message: {e}")
            return None
            
    async def _process_user_message(self, user_message: str, user_name: str) -> str:
        """
        Обработка сообщения пользователя (аналогично Telegram боту)
        
        Args:
            user_message: Текст сообщения
            user_name: Имя пользователя
            
        Returns:
            str: Ответ для пользователя
        """
        # Проверяем приветствия
        greeting_keywords = [
            'привет', 'здравствуй', 'добрый день', 'добрый вечер', 
            'доброе утро', 'hi', 'hello', 'начать'
        ]
        is_greeting = any(greeting in user_message.lower() for greeting in greeting_keywords)
        
        # Проверяем прощания
        farewell_keywords = [
            'пока', 'до свидания', 'до встречи', 'спасибо', 
            'благодарю', 'bye', 'goodbye', 'thanks'
        ]
        is_farewell = any(farewell in user_message.lower() for farewell in farewell_keywords)
        
        # Проверяем вопросы
        question_keywords = [
            'что', 'как', 'где', 'когда', 'почему', 'зачем', 
            'какие', 'какой', 'сколько', 'есть ли', 'можно ли'
        ]
        is_question = (
            any(question in user_message.lower() for question in question_keywords) 
            or user_message.strip().endswith('?')
        )
        
        if is_greeting:
            return self._get_greeting_response(user_name)
        elif is_farewell:
            return self._get_farewell_response(user_name)
        elif not is_question and len(user_message.split()) < 3:
            return self._get_help_response(user_name)
        else:
            return await self._get_faq_response(user_message)
            
    def _get_greeting_response(self, user_name: str) -> str:
        """Генерация приветственного сообщения"""
        return (
            f"👋 Привет, {user_name}!\n\n"
            "Я бот компании OptFM в MAX мессенджере. "
            "Могу помочь с информацией о наших продуктах и услугах.\n\n"
            "Задайте мне любой вопрос, например:\n"
            "• Какие товары вы продаете?\n"
            "• Как с вами связаться?\n"
            "• Какие условия доставки?\n"
            "• Есть ли у вас гарантия?\n\n"
            "Или напишите 'помощь' для получения дополнительной информации."
        )
        
    def _get_farewell_response(self, user_name: str) -> str:
        """Генерация прощального сообщения"""
        return (
            f"👋 До свидания, {user_name}!\n\n"
            "Спасибо за обращение к OptFM. "
            "Если у вас появятся вопросы, я всегда готов помочь!\n\n"
            "Удачного дня! 😊"
        )
        
    def _get_help_response(self, user_name: str) -> str:
        """Генерация справочного сообщения"""
        return (
            f"🤔 {user_name}, я не совсем понял ваш запрос.\n\n"
            "Задайте мне вопрос о продуктах OptFM, например:\n"
            "• Какие товары вы продаете?\n"
            "• Как с вами связаться?\n"
            "• Какие условия доставки?\n"
            "• Есть ли у вас гарантия?\n\n"
            "Я работаю на основе базы знаний и постараюсь найти нужную информацию."
        )
        
    async def _get_faq_response(self, user_message: str) -> str:
        """
        Поиск ответа в FAQ базе
        
        Args:
            user_message: Сообщение пользователя
            
        Returns:
            str: Ответ из FAQ или сообщение о том, что ответ не найден
        """
        # Поиск ответа в FAQ
        faq_answer = self.faq_manager.search_faq(user_message)
        
        if faq_answer:
            logger.info(f"FAQ answer found: {faq_answer['id']}")
            return (
                f"🤖 {faq_answer['answer']}\n\n"
                "Если у вас есть дополнительные вопросы, не стесняйтесь спрашивать!"
            )
        else:
            logger.info("FAQ answer not found")
            return (
                f"📝 Спасибо за ваш вопрос: \"{user_message}\"\n\n"
                "К сожалению, я не нашел точного ответа в базе знаний. "
                "Для получения подробной информации оставьте заявку, "
                "и наш менеджер свяжется с вами.\n\n"
                "Или попробуйте переформулировать вопрос. Например:\n"
                "• Какие у вас есть продукты?\n"
                "• Как с вами связаться?\n"
                "• Какие цены?\n\n"
                "📞 Контакты для связи:\n"
                "• Телефон: +7 (XXX) XXX-XX-XX\n"
                "• Email: info@optfm.ru"
            )
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Получение информации о боте
        
        Returns:
            dict: Информация о боте или None при ошибке
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/getMe") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Bot info retrieved successfully")
                    return result
                else:
                    logger.error(f"Failed to get bot info: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    async def set_webhook(self, webhook_url: str, secret_token: str = None) -> bool:
        """
        Установка webhook'а для получения сообщений
        
        Args:
            webhook_url: URL для webhook'а
            secret_token: Секретный токен для валидации
            
        Returns:
            bool: Успех установки
        """
        try:
            session = await self._get_session()
            
            payload = {"url": webhook_url}
            if secret_token:
                payload["secret_token"] = secret_token
            
            async with session.post(f"{self.base_url}/setWebhook", json=payload) as response:
                if response.status == 200:
                    logger.info(f"Webhook set successfully: {webhook_url}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to set webhook: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """
        Удаление webhook'а
        
        Returns:
            bool: Успех удаления
        """
        try:
            session = await self._get_session()
            
            async with session.post(f"{self.base_url}/deleteWebhook") as response:
                if response.status == 200:
                    logger.info("Webhook deleted successfully")
                    return True
                else:
                    logger.error(f"Failed to delete webhook: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
                
    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            logger.info("MAX bot session closed")
            
    async def __aenter__(self):
        """Поддержка async context manager"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Поддержка async context manager"""
        await self.close()


# Пример использования
if __name__ == "__main__":
    async def main():
        # Пример инициализации и использования
        api_key = "your_max_api_key_here"
        
        async with OptFMMaxBot(api_key) as bot:
            # Получение информации о боте
            bot_info = await bot.get_me()
            print(f"Bot info: {bot_info}")
            
            # Установка webhook'а
            webhook_url = "https://yourdomain.com/webhook/max/"
            success = await bot.set_webhook(webhook_url)
            print(f"Webhook set: {success}")
            
            # Пример обработки сообщения
            test_message = {
                "message_id": 123,
                "from": {
                    "id": "user123",
                    "first_name": "Тест",
                    "username": "testuser"
                },
                "chat": {
                    "id": "chat123",
                    "type": "private"
                },
                "date": 1234567890,
                "text": "Привет! Какие у вас есть товары?"
            }
            
            response = await bot.handle_message(test_message)
            print(f"Bot response: {response}")
    
    # asyncio.run(main())
    pass
