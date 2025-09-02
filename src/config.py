"""
Configuration module for OptFM AI Bot
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Класс конфигурации приложения"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # FastAPI
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    API_LOG_FILE: str = os.getenv("API_LOG_FILE", "logs/api.log")
    
    # База данных
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Уведомления менеджеров
    NOTIFICATIONS_ENABLED: bool = os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true"
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "bot@optfm.ru")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Валидация обязательных параметров конфигурации
        
        Returns:
            bool: True если все обязательные параметры заданы
        """
        required_fields = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
        ]
        
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
        """Вывод текущей конфигурации (без секретных данных)"""
        print("Конфигурация OptFM AI Bot:")
        print(f"  • HOST: {cls.HOST}")
        print(f"  • PORT: {cls.PORT}")
        print(f"  • LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"  • TELEGRAM_BOT_TOKEN: {'УСТАНОВЛЕН' if cls.TELEGRAM_BOT_TOKEN else 'ОТСУТСТВУЕТ'}")
        print(f"  • DATABASE_URL: {'УСТАНОВЛЕН' if cls.DATABASE_URL else 'ОТСУТСТВУЕТ'}")
