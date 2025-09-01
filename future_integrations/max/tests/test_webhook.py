#!/usr/bin/env python3
"""
Тесты для MAX webhook обработчика

Этот файл содержит тесты для проверки FastAPI эндпоинтов
для обработки webhook'ов от MAX мессенджера.
"""
import pytest
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к модулям для тестирования
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Импортируем модуль для тестирования
from api.max_webhook import router, get_max_bot, verify_webhook_signature

# Создаем тестовое FastAPI приложение
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

class TestWebhookSignatureVerification:
    """Тесты для проверки подписи webhook'ов"""
    
    def test_verify_signature_correct(self):
        """Тест корректной подписи"""
        secret = "test_secret"
        body = b'{"test": "data"}'
        
        # Создаем правильную подпись
        signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        assert verify_webhook_signature(body, signature, secret) is True
    
    def test_verify_signature_incorrect(self):
        """Тест некорректной подписи"""
        secret = "test_secret"
        body = b'{"test": "data"}'
        wrong_signature = "wrong_signature"
        
        assert verify_webhook_signature(body, wrong_signature, secret) is False
    
    def test_verify_signature_no_secret(self):
        """Тест без секретного ключа (должен пропускать проверку)"""
        body = b'{"test": "data"}'
        signature = "any_signature"
        
        assert verify_webhook_signature(body, signature, "") is True
    
    def test_verify_signature_exception(self):
        """Тест обработки исключений при проверке подписи"""
        # Передаем некорректные данные для вызова исключения
        assert verify_webhook_signature(None, "signature", "secret") is False

class TestMaxWebhookEndpoints:
    """Тесты для эндпоинтов webhook'а"""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_message_data(self):
        """Фикстура с валидными данными сообщения"""
        return {
            "message": {
                "message_id": 123,
                "from": {
                    "id": "user_123",
                    "first_name": "Тест",
                    "username": "test_user"
                },
                "chat": {
                    "id": "chat_123",
                    "type": "private"
                },
                "date": 1234567890,
                "text": "Привет!"
            }
        }
    
    @patch('api.max_webhook.get_max_bot')
    def test_webhook_handler_success(self, mock_get_bot, client, valid_message_data):
        """Тест успешной обработки webhook'а"""
        # Настраиваем мок бота
        mock_bot = AsyncMock()
        mock_bot.handle_message.return_value = "Тестовый ответ"
        mock_get_bot.return_value = mock_bot
        
        # Отправляем запрос
        response = client.post("/webhook/max/", json=valid_message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["response_sent"] is True
    
    @patch('api.max_webhook.get_max_bot')
    def test_webhook_handler_no_message(self, mock_get_bot, client):
        """Тест webhook'а без сообщения"""
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        # Отправляем запрос без поля "message"
        response = client.post("/webhook/max/", json={"update_id": 123})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "No message to process" in data["message"]
    
    @patch('api.max_webhook.get_max_bot')
    def test_webhook_handler_non_text_message(self, mock_get_bot, client):
        """Тест webhook'а с не-текстовым сообщением"""
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        message_data = {
            "message": {
                "message_id": 123,
                "from": {"id": "user_123", "first_name": "Тест"},
                "chat": {"id": "chat_123", "type": "private"},
                "date": 1234567890,
                "photo": [{"file_id": "photo_123"}]  # Фото вместо текста
            }
        }
        
        response = client.post("/webhook/max/", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "Non-text message skipped" in data["message"]
    
    def test_webhook_handler_invalid_json(self, client):
        """Тест webhook'а с некорректным JSON"""
        response = client.post(
            "/webhook/max/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
    
    @patch('api.max_webhook.get_max_bot')
    def test_webhook_handler_bot_not_configured(self, mock_get_bot, client, valid_message_data):
        """Тест webhook'а когда бот не сконфигурирован"""
        from fastapi import HTTPException
        mock_get_bot.side_effect = HTTPException(status_code=500, detail="Bot not configured")
        
        response = client.post("/webhook/max/", json=valid_message_data)
        
        assert response.status_code == 500
    
    @patch('api.max_webhook.get_max_bot')
    def test_webhook_handler_processing_failure(self, mock_get_bot, client, valid_message_data):
        """Тест webhook'а когда обработка сообщения не удалась"""
        mock_bot = AsyncMock()
        mock_bot.handle_message.return_value = None  # Обработка не удалась
        mock_get_bot.return_value = mock_bot
        
        response = client.post("/webhook/max/", json=valid_message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_sent"] is False
    
    def test_webhook_signature_verification(self, client, valid_message_data):
        """Тест проверки подписи webhook'а"""
        # Этот тест требует более сложной настройки для корректной работы
        # с FastAPI и проверкой подписи
        pass  # TODO: Реализовать когда будет готова интеграция
    
    def test_status_endpoint(self, client):
        """Тест эндпоинта статуса"""
        response = client.get("/webhook/max/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "max_integration" in data
        assert "api_key_configured" in data
        assert "bot_initialized" in data
    
    @patch('api.max_webhook.get_max_bot')
    def test_test_endpoint_success(self, mock_get_bot, client):
        """Тест тестового эндпоинта"""
        mock_bot = AsyncMock()
        mock_bot._process_user_message.return_value = "Тестовый ответ"
        mock_get_bot.return_value = mock_bot
        
        test_data = {
            "text": "Привет",
            "user_name": "Тест",
            "user_id": "test_123",
            "chat_id": "chat_123"
        }
        
        response = client.post("/webhook/max/test", json=test_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "bot_response" in data
        assert data["bot_response"] == "Тестовый ответ"
    
    def test_test_endpoint_minimal_data(self, client):
        """Тест тестового эндпоинта с минимальными данными"""
        with patch('api.max_webhook.get_max_bot') as mock_get_bot:
            mock_bot = AsyncMock()
            mock_bot._process_user_message.return_value = "Ответ"
            mock_get_bot.return_value = mock_bot
            
            # Отправляем только текст
            response = client.post("/webhook/max/test", json={"text": "тест"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
    
    @patch('api.max_webhook.get_max_bot')
    def test_setup_webhook_endpoint(self, mock_get_bot, client):
        """Тест эндпоинта настройки webhook'а"""
        mock_bot = AsyncMock()
        mock_bot.set_webhook.return_value = True
        mock_get_bot.return_value = mock_bot
        
        webhook_config = {
            "webhook_url": "https://example.com/webhook/max/",
            "secret_token": "test_secret"
        }
        
        response = client.post("/webhook/max/setup-webhook", json=webhook_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "successfully" in data["message"]
    
    def test_setup_webhook_endpoint_missing_url(self, client):
        """Тест эндпоинта настройки webhook'а без URL"""
        response = client.post("/webhook/max/setup-webhook", json={})
        
        assert response.status_code == 400
    
    @patch('api.max_webhook.get_max_bot')
    def test_setup_webhook_endpoint_failure(self, mock_get_bot, client):
        """Тест неудачной настройки webhook'а"""
        mock_bot = AsyncMock()
        mock_bot.set_webhook.return_value = False
        mock_get_bot.return_value = mock_bot
        
        webhook_config = {"webhook_url": "https://example.com/webhook/max/"}
        
        response = client.post("/webhook/max/setup-webhook", json=webhook_config)
        
        assert response.status_code == 500
    
    @patch('api.max_webhook.get_max_bot')
    def test_delete_webhook_endpoint(self, mock_get_bot, client):
        """Тест эндпоинта удаления webhook'а"""
        mock_bot = AsyncMock()
        mock_bot.delete_webhook.return_value = True
        mock_get_bot.return_value = mock_bot
        
        response = client.delete("/webhook/max/webhook")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "deleted successfully" in data["message"]
    
    @patch('api.max_webhook.get_max_bot')
    def test_delete_webhook_endpoint_failure(self, mock_get_bot, client):
        """Тест неудачного удаления webhook'а"""
        mock_bot = AsyncMock()
        mock_bot.delete_webhook.return_value = False
        mock_get_bot.return_value = mock_bot
        
        response = client.delete("/webhook/max/webhook")
        
        assert response.status_code == 500

class TestGetMaxBot:
    """Тесты для функции get_max_bot"""
    
    @patch('api.max_webhook.max_bot_instance', None)
    @patch('api.max_webhook.OptFMMaxBot')
    def test_get_max_bot_creates_instance(self, mock_bot_class):
        """Тест создания экземпляра бота"""
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot
        
        # Мокаем конфигурацию
        with patch('api.max_webhook.max_bot_instance', None):
            # В реальном коде здесь будет Config.MAX_API_KEY
            with patch.dict('os.environ', {'MAX_API_KEY': 'test_key'}):
                result = get_max_bot()
                
                # Проверяем что создался экземпляр
                assert result is not None
    
    @patch('api.max_webhook.max_bot_instance', None)
    def test_get_max_bot_no_api_key(self):
        """Тест получения бота без API ключа"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_max_bot()
        
        assert exc_info.value.status_code == 500
        assert "not configured" in str(exc_info.value.detail)

class TestWebhookPerformance:
    """Тесты производительности webhook'а"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('api.max_webhook.get_max_bot')
    def test_concurrent_webhooks(self, mock_get_bot, client):
        """Тест одновременной обработки множественных webhook'ов"""
        mock_bot = AsyncMock()
        mock_bot.handle_message.return_value = "Ответ"
        mock_get_bot.return_value = mock_bot
        
        # Создаем несколько сообщений
        messages = []
        for i in range(5):
            messages.append({
                "message": {
                    "message_id": i,
                    "from": {"id": f"user_{i}", "first_name": f"User{i}"},
                    "chat": {"id": f"chat_{i}", "type": "private"},
                    "date": 1234567890,
                    "text": f"Сообщение {i}"
                }
            })
        
        # Отправляем все сообщения
        responses = []
        for message in messages:
            response = client.post("/webhook/max/", json=message)
            responses.append(response)
        
        # Проверяем что все обработались успешно
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

class TestWebhookSecurity:
    """Тесты безопасности webhook'а"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_large_payload_handling(self, client):
        """Тест обработки большого payload'а"""
        # Создаем большое сообщение
        large_text = "A" * 10000  # 10KB текста
        
        large_message = {
            "message": {
                "message_id": 123,
                "from": {"id": "user_123", "first_name": "Test"},
                "chat": {"id": "chat_123", "type": "private"},
                "date": 1234567890,
                "text": large_text
            }
        }
        
        with patch('api.max_webhook.get_max_bot') as mock_get_bot:
            mock_bot = AsyncMock()
            mock_bot.handle_message.return_value = "Обработано"
            mock_get_bot.return_value = mock_bot
            
            response = client.post("/webhook/max/", json=large_message)
            
            # Должно обработаться нормально
            assert response.status_code == 200
    
    def test_malformed_json_handling(self, client):
        """Тест обработки некорректного JSON"""
        malformed_payloads = [
            '{"message": {"incomplete": true',  # Незакрытый JSON
            '{"message": null}',  # null сообщение
            '[]',  # Массив вместо объекта
            '"string"',  # Строка вместо объекта
        ]
        
        for payload in malformed_payloads:
            response = client.post(
                "/webhook/max/",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Должно вернуть ошибку 400
            assert response.status_code == 400
    
    def test_missing_headers(self, client):
        """Тест обработки запросов без необходимых заголовков"""
        valid_message = {
            "message": {
                "message_id": 123,
                "from": {"id": "user_123", "first_name": "Test"},
                "chat": {"id": "chat_123", "type": "private"},
                "date": 1234567890,
                "text": "Тест"
            }
        }
        
        # Отправляем без Content-Type
        response = client.post("/webhook/max/", json=valid_message)
        
        # FastAPI автоматически добавляет Content-Type для json параметра
        # Поэтому этот тест проверяет что все работает нормально
        with patch('api.max_webhook.get_max_bot') as mock_get_bot:
            mock_bot = AsyncMock()
            mock_bot.handle_message.return_value = "Ответ"
            mock_get_bot.return_value = mock_bot
            
            response = client.post("/webhook/max/", json=valid_message)
            assert response.status_code == 200

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
