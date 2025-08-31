"""
Telegram Bot Module for OptFM AI Bot
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

class OptFMBot:
    """Основной класс Telegram бота для OptFM"""
    
    def __init__(self, token: str):
        """
        Инициализация бота
        
        Args:
            token: Telegram Bot Token
        """
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик всех текстовых сообщений (эхо-функция)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        welcome_message = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я бот компании OptFM. Могу помочь с информацией о наших продуктах и услугах.\n\n"
            "Просто напишите ваш вопрос, и я постараюсь на него ответить.\n\n"
            "Используйте /help для получения справки."
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /help
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        help_message = (
            "🤖 **OptFM AI Bot - Справка**\n\n"
            "**Доступные команды:**\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n\n"
            "**Как использовать:**\n"
            "Просто напишите ваш вопрос о продуктах OptFM, и я постараюсь помочь!\n\n"
            "Например:\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested help")
        
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Эхо-обработчик для всех текстовых сообщений
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user_message = update.message.text
        user = update.effective_user
        
        # Простая эхо-функция для MVP
        echo_response = f"📝 Вы написали: {user_message}\n\nЭто эхо-ответ. В следующих итерациях здесь будет интеллектуальная обработка."
        
        await update.message.reply_text(echo_response)
        logger.info(f"Echo response to user {user.id}: {user_message[:50]}...")
        
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Starting Telegram bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
    async def stop_polling(self):
        """Остановка бота"""
        logger.info("Stopping Telegram bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
