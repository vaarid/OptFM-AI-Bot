"""
Telegram Bot Module for OptFM AI Bot
"""
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from faq.enhanced_faq_manager import EnhancedFAQManager

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
        self.faq_manager = EnhancedFAQManager()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик команды /faq
        self.application.add_handler(CommandHandler("faq", self.faq_command))
        

        
        # Обработчик callback-запросов (для интерактивных кнопок)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
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
            f"👋 Здравствуйте, {user.first_name}!\n\n"
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
            "/faq - Показать FAQ с интерактивными кнопками\n\n"
            "**Как использовать:**\n"
            "• Напишите вопрос о продуктах OptFM\n"
            "• Используйте /faq для просмотра всех вопросов с кнопками\n"
            "• Нажмите на интересующий вопрос для получения ответа\n\n"
            "**Примеры вопросов:**\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?\n\n"

            "**Интерактивные FAQ:**\n"
            "Команда /faq покажет все вопросы в виде кнопок. Просто нажмите на интересующий вопрос!"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested help")
        
    async def faq_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /faq - показывает FAQ с интерактивными кнопками (пагинация по 10)
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        faq_list = self.faq_manager.get_all_faq()
        
        if not faq_list:
            await update.message.reply_text("К сожалению, база FAQ пуста.")
            return
        
        # Показываем первые 10 вопросов
        start_index = 0
        end_index = min(10, len(faq_list))
        current_faq_list = faq_list[start_index:end_index]
        
        # Создаем интерактивные кнопки для FAQ
        keyboard = []
        
        for faq in current_faq_list:
            # Создаем кнопку с текстом вопроса (улучшенное обрезание)
            button_text = faq['question']
            
            # Увеличиваем лимит и улучшаем обрезание
            if len(button_text) > 50:
                # Ищем последний пробел перед 50-м символом
                cut_point = button_text[:50].rfind(' ')
                if cut_point > 30:  # Если пробел найден не слишком близко к началу
                    button_text = button_text[:cut_point] + "..."
                else:
                    button_text = button_text[:47] + "..."
            
            button = InlineKeyboardButton(
                text=f"{faq['id']}. {button_text}",
                callback_data=f"faq_{faq['id']}"
            )
            
            # Добавляем по 1 кнопке в ряд для лучшей читаемости
            keyboard.append([button])
        
        # Добавляем кнопку "Показать ещё" если есть ещё вопросы
        if len(faq_list) > 10:
            keyboard.append([InlineKeyboardButton("📄 Показать ещё", callback_data="faq_show_more_10")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        faq_text = (
            "📚 **Часто задаваемые вопросы OptFM:**\n\n"
            "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
            f"Показано: **{len(current_faq_list)}** из **{len(faq_list)}** вопросов"
        )
        
        await update.message.reply_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested FAQ list with buttons (page 1)")
        
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик текстовых сообщений с поиском в FAQ
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user_message = update.message.text
        user = update.effective_user
        
        # Проверяем, является ли сообщение приветствием
        greeting_keywords = ['привет', 'здравствуй', 'добрый день', 'добрый вечер', 'доброе утро', 'hi', 'hello']
        is_greeting = any(greeting in user_message.lower() for greeting in greeting_keywords)
        
        # Проверяем, является ли сообщение прощанием
        farewell_keywords = ['пока', 'до свидания', 'до встречи', 'спасибо', 'благодарю', 'bye', 'goodbye', 'thanks']
        is_farewell = any(farewell in user_message.lower() for farewell in farewell_keywords)
        
        # Проверяем, является ли сообщение вопросом (содержит вопросительные слова)
        question_keywords = ['что', 'как', 'где', 'когда', 'почему', 'зачем', 'какие', 'какой', 'сколько', 'есть ли', 'можно ли']
        is_question = any(question in user_message.lower() for question in question_keywords) or user_message.strip().endswith('?')
        
        if is_greeting:
            # Приветствие - даем дружелюбный ответ
            response = (
                f"👋 Привет, {user.first_name}!\n\n"
                "Я бот компании OptFM. Могу помочь с информацией о наших продуктах и услугах.\n\n"
                "Задайте мне любой вопрос, например:\n"
                "• Какие товары вы продаете?\n"
                "• Как с вами связаться?\n"
                "• Какие условия доставки?\n"
                "• Есть ли у вас гарантия?\n\n"
                "Или используйте /help для получения справки."
            )
            logger.info(f"Приветствие от пользователя {user.id}: {user_message}")
        elif is_farewell:
            # Прощание - даем вежливый ответ
            response = (
                f"👋 До свидания, {user.first_name}!\n\n"
                "Спасибо за обращение к OptFM. Если у вас появятся вопросы, "
                "я всегда готов помочь!\n\n"
                "Удачного дня! 😊"
            )
            logger.info(f"Прощание от пользователя {user.id}: {user_message}")
        elif not is_question and len(user_message.split()) < 3:
            # Короткое сообщение без вопроса - предлагаем задать вопрос
            response = (
                f"🤔 {user.first_name}, я не совсем понял ваш запрос.\n\n"
                "Задайте мне вопрос о продуктах OptFM, например:\n"
                "• Какие товары вы продаете?\n"
                "• Как с вами связаться?\n"
                "• Какие условия доставки?\n"
                "• Есть ли у вас гарантия?\n\n"
                "Или используйте /help для получения справки."
            )
            logger.info(f"Короткое сообщение от пользователя {user.id}: {user_message}")
        else:
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
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /stats - показывает статистику FAQ
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        stats = self.faq_manager.get_statistics()
        
        stats_message = (
            f"📊 **Статистика FAQ OptFM:**\n\n"
            f"• Всего вопросов: {stats['total_faq']}\n"
            f"• Всего ключевых слов: {stats['total_keywords']}\n"
            f"• Среднее количество ключевых слов на вопрос: {stats['average_keywords_per_faq']}\n"
            f"• Размер поискового индекса: {stats['search_index_size']}\n\n"
            f"Используйте /faq для просмотра всех вопросов"
        )
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} requested FAQ statistics")
    
    async def similar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /similar - поиск похожих вопросов
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        if not context.args:
            await update.message.reply_text(
                "🔍 **Поиск похожих вопросов**\n\n"
                "Использование: `/similar ваш вопрос`\n\n"
                "Пример: `/similar как доставить товар`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        similar_questions = self.faq_manager.search_similar_questions(query, limit=3)
        
        if not similar_questions:
            await update.message.reply_text(
                f"❌ Похожих вопросов для \"{query}\" не найдено.\n\n"
                "Попробуйте переформулировать запрос или используйте /faq для просмотра всех вопросов."
            )
            return
        
        similar_message = f"🔍 **Похожие вопросы для \"{query}\":**\n\n"
        
        for i, faq in enumerate(similar_questions, 1):
            similar_message += f"{i}. **{faq['question']}**\n"
        
        similar_message += "\nЗадайте любой из этих вопросов для получения ответа!"
        
        await update.message.reply_text(similar_message, parse_mode='Markdown')
        logger.info(f"User {update.effective_user.id} searched for similar questions: {query}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик нажатий на интерактивные кнопки
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        query = update.callback_query
        await query.answer()  # Убираем "часики" у кнопки
        
        user = update.effective_user
        callback_data = query.data
        
        logger.info(f"Callback от пользователя {user.id}: {callback_data}")
        
        if callback_data == "faq_back_to_list":
            # Возврат к списку FAQ (первая страница)
            faq_list = self.faq_manager.get_all_faq()
            
            # Показываем первые 10 вопросов
            start_index = 0
            end_index = min(10, len(faq_list))
            current_faq_list = faq_list[start_index:end_index]
            
            # Создаем интерактивные кнопки для FAQ
            keyboard = []
            
            for faq in current_faq_list:
                # Создаем кнопку с текстом вопроса (улучшенное обрезание)
                button_text = faq['question']
                
                # Увеличиваем лимит и улучшаем обрезание
                if len(button_text) > 50:
                    # Ищем последний пробел перед 50-м символом
                    cut_point = button_text[:50].rfind(' ')
                    if cut_point > 30:  # Если пробел найден не слишком близко к началу
                        button_text = button_text[:cut_point] + "..."
                    else:
                        button_text = button_text[:47] + "..."
                
                button = InlineKeyboardButton(
                    text=f"{faq['id']}. {button_text}",
                    callback_data=f"faq_{faq['id']}"
                )
                
                # Добавляем по 1 кнопке в ряд для лучшей читаемости
                keyboard.append([button])
            
            # Добавляем кнопку "Показать ещё" если есть ещё вопросы
            if len(faq_list) > 10:
                keyboard.append([InlineKeyboardButton("📄 Показать ещё", callback_data="faq_show_more_10")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            faq_text = (
                "📚 **Часто задаваемые вопросы OptFM:**\n\n"
                "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                f"Показано: **{len(current_faq_list)}** из **{len(faq_list)}** вопросов"
            )
            
            await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
            logger.info(f"User {user.id} returned to FAQ list (page 1)")
            
        elif callback_data.startswith("faq_"):
            faq_id = callback_data[4:]  # Убираем "faq_" из начала
            
            # Проверяем, что это не команда
            if faq_id.startswith("/"):
                await query.edit_message_text("❌ Неверный запрос.")
                logger.warning(f"User {user.id} sent invalid callback: {callback_data}")
                return
            
            if faq_id == "show_more_10":
                # Показать следующие 10 вопросов
                faq_list = self.faq_manager.get_all_faq()
                
                # Показываем следующие 10 вопросов (с 11-го по 20-й)
                start_index = 10
                end_index = min(20, len(faq_list))
                current_faq_list = faq_list[start_index:end_index]
                
                # Создаем интерактивные кнопки для FAQ
                keyboard = []
                
                for faq in current_faq_list:
                    # Создаем кнопку с текстом вопроса (улучшенное обрезание)
                    button_text = faq['question']
                    
                    # Увеличиваем лимит и улучшаем обрезание
                    if len(button_text) > 50:
                        # Ищем последний пробел перед 50-м символом
                        cut_point = button_text[:50].rfind(' ')
                        if cut_point > 30:  # Если пробел найден не слишком близко к началу
                            button_text = button_text[:cut_point] + "..."
                        else:
                            button_text = button_text[:47] + "..."
                    
                    button = InlineKeyboardButton(
                        text=f"{faq['id']}. {button_text}",
                        callback_data=f"faq_{faq['id']}"
                    )
                    
                    # Добавляем по 1 кнопке в ряд для лучшей читаемости
                    keyboard.append([button])
                
                # Добавляем кнопки навигации
                keyboard.append([InlineKeyboardButton("🔙 Назад к началу", callback_data="faq_back_to_list")])
                keyboard.append([InlineKeyboardButton("⬅️ Предыдущая страница", callback_data="faq_back_to_list")])
                
                # Добавляем кнопку "Показать ещё" если есть ещё вопросы
                if len(faq_list) > 20:
                    keyboard.append([InlineKeyboardButton("📄 Показать ещё", callback_data="faq_show_more_20")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                faq_text = (
                    "📚 **Часто задаваемые вопросы OptFM (страница 2):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} requested FAQ page 2")
                
            elif faq_id == "show_more_20":
                # Показать следующие 10 вопросов (с 21-го по 30-й)
                faq_list = self.faq_manager.get_all_faq()
                
                start_index = 20
                end_index = min(30, len(faq_list))
                current_faq_list = faq_list[start_index:end_index]
                
                # Создаем интерактивные кнопки для FAQ
                keyboard = []
                
                for faq in current_faq_list:
                    # Создаем кнопку с текстом вопроса (улучшенное обрезание)
                    button_text = faq['question']
                    
                    # Увеличиваем лимит и улучшаем обрезание
                    if len(button_text) > 50:
                        # Ищем последний пробел перед 50-м символом
                        cut_point = button_text[:50].rfind(' ')
                        if cut_point > 30:  # Если пробел найден не слишком близко к началу
                            button_text = button_text[:cut_point] + "..."
                        else:
                            button_text = button_text[:47] + "..."
                    
                    button = InlineKeyboardButton(
                        text=f"{faq['id']}. {button_text}",
                        callback_data=f"faq_{faq['id']}"
                    )
                    
                    # Добавляем по 1 кнопке в ряд для лучшей читаемости
                    keyboard.append([button])
                
                # Добавляем кнопки навигации
                keyboard.append([InlineKeyboardButton("🔙 Назад к началу", callback_data="faq_back_to_list")])
                keyboard.append([InlineKeyboardButton("⬅️ Предыдущая страница", callback_data="faq_show_more_10")])
                
                # Добавляем кнопку "Показать ещё" если есть ещё вопросы
                if len(faq_list) > 30:
                    keyboard.append([InlineKeyboardButton("📄 Показать ещё", callback_data="faq_show_more_30")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                faq_text = (
                    "📚 **Часто задаваемые вопросы OptFM (страница 3):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} requested FAQ page 3")
                
            elif faq_id == "show_more_30":
                # Показать оставшиеся вопросы (с 31-го)
                faq_list = self.faq_manager.get_all_faq()
                
                start_index = 30
                end_index = len(faq_list)
                current_faq_list = faq_list[start_index:end_index]
                
                # Создаем интерактивные кнопки для FAQ
                keyboard = []
                
                for faq in current_faq_list:
                    # Создаем кнопку с текстом вопроса (улучшенное обрезание)
                    button_text = faq['question']
                    
                    # Увеличиваем лимит и улучшаем обрезание
                    if len(button_text) > 50:
                        # Ищем последний пробел перед 50-м символом
                        cut_point = button_text[:50].rfind(' ')
                        if cut_point > 30:  # Если пробел найден не слишком близко к началу
                            button_text = button_text[:cut_point] + "..."
                        else:
                            button_text = button_text[:47] + "..."
                    
                    button = InlineKeyboardButton(
                        text=f"{faq['id']}. {button_text}",
                        callback_data=f"faq_{faq['id']}"
                    )
                    
                    # Добавляем по 1 кнопке в ряд для лучшей читаемости
                    keyboard.append([button])
                
                # Добавляем кнопки навигации
                keyboard.append([InlineKeyboardButton("🔙 Назад к началу", callback_data="faq_back_to_list")])
                keyboard.append([InlineKeyboardButton("⬅️ Предыдущая страница", callback_data="faq_show_more_20")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                faq_text = (
                    "📚 **Часто задаваемые вопросы OptFM (последняя страница):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} requested FAQ final page")
                
            else:
                # Показать конкретный FAQ
                try:
                    faq_id = int(faq_id)
                    faq = self.faq_manager.get_faq_by_id(faq_id)
                    
                    if faq:
                        # Создаем кнопки для навигации
                        keyboard = []
                        
                        # Кнопка "Назад к списку"
                        keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="faq_back_to_list")])
                        
                        # Кнопка "Следующий вопрос" (если есть)
                        if faq_id < len(self.faq_manager.get_all_faq()):
                            keyboard.append([InlineKeyboardButton("➡️ Следующий вопрос", callback_data=f"faq_{faq_id + 1}")])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        answer_text = (
                            f"🤖 **{faq['question']}**\n\n"
                            f"{faq['answer']}\n\n"
                            f"Если у вас есть дополнительные вопросы, не стесняйтесь спрашивать!"
                        )
                        
                        await query.edit_message_text(answer_text, parse_mode='Markdown', reply_markup=reply_markup)
                        logger.info(f"User {user.id} viewed FAQ {faq_id}")
                        
                    else:
                        await query.edit_message_text("❌ Вопрос не найден.")
                        logger.warning(f"User {user.id} requested non-existent FAQ {faq_id}")
                        
                except ValueError:
                    await query.edit_message_text("❌ Неверный ID вопроса.")
                    logger.warning(f"User {user.id} requested invalid FAQ ID: {faq_id}")
        
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
