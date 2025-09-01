"""
MAX Messenger Webhook Handler for OptFM AI Bot

Этот модуль содержит FastAPI роутер для обработки webhook'ов от MAX мессенджера.
Интегрируется с OptFMMaxBot для обработки входящих сообщений.
"""
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from typing import Dict, Any, Optional
import logging
import hashlib
import hmac
import json

# Импорт MAX бота (при интеграции изменить путь)
from ..bot.max_bot import OptFMMaxBot

logger = logging.getLogger(__name__)

# Создание роутера для MAX webhook'ов
router = APIRouter(prefix="/webhook/max", tags=["MAX Webhook"])

# Глобальная переменная для экземпляра бота
max_bot_instance: Optional[OptFMMaxBot] = None

def get_max_bot() -> OptFMMaxBot:
    """
    Получение экземпляра MAX бота
    
    Returns:
        OptFMMaxBot: Экземпляр бота
        
    Raises:
        HTTPException: Если бот не сконфигурирован
    """
    global max_bot_instance
    
    if max_bot_instance is None:
        # В реальной интеграции загружать из Config
        api_key = "your_max_api_key_here"  # Config.MAX_API_KEY
        base_url = "https://max-api.chat/api"  # Config.MAX_BASE_URL
        
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="MAX bot not configured - API key missing"
            )
            
        max_bot_instance = OptFMMaxBot(api_key, base_url)
        logger.info("MAX bot instance created")
    
    return max_bot_instance

def verify_webhook_signature(
    body: bytes, 
    signature: str, 
    secret: str
) -> bool:
    """
    Верификация подписи webhook'а для безопасности
    
    Args:
        body: Тело запроса в байтах
        signature: Подпись из заголовка
        secret: Секретный ключ
        
    Returns:
        bool: True если подпись валидна
    """
    if not secret:
        # Если секрет не настроен, пропускаем проверку
        return True
        
    try:
        # Создаем HMAC подпись
        expected_signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем подписи
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

@router.post("/")
async def max_webhook_handler(
    request: Request,
    x_max_signature: Optional[str] = Header(None),
    bot: OptFMMaxBot = Depends(get_max_bot)
):
    """
    Основной обработчик webhook'ов от MAX
    
    Args:
        request: HTTP запрос
        x_max_signature: Подпись webhook'а (если используется)
        bot: Экземпляр MAX бота
        
    Returns:
        dict: Статус обработки
        
    Raises:
        HTTPException: При ошибках обработки
    """
    try:
        # Получаем тело запроса
        body = await request.body()
        
        # Верификация подписи (если настроена)
        webhook_secret = "your_webhook_secret"  # Config.MAX_WEBHOOK_SECRET
        if webhook_secret and x_max_signature:
            if not verify_webhook_signature(body, x_max_signature, webhook_secret):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Парсим JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        logger.info(f"Received MAX webhook: {data}")
        
        # Проверяем наличие сообщения
        if "message" not in data:
            logger.info("Webhook without message, skipping")
            return {"status": "ok", "message": "No message to process"}
            
        message = data["message"]
        
        # Проверяем, что это текстовое сообщение
        if "text" not in message:
            logger.info("Non-text message received, skipping")
            return {"status": "ok", "message": "Non-text message skipped"}
        
        # Обрабатываем сообщение
        response = await bot.handle_message(message)
        
        if response:
            logger.info("Message processed successfully")
            return {
                "status": "ok", 
                "message": "Message processed",
                "response_sent": True
            }
        else:
            logger.warning("Failed to process message")
            return {
                "status": "ok", 
                "message": "Message processing failed",
                "response_sent": False
            }
        
    except HTTPException:
        # Повторно выбрасываем HTTP исключения
        raise
    except Exception as e:
        logger.error(f"Error processing MAX webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def max_webhook_status():
    """
    Проверка статуса MAX интеграции
    
    Returns:
        dict: Статус интеграции
    """
    try:
        global max_bot_instance
        
        # Проверяем конфигурацию
        api_key_configured = True  # bool(Config.MAX_API_KEY)
        bot_initialized = max_bot_instance is not None
        
        status = {
            "max_integration": "enabled" if api_key_configured else "disabled",
            "api_key_configured": api_key_configured,
            "bot_initialized": bot_initialized,
            "webhook_endpoint": "/webhook/max/",
        }
        
        # Если бот инициализирован, проверяем связь с API
        if bot_initialized:
            try:
                bot_info = await max_bot_instance.get_me()
                status["api_connection"] = "ok" if bot_info else "error"
                status["bot_info"] = bot_info
            except Exception as e:
                status["api_connection"] = "error"
                status["api_error"] = str(e)
        else:
            status["api_connection"] = "not_tested"
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking MAX status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_max_message(
    test_data: Dict[str, Any],
    bot: OptFMMaxBot = Depends(get_max_bot)
):
    """
    Тестовый эндпоинт для проверки обработки сообщений
    
    Args:
        test_data: Тестовые данные сообщения
        bot: Экземпляр MAX бота
        
    Returns:
        dict: Результат обработки тестового сообщения
    """
    try:
        logger.info(f"Processing test message: {test_data}")
        
        # Создаем тестовое сообщение в формате MAX
        test_message = {
            "message_id": test_data.get("message_id", 999),
            "from": {
                "id": test_data.get("user_id", "test_user"),
                "first_name": test_data.get("user_name", "Тестовый пользователь"),
                "username": test_data.get("username", "testuser")
            },
            "chat": {
                "id": test_data.get("chat_id", "test_chat"),
                "type": "private"
            },
            "date": 1234567890,
            "text": test_data.get("text", "Тестовое сообщение")
        }
        
        # Обрабатываем сообщение (но не отправляем реальный ответ)
        response = await bot._process_user_message(
            test_message["text"], 
            test_message["from"]["first_name"]
        )
        
        return {
            "status": "ok",
            "test_message": test_message,
            "bot_response": response,
            "message": "Test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/setup-webhook")
async def setup_webhook(
    webhook_config: Dict[str, str],
    bot: OptFMMaxBot = Depends(get_max_bot)
):
    """
    Настройка webhook'а в MAX API
    
    Args:
        webhook_config: Конфигурация webhook'а
        bot: Экземпляр MAX бота
        
    Returns:
        dict: Результат настройки
    """
    try:
        webhook_url = webhook_config.get("webhook_url")
        secret_token = webhook_config.get("secret_token")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        # Устанавливаем webhook
        success = await bot.set_webhook(webhook_url, secret_token)
        
        if success:
            return {
                "status": "ok",
                "message": "Webhook configured successfully",
                "webhook_url": webhook_url
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to configure webhook"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhook")
async def delete_webhook(bot: OptFMMaxBot = Depends(get_max_bot)):
    """
    Удаление webhook'а
    
    Args:
        bot: Экземпляр MAX бота
        
    Returns:
        dict: Результат удаления
    """
    try:
        success = await bot.delete_webhook()
        
        if success:
            return {
                "status": "ok",
                "message": "Webhook deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to delete webhook"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Обработчик завершения приложения
async def cleanup_max_bot():
    """Очистка ресурсов при завершении приложения"""
    global max_bot_instance
    if max_bot_instance:
        await max_bot_instance.close()
        max_bot_instance = None
        logger.info("MAX bot instance cleaned up")

# Примеры использования в документации
WEBHOOK_EXAMPLES = {
    "incoming_message": {
        "message": {
            "message_id": 123,
            "from": {
                "id": "user123",
                "first_name": "Иван",
                "username": "ivan_user"
            },
            "chat": {
                "id": "chat123",
                "type": "private"
            },
            "date": 1234567890,
            "text": "Какие у вас есть товары?"
        }
    },
    "test_request": {
        "text": "Привет! Как дела?",
        "user_name": "Тестовый пользователь",
        "user_id": "test123",
        "chat_id": "test_chat"
    },
    "webhook_setup": {
        "webhook_url": "https://yourdomain.com/webhook/max/",
        "secret_token": "your_secret_token_here"
    }
}
