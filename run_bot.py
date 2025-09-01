#!/usr/bin/env python3
"""
Скрипт запуска Fashion Mobile AI Bot
"""
import asyncio
import logging
import os
import sys

# Добавляем src в путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from bot.telegram_bot import FashionMobileBot

# Настройка основного логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Настройка отдельного логгера для API вызовов
api_logger = logging.getLogger('httpx')
api_logger.setLevel(logging.INFO)
api_handler = logging.FileHandler(Config.API_LOG_FILE, encoding='utf-8')
api_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.propagate = False  # Не дублировать в основной лог

logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем конфигурацию
        if not Config.validate():
            logger.error("Ошибка конфигурации. Проверьте переменные окружения.")
            return
        
        # Выводим конфигурацию
        Config.print_config()
        
        # Создаем и запускаем бота
        logger.info("Запуск Fashion Mobile AI Bot...")
        bot = FashionMobileBot(Config.TELEGRAM_BOT_TOKEN)
        
        # Запускаем бота
        await bot.start_polling()
        
        # Держим бота запущенным
        logger.info("Бот успешно запущен и работает")
        await asyncio.Event().wait()  # Бесконечное ожидание
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        # Останавливаем бота
        if 'bot' in locals():
            await bot.stop_polling()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
