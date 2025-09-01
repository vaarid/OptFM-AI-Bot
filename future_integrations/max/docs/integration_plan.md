# Детальный план интеграции с MAX Мессенджером

## 1. Техническая архитектура

### 1.1 Текущая архитектура OptFM Bot
```
├── run_bot.py                  # Точка входа (только Telegram)
├── src/
│   ├── config.py              # Конфигурация (легко расширить)
│   ├── main.py                # FastAPI сервер (готов для webhook'ов)
│   ├── bot/
│   │   └── telegram_bot.py    # Telegram специфичный код
│   └── faq/
│       └── enhanced_faq_manager.py  # Независим от платформы!
```

### 1.2 Целевая архитектура с MAX
```
├── run_bot.py                  # Запуск обоих ботов
├── src/
│   ├── config.py              # + MAX конфигурация
│   ├── main.py                # + MAX webhook роутер
│   ├── bot/
│   │   ├── telegram_bot.py    # Существующий
│   │   └── max_bot.py         # НОВЫЙ: MAX бот
│   ├── api/
│   │   └── max_webhook.py     # НОВЫЙ: Webhook обработчик
│   └── faq/
│       └── enhanced_faq_manager.py  # Переиспользуется!
```

## 2. Компоненты для разработки

### 2.1 OptFMMaxBot класс (`src/bot/max_bot.py`)

**Основные методы:**
- `__init__(api_key, base_url)` - Инициализация
- `send_message(chat_id, text)` - Отправка сообщения
- `handle_message(message_data)` - Обработка входящего сообщения
- `_process_user_message(text, user_name)` - Бизнес-логика (как в Telegram)

**Зависимости:**
- `aiohttp` - Для HTTP запросов к MAX API
- `EnhancedFAQManager` - Переиспользование FAQ логики

### 2.2 Webhook обработчик (`src/api/max_webhook.py`)

**Эндпоинты:**
- `POST /webhook/max/` - Основной webhook
- `GET /webhook/max/status` - Статус интеграции

**Функциональность:**
- Валидация входящих webhook'ов
- Маршрутизация сообщений к OptFMMaxBot
- Обработка ошибок и логирование

### 2.3 Конфигурация (`src/config.py`)

**Новые переменные:**
```python
# MAX Messenger
MAX_API_KEY: str = os.getenv("MAX_API_KEY", "")
MAX_BASE_URL: str = os.getenv("MAX_BASE_URL", "https://max-api.chat/api")
MAX_WEBHOOK_URL: str = os.getenv("MAX_WEBHOOK_URL", "")
MAX_WEBHOOK_SECRET: str = os.getenv("MAX_WEBHOOK_SECRET", "")
```

## 3. Пошаговая реализация

### Шаг 1: Изучение MAX API
- [ ] Регистрация на https://max-api.chat
- [ ] Получение тестового API ключа
- [ ] Изучение документации API
- [ ] Тестирование базовых запросов (curl/Postman)

### Шаг 2: Создание OptFMMaxBot
- [ ] Создать `src/bot/max_bot.py`
- [ ] Реализовать HTTP клиент для MAX API
- [ ] Портировать логику обработки сообщений из Telegram бота
- [ ] Добавить обработку ошибок и логирование

### Шаг 3: Webhook обработчик
- [ ] Создать `src/api/max_webhook.py`
- [ ] Добавить FastAPI роутер для webhook'ов
- [ ] Реализовать валидацию входящих данных
- [ ] Интегрировать с OptFMMaxBot

### Шаг 4: Расширение конфигурации
- [ ] Добавить MAX переменные в `config.py`
- [ ] Обновить валидацию конфигурации
- [ ] Добавить в `env.example`

### Шаг 5: Интеграция в main.py
- [ ] Подключить MAX webhook роутер
- [ ] Добавить статус эндпоинт для мониторинга
- [ ] Обновить CORS настройки если нужно

### Шаг 6: Обновление run_bot.py
- [ ] Добавить инициализацию MAX бота
- [ ] Обновить логику запуска/остановки
- [ ] Добавить в логирование

## 4. API MAX - Основные методы

### 4.1 Отправка сообщения
```http
POST /api/sendMessage
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "chat_id": "chat_id_here",
  "text": "Текст сообщения"
}
```

### 4.2 Настройка webhook'а
```http
POST /api/setWebhook
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "url": "https://yourdomain.com/webhook/max/",
  "secret_token": "your_secret_token"
}
```

### 4.3 Формат входящего сообщения
```json
{
  "message": {
    "message_id": 123,
    "from": {
      "id": "user_id",
      "first_name": "Имя",
      "username": "username"
    },
    "chat": {
      "id": "chat_id",
      "type": "private"
    },
    "date": 1234567890,
    "text": "Текст сообщения от пользователя"
  }
}
```

## 5. Тестирование

### 5.1 Unit тесты
```python
# tests/test_max_bot.py
class TestOptFMMaxBot:
    def test_init()
    def test_send_message()
    def test_handle_message()
    def test_process_user_message()
```

### 5.2 Интеграционные тесты
```python
# tests/test_max_integration.py
class TestMaxIntegration:
    def test_webhook_handler()
    def test_faq_integration()
    def test_error_handling()
```

### 5.3 Тестовые сценарии
- [ ] Отправка простого сообщения
- [ ] Поиск в FAQ
- [ ] Обработка приветствий/прощаний
- [ ] Обработка некорректных запросов
- [ ] Тестирование webhook'а

## 6. Развертывание

### 6.1 Настройка переменных окружения
```bash
# В .env добавить:
MAX_API_KEY=your_max_api_key_here
MAX_BASE_URL=https://max-api.chat/api
MAX_WEBHOOK_URL=https://yourdomain.com/webhook/max/
MAX_WEBHOOK_SECRET=your_webhook_secret
```

### 6.2 Настройка webhook'а в MAX
```bash
curl -X POST "https://max-api.chat/api/setWebhook" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yourdomain.com/webhook/max/",
    "secret_token": "your_webhook_secret"
  }'
```

### 6.3 Проверка работы
- [ ] Проверить статус webhook'а: `GET /webhook/max/status`
- [ ] Отправить тестовое сообщение в MAX бота
- [ ] Проверить логи на сервере
- [ ] Протестировать FAQ поиск

## 7. Мониторинг и логирование

### 7.1 Метрики для отслеживания
- Количество входящих сообщений от MAX
- Количество отправленных ответов
- Частота ошибок API
- Время ответа

### 7.2 Логи
```python
# Примеры логирования
logger.info(f"MAX message received from user {user_id}: {message_text}")
logger.info(f"MAX response sent to user {user_id}: {response_text}")
logger.error(f"MAX API error: {error_details}")
```

## 8. Безопасность

### 8.1 Валидация webhook'ов
- Проверка secret token
- Валидация структуры данных
- Rate limiting

### 8.2 Обработка API ключей
- Хранение в переменных окружения
- Не логировать чувствительные данные
- Ротация ключей при необходимости

## 9. Производительность

### 9.1 Оптимизации
- Переиспользование HTTP соединений
- Кэширование частых запросов FAQ
- Асинхронная обработка сообщений

### 9.2 Ограничения
- Rate limits MAX API
- Таймауты webhook'ов
- Размер сообщений

## 10. Поддержка и обслуживание

### 10.1 Мониторинг работоспособности
- Автоматическая проверка доступности API
- Уведомления о сбоях
- Dashboard с метриками

### 10.2 Обновления
- Отслеживание изменений в MAX API
- Обновление зависимостей
- Миграция при изменении API

## Заключение

Данный план обеспечивает поэтапную и безопасную интеграцию с MAX мессенджером, максимально переиспользуя существующую архитектуру OptFM AI Bot.
