# MAX API Reference для интеграции OptFM Bot

## Обзор

Этот документ содержит справочную информацию по MAX API, необходимую для интеграции с OptFM AI Bot. Основан на неофициальном API https://max-api.chat

## Базовая информация

- **Base URL**: `https://max-api.chat/api`
- **Аутентификация**: Bearer Token в заголовке `Authorization`
- **Content-Type**: `application/json`
- **Rate Limiting**: ~30 запросов в минуту (зависит от тарифа)

## Аутентификация

Все запросы должны содержать заголовок авторизации:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## Основные методы API

### 1. Получение информации о боте

```http
GET /api/getMe
```

**Описание**: Возвращает информацию о текущем боте

**Пример ответа**:
```json
{
  "ok": true,
  "result": {
    "id": "bot_id",
    "is_bot": true,
    "first_name": "OptFM Bot",
    "username": "optfm_bot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false
  }
}
```

### 2. Отправка сообщения

```http
POST /api/sendMessage
```

**Параметры**:
```json
{
  "chat_id": "string",     // ID чата (обязательно)
  "text": "string",        // Текст сообщения (обязательно)
  "parse_mode": "string",  // Опционально: HTML, Markdown
  "disable_web_page_preview": boolean,  // Опционально
  "disable_notification": boolean,      // Опционально
  "reply_to_message_id": integer       // Опционально
}
```

**Пример запроса**:
```json
{
  "chat_id": "123456789",
  "text": "Привет! Это сообщение от OptFM Bot.",
  "parse_mode": "HTML"
}
```

**Пример ответа**:
```json
{
  "ok": true,
  "result": {
    "message_id": 456,
    "from": {
      "id": "bot_id",
      "is_bot": true,
      "first_name": "OptFM Bot",
      "username": "optfm_bot"
    },
    "chat": {
      "id": "123456789",
      "type": "private"
    },
    "date": 1234567890,
    "text": "Привет! Это сообщение от OptFM Bot."
  }
}
```

### 3. Настройка webhook'а

```http
POST /api/setWebhook
```

**Параметры**:
```json
{
  "url": "string",           // URL для webhook'а (обязательно)
  "certificate": "string",   // Опционально: SSL сертификат
  "ip_address": "string",    // Опционально: фиксированный IP
  "max_connections": integer, // Опционально: макс. соединений (1-100)
  "allowed_updates": ["array"], // Опционально: типы обновлений
  "drop_pending_updates": boolean, // Опционально: удалить старые обновления
  "secret_token": "string"   // Опционально: секретный токен
}
```

**Пример запроса**:
```json
{
  "url": "https://yourdomain.com/webhook/max/",
  "secret_token": "your_secret_token_here",
  "max_connections": 40,
  "allowed_updates": ["message", "callback_query"]
}
```

### 4. Удаление webhook'а

```http
POST /api/deleteWebhook
```

**Параметры**:
```json
{
  "drop_pending_updates": boolean  // Опционально: удалить ожидающие обновления
}
```

### 5. Получение информации о webhook'е

```http
GET /api/getWebhookInfo
```

**Пример ответа**:
```json
{
  "ok": true,
  "result": {
    "url": "https://yourdomain.com/webhook/max/",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "ip_address": "1.2.3.4",
    "last_error_date": 0,
    "last_error_message": "",
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"]
  }
}
```

## Структура входящих обновлений (Webhook)

### Формат сообщения

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 456,
    "from": {
      "id": "user_id",
      "is_bot": false,
      "first_name": "Иван",
      "last_name": "Петров",
      "username": "ivan_petrov",
      "language_code": "ru"
    },
    "chat": {
      "id": "chat_id",
      "first_name": "Иван",
      "last_name": "Петров",
      "username": "ivan_petrov",
      "type": "private"
    },
    "date": 1234567890,
    "text": "Привет! Какие у вас есть товары?"
  }
}
```

### Типы чатов

- `"private"` - личный чат с пользователем
- `"group"` - группа
- `"supergroup"` - супергруппа
- `"channel"` - канал

### Поддерживаемые типы контента

1. **Текстовые сообщения** - `text`
2. **Фото** - `photo`
3. **Документы** - `document`
4. **Аудио** - `audio`
5. **Видео** - `video`
6. **Стикеры** - `sticker`
7. **Геолокация** - `location`
8. **Контакт** - `contact`

## Обработка ошибок

### Коды ошибок

- **400** - Bad Request (неверные параметры)
- **401** - Unauthorized (неверный API ключ)
- **403** - Forbidden (недостаточно прав)
- **404** - Not Found (чат/пользователь не найден)
- **429** - Too Many Requests (превышен лимит)
- **500** - Internal Server Error (ошибка сервера)

### Формат ошибки

```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: chat not found"
}
```

### Рекомендации по обработке ошибок

```python
async def handle_api_error(response_status: int, error_data: dict):
    """Обработка ошибок MAX API"""
    
    if response_status == 429:
        # Rate limiting - ждем и повторяем
        retry_after = error_data.get("parameters", {}).get("retry_after", 60)
        await asyncio.sleep(retry_after)
        return "retry"
    
    elif response_status == 403:
        # Пользователь заблокировал бота
        logger.warning(f"User blocked bot: {error_data}")
        return "blocked"
    
    elif response_status == 404:
        # Чат не найден
        logger.warning(f"Chat not found: {error_data}")
        return "not_found"
    
    else:
        # Другие ошибки
        logger.error(f"API error {response_status}: {error_data}")
        return "error"
```

## Ограничения и лимиты

### Rate Limits

- **Сообщения**: 30 сообщений в секунду
- **Группы**: 20 сообщений в минуту на группу
- **API запросы**: зависит от тарифного плана

### Размеры контента

- **Текст сообщения**: до 4096 символов
- **Подпись к медиа**: до 1024 символов
- **Файлы**: до 50 МБ
- **Фото**: до 10 МБ

### Webhook ограничения

- **Таймаут**: 60 секунд на обработку webhook'а
- **Размер**: до 1 МБ на запрос
- **Соединения**: до 100 одновременных

## Безопасность

### Проверка подписи webhook'а

```python
import hmac
import hashlib

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Проверка подписи webhook'а"""
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

### Рекомендации

1. **Используйте HTTPS** для webhook'ов
2. **Проверяйте подписи** с secret_token
3. **Валидируйте входящие данные**
4. **Логируйте подозрительную активность**
5. **Регулярно обновляйте API ключи**

## Примеры использования в OptFM Bot

### Инициализация клиента

```python
import aiohttp

class MaxAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://max-api.chat/api"
        self.session = None
    
    async def _get_session(self):
        if not self.session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
```

### Отправка сообщения

```python
async def send_message(self, chat_id: str, text: str) -> bool:
    session = await self._get_session()
    
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
        if response.status == 200:
            return True
        else:
            error = await response.json()
            logger.error(f"Failed to send message: {error}")
            return False
```

### Обработка webhook'а

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/max/")
async def max_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        message = data["message"]
        
        # Обработка текстового сообщения
        if "text" in message:
            user_text = message["text"]
            chat_id = message["chat"]["id"]
            
            # Логика обработки сообщения
            response = await process_user_message(user_text)
            
            # Отправка ответа
            await send_message(chat_id, response)
    
    return {"status": "ok"}
```

## Отладка и тестирование

### Проверка API ключа

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://max-api.chat/api/getMe
```

### Настройка webhook'а

```bash
curl -X POST "https://max-api.chat/api/setWebhook" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/webhook/max/"}'
```

### Проверка webhook'а

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://max-api.chat/api/getWebhookInfo
```

## Полезные ссылки

- **MAX API документация**: https://max-api.chat/docs
- **Сообщество разработчиков**: https://max-api.chat/community
- **Получение API ключа**: https://max-api.chat/bot/new
- **Статус сервиса**: https://status.max-api.chat

## Заметки для разработчиков

1. **API неофициальный** - может измениться без предупреждения
2. **Тестируйте на staging** перед деплоем в продакшн
3. **Мониторьте логи** на предмет изменений в API
4. **Имейте fallback план** на случай недоступности сервиса
5. **Документируйте все изменения** в интеграции
