"""
Telegram Bot Module for Fashion Mobile AI Bot
"""
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from faq.enhanced_faq_manager import EnhancedFAQManager

logger = logging.getLogger(__name__)

class FashionMobileBot:
    """Основной класс Telegram бота для Fashion Mobile"""
    
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
        
        # Обработчик команды /feedback
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))
        
        # Обработчик команды /form
        self.application.add_handler(CommandHandler("form", self.contact_form_command))
        

        
        # Обработчик callback-запросов (для интерактивных кнопок)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик контактных данных
        self.application.add_handler(MessageHandler(filters.CONTACT, self.contact_handler))
        
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
            "Я бот компании Fashion Mobile. Могу помочь с информацией о наших продуктах и услугах.\n\n"
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
            "🤖 **Fashion Mobile AI Bot - Справка**\n\n"
            "**Доступные команды:**\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/faq - Показать FAQ с интерактивными кнопками\n"
            "/feedback - Форма обратной связи с менеджером\n"
            "/form - Заполнить форму контактных данных\n\n"
            "**Как использовать:**\n"
            "• Напишите вопрос о продуктах Fashion Mobile\n"
            "• Используйте /faq для просмотра всех вопросов с кнопками\n"
            "• Нажмите на интересующий вопрос для получения ответа\n"
            "• Если ответа нет в FAQ, используйте /feedback или /form\n\n"
            "**Примеры вопросов:**\n"
            "• Какие у вас есть продукты?\n"
            "• Расскажите о ценах\n"
            "• Как с вами связаться?\n\n"
            "**Обратная связь:**\n"
            "• /feedback - быстрая связь с менеджером\n"
            "• /form - подробная форма с контактными данными"
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
            "📚 **Часто задаваемые вопросы Fashion Mobile:**\n\n"
            "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
            f"Показано: **{len(current_faq_list)}** из **{len(faq_list)}** вопросов"
        )
        
        await update.message.reply_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
        logger.info(f"User {update.effective_user.id} requested FAQ list with buttons (page 1)")
        
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /feedback - показывает форму обратной связи
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        
        feedback_text = (
            "📋 **Форма обратной связи Fashion Mobile**\n\n"
            "Здравствуйте! Если у вас есть вопросы, которые не покрывает наша база знаний, "
            "или вам нужна персональная консультация, оставьте заявку.\n\n"
            "**Наш менеджер свяжется с вами в ближайшее время!**\n\n"
            "**Способы связи:**\n"
            "• Email\n"
            "• Telegram\n"
            "• Оставить контактные данные в чате\n\n"
            "**Время работы:**\n"
            "• Пн-Пт: 9:00 - 18:00\n"
            "• Сб: 10:00 - 16:00\n"
            "• Вс: выходной"
        )
        
        # Создаем кнопки для быстрого ответа
        keyboard = [
            [InlineKeyboardButton("💬 Telegram менеджер", url="https://t.me/fashionmobile_manager")],
            [InlineKeyboardButton("📚 Посмотреть FAQ", callback_data="faq_back_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Создаем дополнительную клавиатуру с кнопкой "Поделиться контактом"
        contact_keyboard = [[KeyboardButton("📱 Поделиться контактом", request_contact=True)]]
        contact_reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(feedback_text, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Отправляем дополнительное сообщение с кнопкой "Поделиться контактом"
        contact_text = (
            "📱 **Или поделитесь контактом одним нажатием:**\n\n"
            "Нажмите кнопку ниже, чтобы быстро отправить ваши контактные данные."
        )
        await update.message.reply_text(contact_text, reply_markup=contact_reply_markup)
        
        logger.info(f"User {user.id} requested feedback form")
        
    async def contact_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик контактных данных (кнопка "Поделиться контактом")
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        contact = update.message.contact
        
        # Извлекаем данные из контакта
        contact_name = contact.first_name
        if contact.last_name:
            contact_name += f" {contact.last_name}"
        
        contact_phone = contact.phone_number
        
        response = (
            "📱 **Контактные данные получены!**\n\n"
            f"**Имя:** {contact_name}\n"
            f"**Телефон:** {contact_phone}\n\n"
            "✅ Спасибо за предоставление контактных данных!\n\n"
            "Наш менеджер свяжется с вами в ближайшее время для ответа на ваш вопрос.\n\n"
            "**Время работы:**\n"
            "• Пн-Пт: 9:00 - 18:00\n"
            "• Сб: 10:00 - 16:00\n"
            "• Вс: выходной\n\n"
            "Если у вас есть срочные вопросы, звоните: +7 (XXX) XXX-XX-XX"
        )
        
        # Логируем контактные данные
        logger.info(f"User {user.id} ({user.username}) shared contact: {contact_name}, {contact_phone}")
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    async def contact_form_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /form - показывает форму для заполнения контактных данных
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user = update.effective_user
        
        form_text = (
            "📋 **Форма обратной связи Fashion Mobile**\n\n"
            "Для получения персональной консультации заполните форму:\n\n"
            "**1. Ваше имя:**\n"
            "Напишите ваше имя\n\n"
            "**2. Email:**\n"
            "Укажите ваш email для связи\n\n"
            "**3. Телефон:**\n"
            "Ваш номер телефона\n\n"
            "**4. Как удобнее связаться?**\n"
            "Выберите предпочтительный способ связи\n\n"
            "**5. Согласие на обработку персональных данных**\n"
            "Подтвердите согласие на обработку ваших данных\n\n"
            "**Начните с ввода вашего имени:**"
        )
        
        # Создаем кнопки для быстрого заполнения
        keyboard = [
            [InlineKeyboardButton("📞 Предпочитаю звонок", callback_data="contact_phone")],
            [InlineKeyboardButton("✉️ Предпочитаю email", callback_data="contact_email")],
            [InlineKeyboardButton("💬 Предпочитаю Telegram", callback_data="contact_telegram")],
            [InlineKeyboardButton("📚 Вернуться к FAQ", callback_data="faq_back_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(form_text, parse_mode='Markdown', reply_markup=reply_markup)
        logger.info(f"User {user.id} requested contact form")
        
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик текстовых сообщений с поиском в FAQ
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        user_message = update.message.text
        user = update.effective_user
        
        # Проверяем, является ли сообщение контактными данными
        import re
        phone_pattern = r'(\+?7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        is_phone = bool(re.search(phone_pattern, user_message))
        is_email = bool(re.search(email_pattern, user_message))
        
        # Проверяем, заполняет ли пользователь форму
        if 'form_step' in context.user_data:
            await self._handle_form_step(update, context, user_message)
            return
        
        if is_phone or is_email:
            # Пользователь оставил контактные данные
            contact_type = "телефон" if is_phone else "email"
            response = (
                f"✅ Спасибо! Ваш {contact_type} получен.\n\n"
                f"**Ваши контактные данные:** {user_message}\n\n"
                "Наш менеджер свяжется с вами в ближайшее время для ответа на ваш вопрос.\n\n"
                "**Время работы:**\n"
                "• Пн-Пт: 9:00 - 18:00\n"
                "• Сб: 10:00 - 16:00\n"
                "• Вс: выходной\n\n"
                "Если у вас есть срочные вопросы, звоните: +7 (XXX) XXX-XX-XX"
            )
            
            # Логируем контактные данные
            logger.info(f"User {user.id} ({user.username}) left contact info: {user_message}")
            
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        # Проверяем, является ли сообщение приветствием
        greeting_keywords = ['привет', 'здравствуй', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро', 'hi', 'hello']
        is_greeting = any(greeting in user_message.lower() for greeting in greeting_keywords)
        
        # Проверяем, является ли сообщение прощанием
        farewell_keywords = ['пока', 'до свидания', 'до встречи', 'спасибо', 'благодарю', 'bye', 'goodbye', 'thanks']
        is_farewell = any(farewell in user_message.lower() for farewell in farewell_keywords)
        
        # Проверяем, является ли сообщение вопросом (содержит вопросительные слова)
        question_keywords = ['что', 'как', 'где', 'когда', 'почему', 'зачем', 'какие', 'какой', 'сколько', 'есть ли', 'можно ли']
        is_question = any(question in user_message.lower() for question in question_keywords) or user_message.strip().endswith('?')
        
        if is_greeting:
            # Приветствие - даем вежливый ответ
            response = (
                f"👋 Здравствуйте, {user.first_name}!\n\n"
                "Я бот компании Fashion Mobile. Могу помочь с информацией о наших продуктах и услугах.\n\n"
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
                "Спасибо за обращение к Fashion Mobile. Если у вас появятся вопросы, "
                "я всегда готов помочь!\n\n"
                "Удачного дня! 😊"
            )
            logger.info(f"Прощание от пользователя {user.id}: {user_message}")
        elif not is_question and len(user_message.split()) < 3:
            # Короткое сообщение без вопроса - предлагаем задать вопрос
            response = (
                f"🤔 {user.first_name}, я не совсем понял ваш запрос.\n\n"
                "Задайте мне вопрос о продуктах Fashion Mobile, например:\n"
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
                
                # Создаем кнопки для обратной связи
                keyboard = [
                    [InlineKeyboardButton("📞 Оставить заявку", callback_data=f"feedback_{user.id}_{hash(user_message) % 10000}")],
                    [InlineKeyboardButton("📋 Заполнить форму", callback_data="start_form")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                logger.info(f"FAQ ответ не найден для пользователя {user.id}: {user_message[:50]}...")
                
                await update.message.reply_text(response, reply_markup=reply_markup)
                
                # Отправляем дополнительное сообщение с кнопкой "Поделиться контактом"
                contact_text = (
                    "📱 **Или поделитесь контактом одним нажатием:**\n\n"
                    "Нажмите кнопку ниже, чтобы быстро отправить ваши контактные данные."
                )
                contact_keyboard = [[KeyboardButton("📱 Поделиться контактом", request_contact=True)]]
                contact_reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text(contact_text, reply_markup=contact_reply_markup)
                
                return
        
        await update.message.reply_text(response)
    
    async def _handle_form_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
        """
        Обработка заполнения формы контактных данных
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
            user_message: Сообщение пользователя
        """
        user = update.effective_user
        form_step = context.user_data.get('form_step', 'name')
        
        if form_step == 'name':
            # Сохраняем имя
            context.user_data['user_name'] = user_message
            context.user_data['form_step'] = 'email'
            
            response = (
                f"✅ Имя сохранено: **{user_message}**\n\n"
                "**2. Email:**\n"
                "Укажите ваш email для связи"
            )
            
        elif form_step == 'email':
            # Проверяем email
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.search(email_pattern, user_message):
                response = "❌ Неверный формат email. Попробуйте еще раз:"
                await update.message.reply_text(response)
                return
            
            context.user_data['user_email'] = user_message
            context.user_data['form_step'] = 'phone'
            
            response = (
                f"✅ Email сохранен: **{user_message}**\n\n"
                "**3. Телефон:**\n"
                "Ваш номер телефона"
            )
            
        elif form_step == 'phone':
            # Проверяем телефон
            import re
            phone_pattern = r'(\+?7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
            if not re.search(phone_pattern, user_message):
                response = "❌ Неверный формат телефона. Попробуйте еще раз:"
                await update.message.reply_text(response)
                return
            
            context.user_data['user_phone'] = user_message
            context.user_data['form_step'] = 'consent'
            
            response = (
                f"✅ Телефон сохранен: **{user_message}**\n\n"
                "**4. Согласие на обработку персональных данных**\n"
                "Напишите 'Согласен' или 'Согласна' для подтверждения"
            )
            
        elif form_step == 'consent':
            # Проверяем согласие
            consent_words = ['согласен', 'согласна', 'да', 'yes', 'подтверждаю']
            if not any(word in user_message.lower() for word in consent_words):
                response = "❌ Для продолжения необходимо дать согласие. Напишите 'Согласен' или 'Согласна':"
                await update.message.reply_text(response)
                return
            
            # Форма заполнена
            context.user_data['consent'] = user_message
            context.user_data['form_step'] = 'completed'
            
            # Собираем все данные
            user_name = context.user_data.get('user_name', 'Не указано')
            user_email = context.user_data.get('user_email', 'Не указано')
            user_phone = context.user_data.get('user_phone', 'Не указано')
            preferred_contact = context.user_data.get('preferred_contact', 'не указан')
            
            method_names = {
                "phone": "📞 звонок",
                "email": "✉️ email", 
                "telegram": "💬 Telegram"
            }
            preferred_method = method_names.get(preferred_contact, "не указан")
            
            response = (
                "🎉 **Форма успешно заполнена!**\n\n"
                "**Ваши данные:**\n"
                f"• Имя: {user_name}\n"
                f"• Email: {user_email}\n"
                f"• Телефон: {user_phone}\n"
                f"• Предпочтительный способ связи: {preferred_method}\n"
                f"• Согласие на обработку данных: ✅\n\n"
                "**Спасибо за обращение!**\n"
                "Наш менеджер свяжется с вами в ближайшее время.\n\n"
                "**Время работы:**\n"
                "• Пн-Пт: 9:00 - 18:00\n"
                "• Сб: 10:00 - 16:00\n"
                "• Вс: выходной"
            )
            
            # Логируем заполненную форму
            logger.info(f"User {user.id} ({user.username}) completed contact form: {user_name}, {user_email}, {user_phone}, {preferred_contact}")
            
            # Очищаем данные формы
            context.user_data.clear()
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /stats - показывает статистику FAQ
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст бота
        """
        stats = self.faq_manager.get_statistics()
        
        stats_message = (
            f"📊 **Статистика FAQ Fashion Mobile:**\n\n"
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
        
        try:
            await query.answer()  # Убираем "часики" у кнопки
        except Exception as e:
            # Обрабатываем ошибки устаревших callback query
            logger.warning(f"Failed to answer callback query: {e}")
            return
        
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
                "📚 **Часто задаваемые вопросы Fashion Mobile:**\n\n"
                "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                f"Показано: **{len(current_faq_list)}** из **{len(faq_list)}** вопросов"
            )
            
            try:
                await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} returned to FAQ list (page 1)")
            except Exception as e:
                logger.warning(f"Failed to edit message for user {user.id}: {e}")
                # Отправляем новое сообщение если редактирование не удалось
                await context.bot.send_message(
                    chat_id=user.id,
                    text=faq_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
        elif callback_data == "start_form":
            # Начинаем заполнение формы
            context.user_data['form_step'] = 'name'
            
            form_text = (
                "📋 **Форма обратной связи Fashion Mobile**\n\n"
                "Для получения персональной консультации заполните форму:\n\n"
                "**1. Ваше имя:**\n"
                "Напишите ваше имя\n\n"
                "**2. Email:**\n"
                "Укажите ваш email для связи\n\n"
                "**3. Телефон:**\n"
                "Ваш номер телефона\n\n"
                "**4. Как удобнее связаться?**\n"
                "Выберите предпочтительный способ связи\n\n"
                "**5. Согласие на обработку персональных данных**\n"
                "Подтвердите согласие на обработку ваших данных\n\n"
                "**Начните с ввода вашего имени:**"
            )
            
            # Создаем кнопки для быстрого заполнения
            keyboard = [
                [InlineKeyboardButton("📞 Предпочитаю звонок", callback_data="contact_phone")],
                [InlineKeyboardButton("✉️ Предпочитаю email", callback_data="contact_email")],
                [InlineKeyboardButton("💬 Предпочитаю Telegram", callback_data="contact_telegram")],
                [InlineKeyboardButton("📚 Вернуться к FAQ", callback_data="faq_back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(form_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} started contact form")
            except Exception as e:
                logger.warning(f"Failed to edit message for user {user.id}: {e}")
                await context.bot.send_message(
                    chat_id=user.id,
                    text=form_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        elif callback_data.startswith("contact_"):
            # Обработка выбора предпочтительного способа связи
            contact_method = callback_data.split("_")[1]
            
            method_names = {
                "phone": "📞 звонок",
                "email": "✉️ email", 
                "telegram": "💬 Telegram"
            }
            
            method_name = method_names.get(contact_method, "неизвестный способ")
            
            # Сохраняем предпочтение в контексте и начинаем заполнение формы
            context.user_data['preferred_contact'] = contact_method
            context.user_data['form_step'] = 'name'
            
            response_text = (
                f"✅ Отлично! Вы выбрали: **{method_name}**\n\n"
                "Теперь заполните остальные поля формы:\n\n"
                "**1. Ваше имя:**\n"
                "Напишите ваше имя\n\n"
                "**2. Email:**\n"
                "Укажите ваш email для связи\n\n"
                "**3. Телефон:**\n"
                "Ваш номер телефона\n\n"
                "**4. Согласие на обработку персональных данных**\n"
                "Напишите 'Согласен' или 'Согласна' для подтверждения\n\n"
                "**Начните с ввода вашего имени:**"
            )
            
            keyboard = [
                [InlineKeyboardButton("📚 Вернуться к FAQ", callback_data="faq_back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)
                logger.info(f"User {user.id} selected contact method: {contact_method}")
            except Exception as e:
                logger.warning(f"Failed to edit message for user {user.id}: {e}")
                await context.bot.send_message(
                    chat_id=user.id,
                    text=response_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        elif callback_data.startswith("feedback_"):
            # Обработка обратной связи
            try:
                parts = callback_data.split("_")
                if len(parts) >= 3:
                    user_id = parts[1]
                    question_hash = parts[2]
                    
                    # Создаем форму обратной связи
                    feedback_text = (
                        "📋 **Форма обратной связи Fashion Mobile**\n\n"
                        "Спасибо за ваш интерес! Наш менеджер свяжется с вами в ближайшее время.\n\n"
                        "**Ваши данные:**\n"
                        f"• ID пользователя: {user_id}\n"
                        f"• Время обращения: {context.bot_data.get('current_time', 'Не указано')}\n\n"
                        "**Для связи с менеджером:**\n"
                        "• Email: manager@fashionmobile.ru\n"
                        "• Telegram: @fashionmobile_manager\n"
                        "• Телефон: +7 (XXX) XXX-XX-XX\n\n"
                        "**Или оставьте свои контактные данные:**\n"
                        "Напишите ваш номер телефона или email, и мы свяжемся с вами!"
                    )
                    
                    # Создаем кнопки для быстрого ответа
                    keyboard = [
                        [InlineKeyboardButton("💬 Telegram менеджер", url="https://t.me/fashionmobile_manager")],
                        [InlineKeyboardButton("🔙 Назад к FAQ", callback_data="faq_back_to_list")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    try:
                        await query.edit_message_text(feedback_text, parse_mode='Markdown', reply_markup=reply_markup)
                        logger.info(f"User {user.id} opened feedback form")
                    except Exception as e:
                        logger.warning(f"Failed to edit message for user {user.id}: {e}")
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=feedback_text,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                else:
                    await query.edit_message_text("❌ Ошибка в данных обратной связи.")
                    
            except Exception as e:
                logger.error(f"Error processing feedback callback: {e}")
                await query.edit_message_text("❌ Произошла ошибка при обработке заявки.")
                
        elif callback_data.startswith("faq_"):
            faq_id = callback_data[4:]  # Убираем "faq_" из начала
            
            # Проверяем, что это не команда
            if faq_id.startswith("/"):
                try:
                    await query.edit_message_text("❌ Неверный запрос.")
                    logger.warning(f"User {user.id} sent invalid callback: {callback_data}")
                except Exception as e:
                    logger.warning(f"Failed to edit message for user {user.id}: {e}")
                    await context.bot.send_message(chat_id=user.id, text="❌ Неверный запрос.")
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
                    "📚 **Часто задаваемые вопросы Fashion Mobile (страница 2):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                try:
                    await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                    logger.info(f"User {user.id} requested FAQ page 2")
                except Exception as e:
                    logger.warning(f"Failed to edit message for user {user.id}: {e}")
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=faq_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                
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
                    "📚 **Часто задаваемые вопросы Fashion Mobile (страница 3):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                try:
                    await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                    logger.info(f"User {user.id} requested FAQ page 3")
                except Exception as e:
                    logger.warning(f"Failed to edit message for user {user.id}: {e}")
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=faq_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                
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
                    "📚 **Часто задаваемые вопросы Fashion Mobile (последняя страница):**\n\n"
                    "Нажмите на интересующий вас вопрос, чтобы получить ответ:\n\n"
                    f"Показано: **{start_index + 1}-{end_index}** из **{len(faq_list)}** вопросов"
                )
                
                try:
                    await query.edit_message_text(faq_text, parse_mode='Markdown', reply_markup=reply_markup)
                    logger.info(f"User {user.id} requested FAQ final page")
                except Exception as e:
                    logger.warning(f"Failed to edit message for user {user.id}: {e}")
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=faq_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                
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
                        
                        try:
                            await query.edit_message_text(answer_text, parse_mode='Markdown', reply_markup=reply_markup)
                            logger.info(f"User {user.id} viewed FAQ {faq_id}")
                        except Exception as e:
                            logger.warning(f"Failed to edit message for user {user.id}: {e}")
                            await context.bot.send_message(
                                chat_id=user.id,
                                text=answer_text,
                                parse_mode='Markdown',
                                reply_markup=reply_markup
                            )
                        
                    else:
                        try:
                            await query.edit_message_text("❌ Вопрос не найден.")
                            logger.warning(f"User {user.id} requested non-existent FAQ {faq_id}")
                        except Exception as e:
                            logger.warning(f"Failed to edit message for user {user.id}: {e}")
                            await context.bot.send_message(chat_id=user.id, text="❌ Вопрос не найден.")
                        
                except ValueError:
                    try:
                        await query.edit_message_text("❌ Неверный ID вопроса.")
                        logger.warning(f"User {user.id} requested invalid FAQ ID: {faq_id}")
                    except Exception as e:
                        logger.warning(f"Failed to edit message for user {user.id}: {e}")
                        await context.bot.send_message(chat_id=user.id, text="❌ Неверный ID вопроса.")
        
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
