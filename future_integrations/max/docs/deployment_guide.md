# Руководство по развертыванию MAX интеграции

## Обзор

Этот документ содержит пошаговые инструкции по развертыванию интеграции OptFM AI Bot с MAX мессенджером в продуктивной среде.

## Предварительные требования

### Системные требования

- **Python**: 3.11+
- **Операционная система**: Linux (Ubuntu 20.04+ рекомендуется)
- **RAM**: минимум 512 МБ, рекомендуется 1 ГБ
- **Дисковое пространство**: минимум 500 МБ
- **Сеть**: доступ в интернет, открытый порт для webhook'ов

### Внешние зависимости

- **Домен**: с SSL сертификатом (HTTPS обязателен для webhook'ов)
- **Reverse proxy**: Nginx или аналогичный
- **Система мониторинга**: опционально (Prometheus, Grafana)

## Этап 1: Подготовка окружения

### 1.1 Клонирование проекта

```bash
# Клонируем репозиторий
git clone https://github.com/your-org/optfm-bot.git
cd optfm-bot

# Создаем виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 1.2 Интеграция MAX модулей

```bash
# Копируем MAX модули в основной проект
cp -r future_integrations/max/src/bot/max_bot.py src/bot/
cp -r future_integrations/max/src/api/max_webhook.py src/api/

# Создаем папку для API модулей если не существует
mkdir -p src/api
```

### 1.3 Обновление основных файлов

**src/config.py** - добавляем MAX переменные:
```python
# MAX Messenger Configuration
MAX_API_KEY: str = os.getenv("MAX_API_KEY", "")
MAX_BASE_URL: str = os.getenv("MAX_BASE_URL", "https://max-api.chat/api")
MAX_WEBHOOK_URL: str = os.getenv("MAX_WEBHOOK_URL", "")
MAX_WEBHOOK_SECRET: str = os.getenv("MAX_WEBHOOK_SECRET", "")
MAX_TIMEOUT: int = int(os.getenv("MAX_TIMEOUT", "10"))

@classmethod
def validate(cls) -> bool:
    # Добавляем проверку MAX если API ключ указан
    if cls.MAX_API_KEY and not cls.MAX_WEBHOOK_URL:
        print("ОШИБКА: MAX_WEBHOOK_URL обязателен если указан MAX_API_KEY")
        return False
    return True  # + существующая логика
```

**src/main.py** - подключаем MAX роутер:
```python
from src.api.max_webhook import router as max_router

# Добавляем роутер
app.include_router(max_router)
```

## Этап 2: Получение API ключа MAX

### 2.1 Регистрация в MAX API

1. Перейдите на https://max-api.chat
2. Зарегистрируйтесь или войдите в существующий аккаунт
3. Создайте новый бот:
   - Нажмите "Создать бота"
   - Заполните информацию о боте
   - Скопируйте полученный API ключ

### 2.2 Настройка бота в MAX

```bash
# Проверяем API ключ
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://max-api.chat/api/getMe

# Должен вернуть информацию о боте
```

## Этап 3: Конфигурация

### 3.1 Создание .env файла

```bash
# Копируем пример конфигурации
cp future_integrations/max/examples/env.example .env

# Редактируем конфигурацию
nano .env
```

**Минимальная конфигурация .env:**
```env
# Existing OptFM Bot config
TELEGRAM_BOT_TOKEN=your_telegram_token_here
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# MAX Configuration
MAX_API_KEY=your_max_api_key_here
MAX_WEBHOOK_URL=https://yourdomain.com/webhook/max/
MAX_WEBHOOK_SECRET=your_secure_secret_here
```

### 3.2 Генерация безопасного секрета

```bash
# Генерируем случайный секрет для webhook'а
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Добавляем в .env
echo "MAX_WEBHOOK_SECRET=generated_secret_here" >> .env
```

## Этап 4: Настройка веб-сервера

### 4.1 Конфигурация Nginx

```nginx
# /etc/nginx/sites-available/optfm-bot
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Webhook endpoint
    location /webhook/max/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Webhook specific settings
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        client_max_body_size 1M;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
    
    # Block access to other endpoints (security)
    location / {
        return 404;
    }
}
```

### 4.2 Активация конфигурации

```bash
# Создаем символическую ссылку
sudo ln -s /etc/nginx/sites-available/optfm-bot /etc/nginx/sites-enabled/

# Проверяем конфигурацию
sudo nginx -t

# Перезагружаем Nginx
sudo systemctl reload nginx
```

## Этап 5: Настройка systemd сервиса

### 5.1 Создание сервисного файла

```ini
# /etc/systemd/system/optfm-bot.service
[Unit]
Description=OptFM AI Bot with MAX integration
After=network.target

[Service]
Type=simple
User=optfm
Group=optfm
WorkingDirectory=/home/optfm/optfm-bot
Environment=PATH=/home/optfm/optfm-bot/.venv/bin
ExecStart=/home/optfm/optfm-bot/.venv/bin/python run_bot.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/optfm/optfm-bot/logs

[Install]
WantedBy=multi-user.target
```

### 5.2 Создание пользователя для сервиса

```bash
# Создаем пользователя для бота
sudo adduser --system --group --no-create-home optfm

# Передаем права на папку проекта
sudo chown -R optfm:optfm /path/to/optfm-bot

# Создаем папку для логов
sudo mkdir -p /home/optfm/optfm-bot/logs
sudo chown optfm:optfm /home/optfm/optfm-bot/logs
```

### 5.3 Активация сервиса

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable optfm-bot

# Запускаем сервис
sudo systemctl start optfm-bot

# Проверяем статус
sudo systemctl status optfm-bot
```

## Этап 6: Настройка webhook'а

### 6.1 Установка webhook'а через API

```bash
# Устанавливаем webhook
curl -X POST "https://max-api.chat/api/setWebhook" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://yourdomain.com/webhook/max/",
       "secret_token": "your_webhook_secret_here",
       "max_connections": 40,
       "allowed_updates": ["message"]
     }'
```

### 6.2 Проверка webhook'а

```bash
# Проверяем статус webhook'а
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://max-api.chat/api/getWebhookInfo

# Проверяем наш эндпоинт
curl https://yourdomain.com/webhook/max/status
```

## Этап 7: Тестирование

### 7.1 Запуск тестов

```bash
# Переходим в папку с тестами
cd future_integrations/max/examples

# Устанавливаем зависимости для тестов
pip install aiohttp

# Запускаем тесты
python webhook_test.py
```

### 7.2 Ручное тестирование

1. **Отправьте сообщение боту в MAX**
2. **Проверьте логи:**
   ```bash
   sudo journalctl -u optfm-bot -f
   ```
3. **Проверьте статус через API:**
   ```bash
   curl https://yourdomain.com/webhook/max/status
   ```

## Этап 8: Мониторинг и логирование

### 8.1 Настройка логирования

```python
# Добавить в src/config.py
MAX_LOG_FILE: str = os.getenv("MAX_LOG_FILE", "logs/max.log")
MAX_LOG_LEVEL: str = os.getenv("MAX_LOG_LEVEL", "INFO")
```

### 8.2 Logrotate конфигурация

```bash
# /etc/logrotate.d/optfm-bot
/home/optfm/optfm-bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 optfm optfm
    postrotate
        systemctl reload optfm-bot
    endscript
}
```

### 8.3 Мониторинг с помощью cron

```bash
# Добавляем в crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * curl -f https://yourdomain.com/health > /dev/null 2>&1 || systemctl restart optfm-bot
```

## Этап 9: Безопасность

### 9.1 Firewall настройки

```bash
# Разрешаем только необходимые порты
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 9.2 Fail2Ban для защиты от атак

```bash
# /etc/fail2ban/jail.local
[nginx-webhook]
enabled = true
port = http,https
filter = nginx-webhook
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
```

### 9.3 Регулярное обновление

```bash
# Создаем скрипт обновления
cat > /home/optfm/update-bot.sh << 'EOF'
#!/bin/bash
cd /home/optfm/optfm-bot
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart optfm-bot
EOF

chmod +x /home/optfm/update-bot.sh
```

## Этап 10: Резервное копирование

### 10.1 Скрипт резервного копирования

```bash
#!/bin/bash
# /home/optfm/backup-bot.sh

BACKUP_DIR="/backup/optfm-bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Архивируем конфигурацию и логи
tar -czf $BACKUP_DIR/optfm-bot-$DATE.tar.gz \
    /home/optfm/optfm-bot/.env \
    /home/optfm/optfm-bot/logs/ \
    /etc/nginx/sites-available/optfm-bot \
    /etc/systemd/system/optfm-bot.service

# Удаляем старые бекапы (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 10.2 Автоматическое резервное копирование

```bash
# Добавляем в crontab
0 2 * * * /home/optfm/backup-bot.sh
```

## Troubleshooting

### Проблема: Webhook не получает сообщения

**Решение:**
1. Проверьте доступность URL извне:
   ```bash
   curl -X POST https://yourdomain.com/webhook/max/ \
        -H "Content-Type: application/json" \
        -d '{"test": "message"}'
   ```

2. Проверьте логи Nginx:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Проверьте статус webhook'а в MAX:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://max-api.chat/api/getWebhookInfo
   ```

### Проблема: Бот не отвечает на сообщения

**Решение:**
1. Проверьте логи приложения:
   ```bash
   sudo journalctl -u optfm-bot -f
   ```

2. Проверьте статус FAQ Manager:
   ```bash
   curl https://yourdomain.com/webhook/max/status
   ```

3. Протестируйте обработку сообщений:
   ```bash
   curl -X POST https://yourdomain.com/webhook/max/test \
        -H "Content-Type: application/json" \
        -d '{"text": "Тест", "user_name": "Test"}'
   ```

### Проблема: Высокая нагрузка

**Решение:**
1. Включите rate limiting в Nginx:
   ```nginx
   limit_req_zone $binary_remote_addr zone=webhook:10m rate=1r/s;
   
   location /webhook/max/ {
       limit_req zone=webhook burst=5;
       # ... остальная конфигурация
   }
   ```

2. Оптимизируйте обработку сообщений:
   ```python
   # Кэширование FAQ ответов
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_cached_faq_response(query: str) -> str:
       return faq_manager.search_faq(query)
   ```

## Заключение

После выполнения всех этапов у вас будет полностью развернутая интеграция OptFM AI Bot с MAX мессенджером, включающая:

- ✅ Безопасное развертывание с HTTPS
- ✅ Автоматический запуск через systemd
- ✅ Мониторинг и логирование
- ✅ Резервное копирование
- ✅ Защита от атак

Для поддержки и дальнейшего развития ведите документацию изменений и регулярно обновляйте систему.
