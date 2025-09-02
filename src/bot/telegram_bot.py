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
from forms.request_form import RequestFormManager
from db.database import init_database, get_db
from db.repository import UserRepository, RequestRepository, DialogRepository
from notifications.manager_notifier import ManagerNotifier, NotificationConfig

logger = logging.getLogger(__name__)

class OptFMBot:
    """Основной класс Telegram бота для OptFM"""
    
    def __init__(self, token: str, database_url: str = None):
        """
        Инициализация бота
        
        Args:
            token: Telegram Bot Token
            database_url: URL базы данных
        """
        self.token = token
        self.application = Application.builder().token(token).build()
        self.faq_manager = EnhancedFAQManager()
        
        # Инициализация базы данных
        self.db_manager = init_database(database_url)
        
        # Инициализация форм заявок
        self.form_manager = RequestFormManager()
        
        # Инициализация уведомлений
        notification_config = NotificationConfig.get_default_config()
        self.notifier = ManagerNotifier(notification_config)
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик команды /faq
        self.application.add_handler(CommandHandler("faq", self.faq_command))
        
        # Обработчик команды /request - создание заявки
        self.application.add_handler(CommandHandler("request", self.request_command))
        
        # Обработчик команды /cancel - отмена заявки
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Обработчик команды /my_requests - просмотр своих заявок
        self.application.add_handler(CommandHandler("my_requests", self.my_requests_command))
        
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
            "🤖 OptFM AI Bot - Справка\n\n"
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/faq - Показать FAQ с интерактивными кнопками\n"
            "/request - Создать заявку менеджеру\n"
            "/my_requests - Просмотр ваших заявок\n"
            "/cancel - Отменить заполнение заявки\n\n"
            "Как использовать:\n"
            "• Напишите вопрос о продуктах OptFM\n"
            "• Используйте /faq для просмотра всех вопросов с кнопками\n"
            "• Если ответ не найден, используйте /request для создания заявки\n\n"
            "Примеры вопросов:\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?\n\n"
            "Создание заявки:\n"
            "Используйте /request для создания заявки менеджеру. "
            "Бот проведет вас через простую форму сбора контактных данных.\n\n"
            "Интерактивные FAQ:\n"
            "Команда /faq покажет все вопросы в виде кнопок. Просто нажмите на интересующий вопрос!"
        )
        
        await update.message.reply_text(help_message)
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
        Обработчик всех текстовых сообщений (поиск в FAQ и формы заявок)
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        user_message = update.message.text.strip()
        
        logger.info(f"Сообщение от пользователя {user.id}: {user_message}")
        
        # Проверяем, заполняет ли пользователь форму заявки
        if self.form_manager.is_user_filling_form(user.id):
            await self._handle_form_input(update, context)
            return
        
        # Проверяем, является ли сообщение приветствием
        greetings = ["привет", "здравствуйте", "добрый день", "добрый вечер", "доброе утро", "hi", "hello"]
        is_greeting = any(greeting in user_message.lower() for greeting in greetings)
        
        # Проверяем, является ли сообщение прощанием
        farewells = ["пока", "до свидания", "до встречи", "спасибо", "благодарю", "bye", "goodbye"]
        is_farewell = any(farewell in user_message.lower() for farewell in farewells)
        
        # Проверяем, является ли сообщение вопросом
        question_words = ["что", "как", "где", "когда", "почему", "зачем", "какой", "какая", "какие", "сколько", "?"]
        is_question = any(word in user_message.lower() for word in question_words) or user_message.endswith("?")
        
        if is_greeting:
            response = (
                f"👋 Привет, {user.first_name}! Рад вас видеть!\n\n"
                "Я бот компании OptFM и готов помочь вам с любыми вопросами о наших продуктах и услугах.\n\n"
                "Вы можете:\n"
                "• Задать мне любой вопрос\n"
                "• Использовать /faq для просмотра частых вопросов\n"
                "• Использовать /help для получения справки\n"
                "• Использовать /request для создания заявки менеджеру"
            )
            logger.info(f"Приветствие от пользователя {user.id}: {user_message}")
        elif is_farewell:
            response = (
                f"👋 До свидания, {user.first_name}! Было приятно пообщаться!\n\n"
                "Если у вас появятся вопросы, обращайтесь в любое время. Удачи!"
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
                    "Используйте команду /request для создания заявки или попробуйте переформулировать вопрос."
                )
                logger.info(f"FAQ ответ не найден для пользователя {user.id}: {user_message[:50]}...")
        
        # Сохраняем диалог в базу данных
        await self._save_dialog(user.id, user_message, response, is_question)
        
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
    
    # === Методы для работы с заявками ===
    
    async def request_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /request - создание заявки
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        
        # Проверяем, не заполняет ли пользователь уже форму
        if self.form_manager.is_user_filling_form(user.id):
            await update.message.reply_text(
                "📝 Вы уже заполняете заявку. Продолжайте или используйте /cancel для отмены."
            )
            return
        
        # Начинаем заполнение формы
        message = self.form_manager.start_form(user.id)
        await update.message.reply_text(message)
        
        logger.info(f"User {user.id} started request form")
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /cancel - отмена заявки
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        
        if self.form_manager.is_user_filling_form(user.id):
            message = self.form_manager.cancel_form(user.id)
            await update.message.reply_text(message)
            logger.info(f"User {user.id} cancelled request form")
        else:
            await update.message.reply_text("❌ Вы не заполняете заявку в данный момент.")
    
    async def my_requests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /my_requests - просмотр своих заявок
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        
        try:
            # Получаем пользователя из базы данных
            session = self.db_manager.get_session_sync()
            user_repo = UserRepository(session)
            request_repo = RequestRepository(session)
            
            db_user = user_repo.get_by_telegram_id(user.id)
            
            if not db_user:
                await update.message.reply_text(
                    "❌ У вас пока нет заявок. Используйте /request для создания первой заявки!"
                )
                return
            
            # Получаем заявки пользователя
            requests = request_repo.get_user_requests(db_user.id)
            
            if not requests:
                await update.message.reply_text(
                    "📝 У вас пока нет заявок. Используйте /request для создания первой заявки!"
                )
                return
            
            # Формируем сообщение со списком заявок
            message = f"📋 **Ваши заявки ({len(requests)}):**\n\n"
            
            for i, request in enumerate(requests, 1):
                status_emoji = {
                    "new": "🆕",
                    "in_progress": "⏳", 
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(request.status.value, "❓")
                
                message += (
                    f"{i}. {status_emoji} **{request.title}**\n"
                    f"   📅 {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"   📝 {request.description[:100]}{'...' if len(request.description) > 100 else ''}\n\n"
                )
            
            message += "Для создания новой заявки используйте /request"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info(f"User {user.id} viewed their requests ({len(requests)} requests)")
            
        except Exception as e:
            logger.error(f"Error getting user requests: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении заявок. Попробуйте позже.")
    
    async def _handle_form_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработка ввода в форме заявки
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        user_input = update.message.text.strip()
        
        # Обрабатываем ввод формы
        result = self.form_manager.process_input(user.id, user_input)
        
        await update.message.reply_text(result["message"])
        
        # Если форма завершена, сохраняем заявку
        if result.get("completed", False):
            await self._save_request(user, result["data"])
            # Очищаем форму
            self.form_manager.clear_form(user.id)
    
    async def _save_request(self, user, form_data: Dict[str, Any]):
        """
        Сохранение заявки в базу данных
        
        Args:
            user: Пользователь Telegram
            form_data: Данные формы
        """
        try:
            session = self.db_manager.get_session_sync()
            user_repo = UserRepository(session)
            request_repo = RequestRepository(session)
            
            # Получаем или создаем пользователя
            db_user = user_repo.get_by_telegram_id(user.id)
            if not db_user:
                db_user = user_repo.create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            
            # Обновляем контактные данные пользователя
            user_repo.update_user_contacts(
                db_user.id,
                phone=form_data.get("phone"),
                email=form_data.get("email")
            )
            
            # Создаем заявку
            title = form_data.get("description", "Новая заявка")[:200]
            description = form_data.get("description", "")
            
            request = request_repo.create_request(
                user_id=db_user.id,
                title=title,
                description=description
            )
            
            # Уведомляем менеджеров
            request_data = {
                "id": request.id,
                "title": request.title,
                "description": request.description,
                "created_at": request.created_at
            }
            
            user_data = {
                "name": form_data.get("name"),
                "phone": form_data.get("phone"),
                "email": form_data.get("email"),
                "telegram_id": user.id
            }
            
            self.notifier.notify_new_request(request_data, user_data)
            
            logger.info(f"Request saved successfully: {request.id} for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error saving request: {e}")
    
    async def _save_dialog(self, user_id: int, message: str, response: str, is_question: bool = True):
        """
        Сохранение диалога в базу данных
        
        Args:
            user_id: ID пользователя
            message: Сообщение пользователя
            response: Ответ бота
            is_question: Является ли сообщение вопросом
        """
        try:
            session = self.db_manager.get_session_sync()
            user_repo = UserRepository(session)
            dialog_repo = DialogRepository(session)
            
            # Получаем пользователя
            db_user = user_repo.get_by_telegram_id(user_id)
            if db_user:
                dialog_repo.add_dialog(db_user.id, message, response, is_question)
                
        except Exception as e:
            logger.error(f"Error saving dialog: {e}")
