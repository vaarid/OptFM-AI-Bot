#!/usr/bin/env python3
"""
Unit тесты для OptFMMaxBot

Этот файл содержит тесты для проверки функциональности MAX бота
без необходимости подключения к реальному MAX API.
"""
import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к модулям для тестирования
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Импортируем модуль для тестирования
from bot.max_bot import OptFMMaxBot

class TestOptFMMaxBot:
    """Тесты для основного класса MAX бота"""
    
    @pytest.fixture
    def bot(self):
        """Фикстура для создания экземпляра бота"""
        return OptFMMaxBot("test_api_key", "https://test-api.example.com")
    
    @pytest.fixture
    def mock_session(self):
        """Мок HTTP сессии"""
        session = AsyncMock()
        return session
    
    def test_init(self):
        """Тест инициализации бота"""
        bot = OptFMMaxBot("test_key", "https://test.com")
        
        assert bot.api_key == "test_key"
        assert bot.base_url == "https://test.com"
        assert bot.session is None
        assert bot.faq_manager is not None
    
    def test_init_default_url(self):
        """Тест инициализации с URL по умолчанию"""
        bot = OptFMMaxBot("test_key")
        
        assert bot.base_url == "https://max-api.chat/api"
    
    @pytest.mark.asyncio
    async def test_get_session(self, bot):
        """Тест получения HTTP сессии"""
        session = await bot._get_session()
        
        assert isinstance(session, aiohttp.ClientSession)
        assert session is bot.session
        
        # Проверяем, что повторный вызов возвращает ту же сессию
        session2 = await bot._get_session()
        assert session is session2
        
        await bot.close()
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, bot, mock_session):
        """Тест успешной отправки сообщения"""
        # Настраиваем мок ответа
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        # Тестируем отправку
        result = await bot.send_message("chat_123", "Test message")
        
        assert result is True
        mock_session.post.assert_called_once()
        
        # Проверяем параметры запроса
        call_args = mock_session.post.call_args
        assert "sendMessage" in call_args[0][0]
        assert call_args[1]["json"]["chat_id"] == "chat_123"
        assert call_args[1]["json"]["text"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, bot, mock_session):
        """Тест неудачной отправки сообщения"""
        # Настраиваем мок ответа с ошибкой
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        # Тестируем отправку
        result = await bot.send_message("chat_123", "Test message")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_exception(self, bot, mock_session):
        """Тест обработки исключений при отправке"""
        mock_session.post.side_effect = Exception("Network error")
        bot.session = mock_session
        
        result = await bot.send_message("chat_123", "Test message")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self, bot):
        """Тест успешной обработки входящего сообщения"""
        message_data = {
            "message_id": 123,
            "from": {
                "id": "user_123",
                "first_name": "Test User"
            },
            "chat": {
                "id": "chat_123",
                "type": "private"
            },
            "date": 1234567890,
            "text": "Привет!"
        }
        
        # Мокаем отправку сообщения
        with patch.object(bot, 'send_message', return_value=True) as mock_send:
            response = await bot.handle_message(message_data)
            
            assert response is not None
            assert "Привет" in response
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_no_chat_id(self, bot):
        """Тест обработки сообщения без chat_id"""
        message_data = {
            "message_id": 123,
            "from": {"id": "user_123", "first_name": "Test User"},
            "chat": {},  # Нет ID чата
            "text": "Привет!"
        }
        
        response = await bot.handle_message(message_data)
        assert response is not None  # Ответ генерируется, но не отправляется
    
    @pytest.mark.asyncio
    async def test_process_greeting_message(self, bot):
        """Тест обработки приветствия"""
        response = await bot._process_user_message("Привет!", "Иван")
        
        assert "Привет, Иван" in response
        assert "OptFM" in response
        assert "MAX" in response
    
    @pytest.mark.asyncio
    async def test_process_farewell_message(self, bot):
        """Тест обработки прощания"""
        response = await bot._process_user_message("Спасибо, до свидания!", "Анна")
        
        assert "До свидания, Анна" in response
        assert "OptFM" in response
    
    @pytest.mark.asyncio
    async def test_process_short_message(self, bot):
        """Тест обработки короткого сообщения"""
        response = await bot._process_user_message("ок", "Петр")
        
        assert "Петр, я не совсем понял" in response
        assert "Задайте мне вопрос" in response
    
    @pytest.mark.asyncio
    @patch('bot.max_bot.EnhancedFAQManager')
    async def test_process_faq_message_found(self, mock_faq_manager_class, bot):
        """Тест обработки вопроса с найденным ответом в FAQ"""
        # Настраиваем мок FAQ Manager
        mock_faq_manager = MagicMock()
        mock_faq_manager.search_faq.return_value = {
            "id": 1,
            "question": "Тестовый вопрос",
            "answer": "Тестовый ответ из FAQ"
        }
        bot.faq_manager = mock_faq_manager
        
        response = await bot._process_user_message("Какие у вас товары?", "Мария")
        
        assert "Тестовый ответ из FAQ" in response
        assert "дополнительные вопросы" in response
    
    @pytest.mark.asyncio
    @patch('bot.max_bot.EnhancedFAQManager')
    async def test_process_faq_message_not_found(self, mock_faq_manager_class, bot):
        """Тест обработки вопроса без ответа в FAQ"""
        # Настраиваем мок FAQ Manager
        mock_faq_manager = MagicMock()
        mock_faq_manager.search_faq.return_value = None
        bot.faq_manager = mock_faq_manager
        
        response = await bot._process_user_message("Очень специфический вопрос", "Алексей")
        
        assert "не нашел точного ответа" in response
        assert "оставьте заявку" in response
        assert "Очень специфический вопрос" in response
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, bot, mock_session):
        """Тест успешного получения информации о боте"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "ok": True,
            "result": {
                "id": "bot_123",
                "first_name": "Test Bot",
                "username": "test_bot"
            }
        }
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        result = await bot.get_me()
        
        assert result is not None
        assert result["ok"] is True
        assert result["result"]["id"] == "bot_123"
    
    @pytest.mark.asyncio
    async def test_get_me_failure(self, bot, mock_session):
        """Тест неудачного получения информации о боте"""
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        result = await bot.get_me()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_webhook_success(self, bot, mock_session):
        """Тест успешной установки webhook'а"""
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        result = await bot.set_webhook("https://example.com/webhook", "secret_token")
        
        assert result is True
        
        # Проверяем параметры запроса
        call_args = mock_session.post.call_args
        assert "setWebhook" in call_args[0][0]
        webhook_data = call_args[1]["json"]
        assert webhook_data["url"] == "https://example.com/webhook"
        assert webhook_data["secret_token"] == "secret_token"
    
    @pytest.mark.asyncio
    async def test_set_webhook_without_secret(self, bot, mock_session):
        """Тест установки webhook'а без секретного токена"""
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        result = await bot.set_webhook("https://example.com/webhook")
        
        assert result is True
        
        # Проверяем что secret_token не передан
        webhook_data = mock_session.post.call_args[1]["json"]
        assert "secret_token" not in webhook_data
    
    @pytest.mark.asyncio
    async def test_delete_webhook_success(self, bot, mock_session):
        """Тест успешного удаления webhook'а"""
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        bot.session = mock_session
        
        result = await bot.delete_webhook()
        
        assert result is True
        mock_session.post.assert_called_once()
        assert "deleteWebhook" in mock_session.post.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_close(self, bot):
        """Тест закрытия сессии"""
        # Создаем мок сессию
        mock_session = AsyncMock()
        bot.session = mock_session
        
        await bot.close()
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Тест использования как context manager"""
        async with OptFMMaxBot("test_key") as bot:
            assert isinstance(bot, OptFMMaxBot)
        
        # После выхода из контекста сессия должна быть закрыта
        # (проверяем что нет ошибок)

class TestMaxBotMessageProcessing:
    """Тесты для обработки различных типов сообщений"""
    
    @pytest.fixture
    def bot(self):
        return OptFMMaxBot("test_api_key")
    
    @pytest.mark.asyncio
    async def test_greeting_variations(self, bot):
        """Тест различных вариантов приветствий"""
        greetings = [
            "привет",
            "Здравствуйте",
            "Добрый день",
            "Hi",
            "Hello"
        ]
        
        for greeting in greetings:
            response = await bot._process_user_message(greeting, "Тест")
            assert "Привет, Тест" in response
            assert "OptFM" in response
    
    @pytest.mark.asyncio
    async def test_farewell_variations(self, bot):
        """Тест различных вариантов прощаний"""
        farewells = [
            "пока",
            "до свидания",
            "спасибо",
            "благодарю",
            "bye"
        ]
        
        for farewell in farewells:
            response = await bot._process_user_message(farewell, "Тест")
            assert "До свидания, Тест" in response
            assert "OptFM" in response
    
    @pytest.mark.asyncio
    async def test_question_detection(self, bot):
        """Тест распознавания вопросов"""
        questions = [
            "Что у вас есть?",
            "Как заказать?",
            "Где вы находитесь?",
            "Сколько это стоит?",
            "Есть ли у вас гарантия?",
            "Можно ли вернуть товар?",
            "Просто вопрос без ключевых слов?"
        ]
        
        for question in questions:
            response = await bot._process_user_message(question, "Тест")
            # Должен обрабатываться как поиск в FAQ, а не как короткое сообщение
            assert "не совсем понял" not in response

class TestMaxBotErrorHandling:
    """Тесты для обработки ошибочных ситуаций"""
    
    @pytest.fixture
    def bot(self):
        return OptFMMaxBot("test_api_key")
    
    @pytest.mark.asyncio
    async def test_handle_message_empty_data(self, bot):
        """Тест обработки пустых данных сообщения"""
        result = await bot.handle_message({})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_message_missing_fields(self, bot):
        """Тест обработки сообщения с отсутствующими полями"""
        incomplete_message = {
            "from": {"first_name": "Test"},
            # Отсутствуют другие обязательные поля
        }
        
        # Не должно вызывать исключение
        result = await bot.handle_message(incomplete_message)
        assert result is not None  # Должен сгенерировать ответ
    
    @pytest.mark.asyncio
    async def test_send_message_timeout(self, bot):
        """Тест обработки таймаута при отправке сообщения"""
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()
        bot.session = mock_session
        
        result = await bot.send_message("chat_123", "Test")
        assert result is False

@pytest.mark.integration
class TestMaxBotIntegration:
    """Интеграционные тесты (требуют реального API ключа)"""
    
    @pytest.mark.skip(reason="Требует реальный API ключ")
    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """Тест подключения к реальному API (пропускается по умолчанию)"""
        api_key = os.getenv("MAX_API_KEY_FOR_TESTING")
        if not api_key:
            pytest.skip("MAX_API_KEY_FOR_TESTING не установлен")
        
        async with OptFMMaxBot(api_key) as bot:
            bot_info = await bot.get_me()
            assert bot_info is not None
            assert bot_info.get("ok") is True

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
