# Чек-лист интеграции с MAX мессенджером

## ✅ Предварительная подготовка

- [ ] **Изучена документация MAX API** - https://max-api.chat/docs
- [ ] **Получен тестовый API ключ** - https://max-api.chat/bot/new
- [ ] **Настроено тестовое окружение** - сервер с HTTPS доступом
- [ ] **Изучена текущая архитектура OptFM Bot** - понимание FAQ Manager и структуры проекта

## 📁 Файловая структура

### Копирование модулей в основной проект

- [ ] **Скопирован MAX бот модуль**
  ```bash
  cp future_integrations/max/src/bot/max_bot.py src/bot/
  ```

- [ ] **Создана папка для API модулей**
  ```bash
  mkdir -p src/api
  ```

- [ ] **Скопирован webhook обработчик**
  ```bash
  cp future_integrations/max/src/api/max_webhook.py src/api/
  ```

### Обновление основных файлов

- [ ] **Обновлен src/config.py** - добавлены MAX переменные окружения
- [ ] **Обновлен src/main.py** - подключен MAX роутер
- [ ] **Обновлен run_bot.py** - добавлена инициализация MAX бота
- [ ] **Обновлен requirements.txt** - добавлены зависимости для MAX

## ⚙️ Конфигурация

### Переменные окружения

- [ ] **Создан .env файл** на основе `future_integrations/max/examples/env.example`
- [ ] **Заполнен MAX_API_KEY** - API ключ от MAX
- [ ] **Настроен MAX_WEBHOOK_URL** - публичный HTTPS URL для webhook'а
- [ ] **Сгенерирован MAX_WEBHOOK_SECRET** - секретный токен для безопасности
- [ ] **Проверены остальные настройки** - таймауты, лимиты и т.д.

### Проверка конфигурации

- [ ] **Запущена валидация config**
  ```bash
  python -c "from src.config import Config; print(Config.validate())"
  ```

- [ ] **Проверена доступность API**
  ```bash
  curl -H "Authorization: Bearer YOUR_API_KEY" https://max-api.chat/api/getMe
  ```

## 🛠️ Код интеграции

### Основные изменения в src/config.py

- [ ] **Добавлены MAX переменные**
  ```python
  MAX_API_KEY: str = os.getenv("MAX_API_KEY", "")
  MAX_BASE_URL: str = os.getenv("MAX_BASE_URL", "https://max-api.chat/api")
  MAX_WEBHOOK_URL: str = os.getenv("MAX_WEBHOOK_URL", "")
  MAX_WEBHOOK_SECRET: str = os.getenv("MAX_WEBHOOK_SECRET", "")
  ```

- [ ] **Обновлена валидация**
  ```python
  if cls.MAX_API_KEY and not cls.MAX_WEBHOOK_URL:
      print("ОШИБКА: MAX_WEBHOOK_URL обязателен если указан MAX_API_KEY")
      return False
  ```

- [ ] **Обновлен print_config()** - вывод статуса MAX интеграции

### Изменения в src/main.py

- [ ] **Добавлен импорт MAX роутера**
  ```python
  from src.api.max_webhook import router as max_router
  ```

- [ ] **Подключен роутер**
  ```python
  app.include_router(max_router)
  ```

### Изменения в run_bot.py

- [ ] **Добавлен импорт MAX бота**
  ```python
  from bot.max_bot import OptFMMaxBot
  ```

- [ ] **Добавлена инициализация в main()**
  ```python
  max_bot = None
  if Config.MAX_API_KEY:
      max_bot = OptFMMaxBot(Config.MAX_API_KEY, Config.MAX_BASE_URL)
  ```

- [ ] **Добавлена очистка ресурсов**
  ```python
  if max_bot:
      await max_bot.close()
  ```

## 🌐 Веб-сервер и развертывание

### Nginx конфигурация

- [ ] **Настроен SSL сертификат** - HTTPS обязателен для webhook'ов
- [ ] **Добавлен location для webhook'а**
  ```nginx
  location /webhook/max/ {
      proxy_pass http://127.0.0.1:8000;
      # ... proxy настройки
  }
  ```

- [ ] **Настроен firewall** - открыты только необходимые порты
- [ ] **Проверена доступность** - `curl https://yourdomain.com/health`

### Systemd сервис

- [ ] **Создан сервисный файл** - `/etc/systemd/system/optfm-bot.service`
- [ ] **Создан пользователь для сервиса** - `adduser --system optfm`
- [ ] **Настроены права доступа** - `chown optfm:optfm /path/to/project`
- [ ] **Включен автозапуск** - `systemctl enable optfm-bot`

## 🔗 Настройка webhook'а

### Установка webhook'а в MAX

- [ ] **Webhook настроен через API**
  ```bash
  curl -X POST "https://max-api.chat/api/setWebhook" \
       -H "Authorization: Bearer YOUR_API_KEY" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://yourdomain.com/webhook/max/", "secret_token": "YOUR_SECRET"}'
  ```

- [ ] **Проверен статус webhook'а**
  ```bash
  curl -H "Authorization: Bearer YOUR_API_KEY" https://max-api.chat/api/getWebhookInfo
  ```

### Проверка эндпоинтов

- [ ] **Webhook статус** - `GET https://yourdomain.com/webhook/max/status`
- [ ] **Тестовый эндпоинт** - `POST https://yourdomain.com/webhook/max/test`
- [ ] **Health check** - `GET https://yourdomain.com/health`

## 🧪 Тестирование

### Автоматические тесты

- [ ] **Установлены зависимости для тестов**
  ```bash
  pip install pytest pytest-asyncio
  ```

- [ ] **Запущены unit тесты**
  ```bash
  python -m pytest future_integrations/max/tests/test_max_bot.py -v
  ```

- [ ] **Запущены webhook тесты**
  ```bash
  python -m pytest future_integrations/max/tests/test_webhook.py -v
  ```

- [ ] **Запущен интеграционный тест**
  ```bash
  python future_integrations/max/examples/webhook_test.py
  ```

### Ручное тестирование

- [ ] **Отправлено тестовое сообщение боту в MAX**
- [ ] **Проверены логи приложения**
  ```bash
  sudo journalctl -u optfm-bot -f
  ```

- [ ] **Протестированы различные типы сообщений**
  - [ ] Приветствие
  - [ ] Вопросы из FAQ
  - [ ] Незнакомые вопросы
  - [ ] Прощания

## 📊 Мониторинг и логирование

### Настройка логирования

- [ ] **Добавлено логирование MAX событий** в код
- [ ] **Настроен logrotate** - `/etc/logrotate.d/optfm-bot`
- [ ] **Проверена запись логов** - `tail -f logs/app.log`

### Мониторинг

- [ ] **Настроен health check cron**
  ```bash
  */5 * * * * curl -f https://yourdomain.com/health > /dev/null 2>&1 || systemctl restart optfm-bot
  ```

- [ ] **Настроены алерты** - уведомления о сбоях (опционально)
- [ ] **Настроен мониторинг ресурсов** - CPU, RAM, диск

## 🔒 Безопасность

### Защита API ключей

- [ ] **API ключи в переменных окружения** - не в коде
- [ ] **Права доступа к .env файлу** - `chmod 600 .env`
- [ ] **Безопасный секретный токен** - сгенерирован криптографически стойкий

### Защита webhook'а

- [ ] **Проверка подписи webhook'а** - реализована в коде
- [ ] **Rate limiting** - настроен в Nginx (опционально)
- [ ] **Fail2Ban** - защита от атак (опционально)

## 📋 Документация

### Обновление документации

- [ ] **Обновлен README.md** - добавлена информация о MAX интеграции
- [ ] **Созданы инструкции для команды** - как пользоваться новой функциональностью
- [ ] **Документированы изменения** - в CHANGELOG или аналогичном файле

### Резервное копирование

- [ ] **Настроен backup скрипт** - копирование конфигурации и логов
- [ ] **Протестировано восстановление** - процедура disaster recovery

## 🚀 Запуск в продакшн

### Финальная проверка

- [ ] **Все тесты проходят** - автоматические и ручные
- [ ] **Конфигурация проверена** - production настройки
- [ ] **Мониторинг работает** - логи пишутся, алерты настроены
- [ ] **Команда проинформирована** - о новой функциональности

### Развертывание

- [ ] **Сервис запущен**
  ```bash
  sudo systemctl start optfm-bot
  sudo systemctl status optfm-bot
  ```

- [ ] **Webhook активен** - принимает сообщения от MAX
- [ ] **Проведено smoke тестирование** - базовые сценарии работают
- [ ] **Настроен rollback план** - как откатиться при проблемах

## 📈 Пост-интеграция

### Мониторинг после запуска

- [ ] **Отслеживание метрик** - количество сообщений, ошибки, время ответа
- [ ] **Анализ логов** - поиск проблем и оптимизаций
- [ ] **Сбор обратной связи** - от пользователей MAX

### Дальнейшее развитие

- [ ] **Планирование улучшений** - на основе использования
- [ ] **Интеграция с аналитикой** - понимание поведения пользователей
- [ ] **Масштабирование** - если нагрузка растет

---

## 🆘 Troubleshooting

### Частые проблемы

**Webhook не получает сообщения:**
1. Проверить доступность URL извне
2. Проверить SSL сертификат
3. Проверить логи Nginx и приложения
4. Проверить статус webhook'а в MAX API

**Бот не отвечает:**
1. Проверить логи приложения
2. Проверить работу FAQ Manager
3. Протестировать через тестовый эндпоинт
4. Проверить API ключ MAX

**Ошибки аутентификации:**
1. Проверить корректность API ключа
2. Проверить формат Authorization заголовка
3. Проверить не истек ли срок действия ключа

### Полезные команды

```bash
# Проверка статуса сервиса
sudo systemctl status optfm-bot

# Просмотр логов
sudo journalctl -u optfm-bot -f

# Перезапуск сервиса
sudo systemctl restart optfm-bot

# Проверка конфигурации Nginx
sudo nginx -t

# Тест webhook'а
curl -X POST https://yourdomain.com/webhook/max/test -H "Content-Type: application/json" -d '{"text": "тест"}'
```

---

**Удачной интеграции! 🎉**
