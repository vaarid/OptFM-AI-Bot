"""
Telegram Bot Module for OptFM AI Bot
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from faq.faq_manager import FAQManager

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
        self.faq_manager = FAQManager()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик команды /faq
        self.application.add_handler(CommandHandler("faq", self.faq_command))
        
        # Обработчик всех текстовых сообщений (поиск в FAQ)
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
            "/help - Показать эту справку\n"
            "/faq - Показать список часто задаваемых вопросов\n\n"
            "**Как использовать:**\n"
            "Просто напишите ваш вопрос о продуктах OptFM, и я найду ответ в базе знаний!\n\n"
            "**Примеры вопросов:**\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?\n"
            "• Есть ли доставка?\n"
            "• Какие гарантии?"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested help")
        
    async def faq_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /faq
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        faq_list = self.faq_manager.get_all_faq()
        
        if not faq_list:
            await update.message.reply_text("К сожалению, база FAQ пуста.")
            return
        
        # Формируем список FAQ
        faq_text = "📚 **Часто задаваемые вопросы OptFM:**\n\n"
        
        for faq in faq_list:
            faq_text += f"**{faq['id']}. {faq['question']}**\n"
        
        faq_text += "\nПросто напишите ваш вопрос, и я постараюсь найти ответ!"
        
        await update.message.reply_text(faq_text, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested FAQ list")
        
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик текстовых сообщений с поиском в FAQ
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user_message = update.message.text
        user = update.effective_user
        
        # Поиск ответа в FAQ
        faq_answer = self.faq_manager.search_faq(user_message)
        
        if faq_answer:
            # Найден ответ в FAQ
            response = f"🤖 {faq_answer['answer']}\n\nЕсли у вас есть дополнительные вопросы, не стесняйтесь спрашивать!"
            logger.info(f"FAQ ответ для пользователя {user.id}: {faq_answer['id']}")
        else:
            # Ответ не найден - предлагаем оставить заявку
            response = (
                f"📝 Спасибо за ваш вопрос: \"{user_message}\"\n\n"
                "К сожалению, я не нашел точного ответа в базе знаний. "
                "Для получения подробной информации оставьте заявку, и наш менеджер свяжется с вами.\n\n"
                "Или попробуйте переформулировать вопрос. Например:\n"
                "• Какие у вас есть продукты?\n"
                "• Как с вами связаться?\n"
                "• Какие цены?"
            )
            logger.info(f"FAQ ответ не найден для пользователя {user.id}: {user_message[:50]}...")
        
        await update.message.reply_text(response)
        
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
