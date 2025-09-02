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
from rag.product_rag_manager import ProductRAGManager

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
        
        # Инициализируем RAG менеджер для поиска товаров
        try:
            self.rag_manager = ProductRAGManager()
            logger.info("RAG менеджер успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации RAG менеджера: {e}")
            self.rag_manager = None
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик команды /faq
        self.application.add_handler(CommandHandler("faq", self.faq_command))
        
        # Обработчик команды /search для поиска товаров
        self.application.add_handler(CommandHandler("search", self.search_command))
        
        # Обработчик команды /categories для просмотра категорий
        self.application.add_handler(CommandHandler("categories", self.categories_command))
        
        # Обработчик команды /manufacturers для просмотра производителей
        self.application.add_handler(CommandHandler("manufacturers", self.manufacturers_command))
        
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
            f"Здравствуйте, {user.first_name}!\n\n"
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
            "/faq - Показать FAQ с интерактивными кнопками\n"
            "/search - Интерактивный поиск товаров\n"
            "/categories - Просмотр категорий товаров\n"
            "/manufacturers - Просмотр производителей техники\n\n"
            "**Как использовать:**\n"
            "• Напишите вопрос о продуктах OptFM\n"
            "• Используйте /faq для просмотра всех вопросов с кнопками\n"
            "• Используйте /search для интерактивного поиска товаров\n"
            "• Просто напишите название товара или производителя для поиска\n"
            "• Нажмите на интересующий вопрос для получения ответа\n\n"
            "**Поиск товаров:**\n"
            "• Нажмите /search и введите запрос\n"
            "• Или просто напишите: Samsung, iPhone, FM модулятор\n"
            "• Используйте интерактивные кнопки для навигации\n\n"
            "**Примеры запросов:**\n"
            "• Samsung\n"
            "• iPhone\n"
            "• FM модулятор\n"
            "• защитное стекло\n"
            "• наушники\n"
            "• зарядка\n\n"
            "**Примеры вопросов:**\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?\n\n"
            "**Интерактивные возможности:**\n"
            "Все функции доступны через удобные кнопки!"
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
        Обработчик текстовых сообщений с поиском в FAQ и товарах
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user_message = update.message.text
        user = update.effective_user
        
        # Проверяем, находится ли пользователь в режиме поиска
        if context.user_data.get('search_mode', False):
            # Пользователь в режиме поиска - выполняем поиск товаров
            await self._perform_search(update, user_message)
            # Сбрасываем режим поиска
            context.user_data['search_mode'] = False
            return
        
        # Проверяем, является ли сообщение приветствием
        greeting_keywords = ['здравствуйте', 'здравствуй', 'добрый день', 'добрый вечер', 'доброе утро', 'hi', 'hello']
        is_greeting = any(greeting in user_message.lower() for greeting in greeting_keywords)
        
        # Проверяем, является ли сообщение прощанием
        farewell_keywords = ['пока', 'до свидания', 'до встречи', 'спасибо', 'благодарю', 'bye', 'goodbye', 'thanks']
        is_farewell = any(farewell in user_message.lower() for farewell in farewell_keywords)
        
        # Проверяем, является ли сообщение вопросом (содержит вопросительные слова)
        question_keywords = ['что', 'как', 'где', 'когда', 'почему', 'зачем', 'какие', 'какой', 'сколько', 'есть ли', 'можно ли']
        is_question = any(question in user_message.lower() for question in question_keywords) or user_message.strip().endswith('?')
        
        # Проверяем, может ли это быть поисковый запрос (короткое сообщение без вопроса)
        is_potential_search = len(user_message.split()) <= 3 and not is_question and not is_greeting and not is_farewell
        
        if is_greeting:
            # Приветствие - даем вежливый ответ
            response = (
                f"Здравствуйте, {user.first_name}!\n\n"
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
                f"До свидания, {user.first_name}!\n\n"
                "Спасибо за обращение к OptFM. Если у вас появятся вопросы, "
                "я всегда готов помочь!\n\n"
                "Удачного дня!"
            )
            logger.info(f"Прощание от пользователя {user.id}: {user_message}")
        elif is_potential_search:
            # Возможно, это поисковый запрос - предлагаем поиск
            response = (
                f"🔍 Возможно, вы ищете товар: \"{user_message}\"\n\n"
                "Хотите выполнить поиск в каталоге товаров?\n\n"
                "Или задайте мне вопрос о продуктах OptFM."
            )
            
            # Создаем кнопки для поиска
            keyboard = [
                [InlineKeyboardButton("🔍 Да, найти товар", callback_data=f"search_query_{user_message}")],
                [InlineKeyboardButton("📚 Задать вопрос", callback_data="ask_question")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup)
            logger.info(f"Потенциальный поисковый запрос от пользователя {user.id}: {user_message}")
            return
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
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /search - интерактивный поиск товаров в каталоге
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        if not self.rag_manager:
            await update.message.reply_text(
                "❌ Поиск товаров временно недоступен. Попробуйте позже."
            )
            return
        
        # Если есть аргументы, выполняем поиск
        if context.args:
            query = " ".join(context.args)
            await self._perform_search(update, query)
            return
        
        # Если аргументов нет, показываем интерактивное меню поиска
        search_message = (
            "🔍 **Поиск товаров OptFM**\n\n"
            "Введите наименование аксессуара или производителя, "
            "к которому хотите подобрать аксессуар.\n\n"
            "**Примеры запросов:**\n"
            "• Samsung\n"
            "• iPhone\n"
            "• FM модулятор\n"
            "• защитное стекло\n"
            "• наушники\n"
            "• зарядка"
        )
        
        # Создаем интерактивные кнопки
        keyboard = [
            [InlineKeyboardButton("📂 Просмотр категорий", callback_data="search_categories")],
            [InlineKeyboardButton("🏭 Просмотр производителей", callback_data="search_manufacturers")],
            [InlineKeyboardButton("🔍 Популярные запросы", callback_data="search_popular")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            search_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Сохраняем состояние поиска для пользователя
        context.user_data['search_mode'] = True
        logger.info(f"Пользователь {update.effective_user.id} запустил интерактивный поиск")
    
    async def _perform_search(self, update: Update, query: str):
        """
        Выполняет поиск товаров с улучшенной логикой
        
        Args:
            update: Объект обновления от Telegram
            query: Поисковый запрос
        """
        user = update.effective_user
        
        try:
            # Улучшенный поиск с приоритетом по производителям
            products = self.rag_manager.search_products(query, top_k=10)
            
            if not products:
                # Если товары не найдены, предлагаем альтернативы
                await self._handle_no_results(update, query)
                return
            
            # Анализируем результаты для улучшения UX
            categories_found = set()
            manufacturers_found = set()
            
            for product in products:
                if product.get('category'):
                    categories_found.add(product['category'])
                if product.get('device_manufacturers'):
                    manufacturers_found.update(product['device_manufacturers'])
            
            # Формируем умное сообщение с результатами
            search_message = f"🔍 **Поиск: \"{query}\"**\n\n"
            
            if len(products) <= 5:
                search_message += f"Найдено товаров: **{len(products)}**\n\n"
            else:
                search_message += f"Найдено товаров: **{len(products)}** (показано 5)\n\n"
            
            # Показываем только первые 5 товаров для лучшего UX
            display_products = products[:5]
            
            # Создаем кнопки для каждого товара
            keyboard = []
            
            for i, product in enumerate(display_products, 1):
                # Формируем текст кнопки
                button_text = f"{i}. {product['name'][:40]}"
                if len(product['name']) > 40:
                    button_text += "..."
                
                # Добавляем кнопку
                keyboard.append([InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"product_{product['id']}"
                )])
                
                # Добавляем краткую информацию в сообщение
                category = product.get('category', 'Не указана')
                brand = product.get('brand', 'Не указан')
                search_message += f"**{i}.** {product['name']}\n"
                search_message += f"    Категория: {category}\n"
                search_message += f"    Бренд: {brand}\n\n"
            
            # Добавляем умные кнопки на основе найденных категорий
            if categories_found:
                keyboard.append([InlineKeyboardButton("📂 Уточнить по категориям", callback_data="search_categories")])
            
            if manufacturers_found:
                keyboard.append([InlineKeyboardButton("🏭 Уточнить по производителям", callback_data="search_manufacturers")])
            
            # Добавляем кнопку "Новый поиск"
            keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                search_message, 
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )
            
            logger.info(f"Поиск товаров для пользователя {user.id}: найдено {len(products)} товаров для запроса '{query}'")
            
        except Exception as e:
            logger.error(f"Ошибка поиска товаров для пользователя {user.id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при поиске товаров. Попробуйте позже."
            )
    
    async def _handle_no_results(self, update: Update, query: str):
        """
        Обрабатывает случай, когда товары не найдены
        
        Args:
            update: Объект обновления от Telegram
            query: Поисковый запрос
        """
        user = update.effective_user
        
        # Пытаемся найти похожие товары или предложить альтернативы
        try:
            # Ищем товары с похожими названиями
            similar_products = self.rag_manager.search_products(query, top_k=3)
            
            if similar_products:
                no_results_message = (
                    f"🔍 **Поиск: \"{query}\"**\n\n"
                    "❌ Товары не найдены.\n\n"
                    "**Возможно, вы искали:**\n"
                )
                
                keyboard = []
                for i, product in enumerate(similar_products, 1):
                    no_results_message += f"• {product['name']}\n"
                    keyboard.append([InlineKeyboardButton(
                        text=f"Показать: {product['name'][:30]}...",
                        callback_data=f"product_{product['id']}"
                    )])
                
                keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_new")])
                keyboard.append([InlineKeyboardButton("📂 Просмотр категорий", callback_data="search_categories")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    no_results_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                # Если ничего не найдено, предлагаем общие категории
                await update.message.reply_text(
                    f"🔍 **Поиск: \"{query}\"**\n\n"
                    "❌ Товары не найдены.\n\n"
                    "**Попробуйте:**\n"
                    "• Переформулировать запрос\n"
                    "• Использовать более общие термины\n"
                    "• Просмотреть категории товаров\n\n"
                    "**Примеры запросов:**\n"
                    "• Samsung\n"
                    "• iPhone\n"
                    "• защитное стекло\n"
                    "• зарядка\n"
                    "• наушники"
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки отсутствующих результатов для пользователя {user.id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при поиске. Попробуйте позже."
            )
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /categories - показывает все категории товаров
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        if not self.rag_manager:
            await update.message.reply_text(
                "❌ Каталог товаров временно недоступен. Попробуйте позже."
            )
            return
        
        try:
            categories = self.rag_manager.get_categories()
            
            if not categories:
                await update.message.reply_text("❌ Категории товаров не найдены.")
                return
            
            # Показываем первые 20 категорий
            categories_message = "📂 **Категории товаров OptFM:**\n\n"
            
            keyboard = []
            for i, category in enumerate(categories[:20], 1):
                categories_message += f"**{i}.** {category}\n"
                
                # Создаем кнопку для категории
                button_text = category[:30] + "..." if len(category) > 30 else category
                keyboard.append([InlineKeyboardButton(
                    text=f"{i}. {button_text}",
                    callback_data=f"category_{category}"
                )])
            
            if len(categories) > 20:
                categories_message += f"\n... и еще **{len(categories) - 20}** категорий\n"
                keyboard.append([InlineKeyboardButton("📄 Показать еще", callback_data="categories_more")])
            
            keyboard.append([InlineKeyboardButton("🔍 Поиск товаров", callback_data="search_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                categories_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Пользователь {update.effective_user.id} запросил список категорий")
            
        except Exception as e:
            logger.error(f"Ошибка получения категорий для пользователя {update.effective_user.id}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении категорий.")
    
    async def manufacturers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /manufacturers - показывает всех производителей техники
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        if not self.rag_manager:
            await update.message.reply_text(
                "❌ Каталог товаров временно недоступен. Попробуйте позже."
            )
            return
        
        try:
            manufacturers = self.rag_manager.get_device_manufacturers()
            
            if not manufacturers:
                await update.message.reply_text("❌ Производители техники не найдены.")
                return
            
            # Показываем производителей
            manufacturers_message = "🏭 **Производители техники:**\n\n"
            
            keyboard = []
            for i, manufacturer in enumerate(manufacturers[:15], 1):
                manufacturers_message += f"**{i}.** {manufacturer}\n"
                
                # Создаем кнопку для производителя
                keyboard.append([InlineKeyboardButton(
                    text=f"{i}. {manufacturer}",
                    callback_data=f"manufacturer_{manufacturer}"
                )])
            
            if len(manufacturers) > 15:
                manufacturers_message += f"\n... и еще **{len(manufacturers) - 15}** производителей\n"
                keyboard.append([InlineKeyboardButton("📄 Показать еще", callback_data="manufacturers_more")])
            
            keyboard.append([InlineKeyboardButton("🔍 Поиск товаров", callback_data="search_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                manufacturers_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Пользователь {update.effective_user.id} запросил список производителей")
            
        except Exception as e:
            logger.error(f"Ошибка получения производителей для пользователя {update.effective_user.id}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении производителей.")
    
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
        
        # Обработка кнопок для товаров и поиска
        elif callback_data.startswith("product_"):
            # Показать детали товара
            product_id = callback_data[8:]  # Убираем "product_" из начала
            
            if not self.rag_manager:
                await query.edit_message_text("❌ Информация о товаре временно недоступна.")
                return
            
            try:
                # Получаем товар по точному ID
                product = self.rag_manager.get_product_by_id(product_id)
                
                if product:
                    
                    # Формируем детальную информацию о товаре
                    product_info = f"📦 **{product['name']}**\n\n"
                    
                    if product.get('category'):
                        product_info += f"**Категория:** {product['category']}\n"
                    
                    if product.get('subcategory'):
                        product_info += f"**Подкатегория:** {product['subcategory']}\n"
                    
                    if product.get('brand') and product['brand'] != 'Unknown':
                        product_info += f"**Бренд:** {product['brand']}\n"
                    
                    if product.get('device_manufacturers'):
                        manufacturers = ", ".join(product['device_manufacturers'])
                        product_info += f"**Совместимость:** {manufacturers}\n"
                    
                    if product.get('description'):
                        product_info += f"**Описание:** {product['description']}\n"
                    
                    product_info += f"\n**Цена:** {product.get('price', 'Уточняйте у менеджера')}\n\n"
                    product_info += "💬 Для заказа свяжитесь с менеджером!"
                    
                    # Создаем кнопки навигации
                    keyboard = [
                        [InlineKeyboardButton("🔍 Новый поиск", callback_data="search_new")],
                        [InlineKeyboardButton("📂 Категории", callback_data="search_categories")],
                        [InlineKeyboardButton("🏭 Производители", callback_data="search_manufacturers")]
                    ]
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(product_info, parse_mode='Markdown', reply_markup=reply_markup)
                    logger.info(f"User {user.id} viewed product details: {product_id}")
                    
                else:
                    await query.edit_message_text("❌ Товар не найден.")
                    logger.warning(f"User {user.id} requested non-existent product: {product_id}")
                    
            except Exception as e:
                logger.error(f"Ошибка получения информации о товаре для пользователя {user.id}: {e}")
                await query.edit_message_text("❌ Произошла ошибка при получении информации о товаре.")
        
        elif callback_data == "search_new":
            # Новый поиск - запускаем интерактивный режим
            search_message = (
                "🔍 **Поиск товаров OptFM**\n\n"
                "Введите наименование аксессуара или производителя, "
                "к которому хотите подобрать аксессуар.\n\n"
                "**Примеры запросов:**\n"
                "• Samsung\n"
                "• iPhone\n"
                "• FM модулятор\n"
                "• защитное стекло\n"
                "• наушники\n"
                "• зарядка"
            )
            
            # Создаем интерактивные кнопки
            keyboard = [
                [InlineKeyboardButton("📂 Просмотр категорий", callback_data="search_categories")],
                [InlineKeyboardButton("🏭 Просмотр производителей", callback_data="search_manufacturers")],
                [InlineKeyboardButton("🔍 Популярные запросы", callback_data="search_popular")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                search_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Устанавливаем режим поиска для пользователя
            context.user_data['search_mode'] = True
            logger.info(f"User {user.id} started interactive search")
        
        elif callback_data.startswith("search_query_"):
            # Поиск по конкретному запросу
            query = callback_data[13:]  # Убираем "search_query_" из начала
            await self._perform_search(update, query)
            logger.info(f"User {user.id} searched for: {query}")
        
        elif callback_data == "search_popular":
            # Показать популярные запросы
            popular_message = (
                "🔍 **Популярные запросы:**\n\n"
                "Выберите интересующий вас запрос:"
            )
            
            keyboard = [
                [InlineKeyboardButton("📱 Samsung", callback_data="search_query_Samsung")],
                [InlineKeyboardButton("🍎 iPhone", callback_data="search_query_iPhone")],
                [InlineKeyboardButton("📻 FM модулятор", callback_data="search_query_FM модулятор")],
                [InlineKeyboardButton("🛡️ Защитное стекло", callback_data="search_query_защитное стекло")],
                [InlineKeyboardButton("🎧 Наушники", callback_data="search_query_наушники")],
                [InlineKeyboardButton("🔌 Зарядка", callback_data="search_query_зарядка")],
                [InlineKeyboardButton("📂 Все категории", callback_data="search_categories")],
                [InlineKeyboardButton("🔍 Свой запрос", callback_data="search_new")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                popular_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            logger.info(f"User {user.id} requested popular searches")
        
        elif callback_data == "ask_question":
            # Переключение в режим вопросов
            question_message = (
                "📚 **Задайте вопрос о продуктах OptFM**\n\n"
                "Напишите ваш вопрос, и я постараюсь на него ответить.\n\n"
                "**Примеры вопросов:**\n"
                "• Какие у вас есть продукты?\n"
                "• Как с вами связаться?\n"
                "• Какие условия доставки?\n"
                "• Есть ли у вас гарантия?"
            )
            
            await query.edit_message_text(
                question_message,
                parse_mode='Markdown'
            )
            logger.info(f"User {user.id} switched to question mode")
        
        elif callback_data == "search_categories":
            # Показать категории
            if not self.rag_manager:
                await query.edit_message_text("❌ Каталог товаров временно недоступен.")
                return
            
            try:
                categories = self.rag_manager.get_categories()
                
                if not categories:
                    await query.edit_message_text("❌ Категории товаров не найдены.")
                    return
                
                categories_message = "📂 **Категории товаров OptFM:**\n\n"
                
                keyboard = []
                for i, category in enumerate(categories[:15], 1):
                    categories_message += f"**{i}.** {category}\n"
                    
                    button_text = category[:30] + "..." if len(category) > 30 else category
                    keyboard.append([InlineKeyboardButton(
                        text=f"{i}. {button_text}",
                        callback_data=f"category_{category}"
                    )])
                
                if len(categories) > 15:
                    categories_message += f"\n... и еще **{len(categories) - 15}** категорий\n"
                    keyboard.append([InlineKeyboardButton("📄 Показать еще", callback_data="categories_more")])
                
                keyboard.append([InlineKeyboardButton("🔍 Поиск товаров", callback_data="search_new")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(categories_message, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} requested categories from search")
                
            except Exception as e:
                logger.error(f"Ошибка получения категорий для пользователя {user.id}: {e}")
                await query.edit_message_text("❌ Произошла ошибка при получении категорий.")
        
        elif callback_data == "search_manufacturers":
            # Показать производителей
            if not self.rag_manager:
                await query.edit_message_text("❌ Каталог товаров временно недоступен.")
                return
            
            try:
                manufacturers = self.rag_manager.get_device_manufacturers()
                
                if not manufacturers:
                    await query.edit_message_text("❌ Производители техники не найдены.")
                    return
                
                manufacturers_message = "🏭 **Производители техники:**\n\n"
                
                keyboard = []
                for i, manufacturer in enumerate(manufacturers[:15], 1):
                    manufacturers_message += f"**{i}.** {manufacturer}\n"
                    
                    keyboard.append([InlineKeyboardButton(
                        text=f"{i}. {manufacturer}",
                        callback_data=f"manufacturer_{manufacturer}"
                    )])
                
                if len(manufacturers) > 15:
                    manufacturers_message += f"\n... и еще **{len(manufacturers) - 15}** производителей\n"
                    keyboard.append([InlineKeyboardButton("📄 Показать еще", callback_data="manufacturers_more")])
                
                keyboard.append([InlineKeyboardButton("🔍 Поиск товаров", callback_data="search_new")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(manufacturers_message, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} requested manufacturers from search")
                
            except Exception as e:
                logger.error(f"Ошибка получения производителей для пользователя {user.id}: {e}")
                await query.edit_message_text("❌ Произошла ошибка при получении производителей.")
        
        elif callback_data.startswith("category_"):
            # Поиск товаров по категории
            category = callback_data[9:]  # Убираем "category_" из начала
            
            if not self.rag_manager:
                await query.edit_message_text("❌ Поиск товаров временно недоступен.")
                return
            
            try:
                products = self.rag_manager.get_products_by_category(category, limit=10)
                
                if not products:
                    await query.edit_message_text(f"❌ В категории '{category}' товары не найдены.")
                    return
                
                category_message = f"📂 **Категория: {category}**\n\n"
                category_message += f"Найдено товаров: **{len(products)}**\n\n"
                
                keyboard = []
                for i, product in enumerate(products, 1):
                    button_text = f"{i}. {product['name'][:40]}"
                    if len(product['name']) > 40:
                        button_text += "..."
                    
                    keyboard.append([InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"product_{product['id']}"
                    )])
                    
                    category_message += f"**{i}.** {product['name']}\n"
                    category_message += f"    Бренд: {product.get('brand', 'Не указан')}\n\n"
                
                keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_new")])
                keyboard.append([InlineKeyboardButton("📂 Все категории", callback_data="search_categories")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(category_message, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} viewed category: {category}")
                
            except Exception as e:
                logger.error(f"Ошибка поиска товаров по категории для пользователя {user.id}: {e}")
                await query.edit_message_text("❌ Произошла ошибка при поиске товаров по категории.")
        
        elif callback_data.startswith("manufacturer_"):
            # Поиск товаров по производителю
            manufacturer = callback_data[13:]  # Убираем "manufacturer_" из начала
            
            if not self.rag_manager:
                await query.edit_message_text("❌ Поиск товаров временно недоступен.")
                return
            
            try:
                products = self.rag_manager.search_products(manufacturer, top_k=10, device_manufacturer_filter=manufacturer)
                
                if not products:
                    await query.edit_message_text(f"❌ Товары для производителя '{manufacturer}' не найдены.")
                    return
                
                manufacturer_message = f"🏭 **Производитель: {manufacturer}**\n\n"
                manufacturer_message += f"Найдено товаров: **{len(products)}**\n\n"
                
                keyboard = []
                for i, product in enumerate(products, 1):
                    button_text = f"{i}. {product['name'][:40]}"
                    if len(product['name']) > 40:
                        button_text += "..."
                    
                    keyboard.append([InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"product_{product['id']}"
                    )])
                    
                    manufacturer_message += f"**{i}.** {product['name']}\n"
                    manufacturer_message += f"    Категория: {product.get('category', 'Не указана')}\n"
                    manufacturer_message += f"    Бренд: {product.get('brand', 'Не указан')}\n\n"
                
                keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_new")])
                keyboard.append([InlineKeyboardButton("🏭 Все производители", callback_data="search_manufacturers")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(manufacturer_message, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} viewed manufacturer: {manufacturer}")
                
            except Exception as e:
                logger.error(f"Ошибка поиска товаров по производителю для пользователя {user.id}: {e}")
                await query.edit_message_text("❌ Произошла ошибка при поиске товаров по производителю.")
        
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
