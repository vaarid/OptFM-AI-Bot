"""
MAX Messenger Configuration for OptFM AI Bot

Расширение конфигурации для поддержки MAX мессенджера.
Этот файл показывает, какие изменения нужно внести в основной config.py
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class MaxConfig:
    """Конфигурация для MAX мессенджера"""
    
    # MAX Messenger API
    MAX_API_KEY: str = os.getenv("MAX_API_KEY", "")
    MAX_BASE_URL: str = os.getenv("MAX_BASE_URL", "https://max-api.chat/api")
    MAX_WEBHOOK_URL: str = os.getenv("MAX_WEBHOOK_URL", "")
    MAX_WEBHOOK_SECRET: str = os.getenv("MAX_WEBHOOK_SECRET", "")
    
    # Опциональные настройки
    MAX_TIMEOUT: int = int(os.getenv("MAX_TIMEOUT", "10"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    MAX_RATE_LIMIT: int = int(os.getenv("MAX_RATE_LIMIT", "30"))  # сообщений в минуту
    
    @classmethod
    def validate_max_config(cls) -> tuple[bool, list[str]]:
        """
        Валидация конфигурации MAX
        
        Returns:
            tuple: (is_valid, missing_fields)
        """
        required_fields = [
            ("MAX_API_KEY", cls.MAX_API_KEY),
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        return len(missing_fields) == 0, missing_fields
    
    @classmethod
    def is_max_enabled(cls) -> bool:
        """Проверка, включена ли поддержка MAX"""
        return bool(cls.MAX_API_KEY)
    
    @classmethod
    def print_max_config(cls):
        """Вывод конфигурации MAX (без секретных данных)"""
        print("Конфигурация MAX Messenger:")
        print(f"  • MAX_API_KEY: {'УСТАНОВЛЕН' if cls.MAX_API_KEY else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_BASE_URL: {cls.MAX_BASE_URL}")
        print(f"  • MAX_WEBHOOK_URL: {'УСТАНОВЛЕН' if cls.MAX_WEBHOOK_URL else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_WEBHOOK_SECRET: {'УСТАНОВЛЕН' if cls.MAX_WEBHOOK_SECRET else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_TIMEOUT: {cls.MAX_TIMEOUT}s")
        print(f"  • MAX_RETRY_ATTEMPTS: {cls.MAX_RETRY_ATTEMPTS}")
        print(f"  • MAX_RATE_LIMIT: {cls.MAX_RATE_LIMIT} msg/min")
        print(f"  • MAX_ENABLED: {'ДА' if cls.is_max_enabled() else 'НЕТ'}")

# Расширение основного класса Config
class ExtendedConfig:
    """
    Пример расширения основного Config класса для поддержки MAX
    
    В реальной интеграции эти поля нужно добавить в основной Config класс в src/config.py
    """
    
    # Существующие поля из основного Config
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    API_LOG_FILE: str = os.getenv("API_LOG_FILE", "logs/api.log")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Новые поля для MAX
    MAX_API_KEY: str = os.getenv("MAX_API_KEY", "")
    MAX_BASE_URL: str = os.getenv("MAX_BASE_URL", "https://max-api.chat/api")
    MAX_WEBHOOK_URL: str = os.getenv("MAX_WEBHOOK_URL", "")
    MAX_WEBHOOK_SECRET: str = os.getenv("MAX_WEBHOOK_SECRET", "")
    MAX_TIMEOUT: int = int(os.getenv("MAX_TIMEOUT", "10"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    MAX_RATE_LIMIT: int = int(os.getenv("MAX_RATE_LIMIT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Расширенная валидация конфигурации
        
        Returns:
            bool: True если все обязательные параметры заданы
        """
        # Обязательные поля для Telegram
        required_fields = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
        ]
        
        # MAX поля обязательны только если указан API ключ
        if cls.MAX_API_KEY:
            required_fields.extend([
                ("MAX_API_KEY", cls.MAX_API_KEY),
            ])
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            print(f"ОТСУТСТВУЮТ обязательные переменные окружения: {', '.join(missing_fields)}")
            print("Пожалуйста, создайте файл .env и добавьте необходимые переменные")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Расширенный вывод конфигурации"""
        print("Конфигурация OptFM AI Bot (расширенная):")
        print(f"  • HOST: {cls.HOST}")
        print(f"  • PORT: {cls.PORT}")
        print(f"  • LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"  • TELEGRAM_BOT_TOKEN: {'УСТАНОВЛЕН' if cls.TELEGRAM_BOT_TOKEN else 'ОТСУТСТВУЕТ'}")
        print(f"  • DATABASE_URL: {'УСТАНОВЛЕН' if cls.DATABASE_URL else 'ОТСУТСТВУЕТ'}")
        print()
        print("MAX Messenger:")
        print(f"  • MAX_API_KEY: {'УСТАНОВЛЕН' if cls.MAX_API_KEY else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_BASE_URL: {cls.MAX_BASE_URL}")
        print(f"  • MAX_WEBHOOK_URL: {'УСТАНОВЛЕН' if cls.MAX_WEBHOOK_URL else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_WEBHOOK_SECRET: {'УСТАНОВЛЕН' if cls.MAX_WEBHOOK_SECRET else 'ОТСУТСТВУЕТ'}")
        print(f"  • MAX_ENABLED: {'ДА' if cls.MAX_API_KEY else 'НЕТ'}")

# Вспомогательные функции для работы с конфигурацией
def get_max_config() -> dict:
    """
    Получение всех настроек MAX в виде словаря
    
    Returns:
        dict: Конфигурация MAX
    """
    return {
        "api_key": MaxConfig.MAX_API_KEY,
        "base_url": MaxConfig.MAX_BASE_URL,
        "webhook_url": MaxConfig.MAX_WEBHOOK_URL,
        "webhook_secret": MaxConfig.MAX_WEBHOOK_SECRET,
        "timeout": MaxConfig.MAX_TIMEOUT,
        "retry_attempts": MaxConfig.MAX_RETRY_ATTEMPTS,
        "rate_limit": MaxConfig.MAX_RATE_LIMIT,
        "enabled": MaxConfig.is_max_enabled()
    }

def validate_max_webhook_url(url: str) -> bool:
    """
    Валидация URL webhook'а
    
    Args:
        url: URL для проверки
        
    Returns:
        bool: True если URL валидный
    """
    if not url:
        return False
    
    # Базовая проверка URL
    return (
        url.startswith(("http://", "https://")) and
        "/webhook/max" in url and
        len(url) > 20
    )

def get_webhook_setup_command() -> str:
    """
    Генерация команды для настройки webhook'а
    
    Returns:
        str: Команда curl для настройки webhook'а
    """
    config = get_max_config()
    
    if not config["enabled"]:
        return "# MAX не настроен - отсутствует API ключ"
    
    curl_command = f'''curl -X POST "{config["base_url"]}/setWebhook" \\
  -H "Authorization: Bearer {config["api_key"]}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "url": "{config["webhook_url"]}"'''
    
    if config["webhook_secret"]:
        curl_command += f''',
    "secret_token": "{config["webhook_secret"]}"'''
    
    curl_command += '''
  }}'"""
    
    return curl_command

# Пример использования
if __name__ == "__main__":
    print("=== Тест конфигурации MAX ===")
    
    # Проверка конфигурации
    is_valid, missing = MaxConfig.validate_max_config()
    print(f"Конфигурация валидна: {is_valid}")
    if not is_valid:
        print(f"Отсутствующие поля: {missing}")
    
    print()
    
    # Вывод конфигурации
    MaxConfig.print_max_config()
    
    print()
    
    # Пример команды настройки webhook'а
    print("=== Команда настройки webhook'а ===")
    print(get_webhook_setup_command())
