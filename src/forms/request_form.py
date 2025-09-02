"""
Request form handling for OptFM AI Bot
"""
from typing import Dict, Any, Optional
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class FormState(Enum):
    """Состояния формы заявки"""
    IDLE = "idle"
    ASKING_NAME = "asking_name"
    ASKING_PHONE = "asking_phone"
    ASKING_EMAIL = "asking_email"
    ASKING_DESCRIPTION = "asking_description"
    COMPLETED = "completed"

class RequestForm:
    """Класс для работы с формой заявки"""
    
    def __init__(self):
        self.state = FormState.IDLE
        self.data = {
            "name": None,
            "phone": None,
            "email": None,
            "description": None,
            "original_question": None
        }
    
    def start_form(self, original_question: str = None) -> str:
        """
        Начало заполнения формы
        
        Args:
            original_question: Исходный вопрос пользователя
            
        Returns:
            str: Сообщение для пользователя
        """
        self.state = FormState.ASKING_NAME
        self.data["original_question"] = original_question
        
        return (
            "📝 Давайте оформим заявку для нашего менеджера!\n\n"
            "Для начала, как вас зовут? (ФИО)"
        )
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Обработка ввода пользователя
        
        Args:
            user_input: Ввод пользователя
            
        Returns:
            Dict[str, Any]: Результат обработки с сообщением и данными
        """
        if self.state == FormState.IDLE:
            return {"message": "Форма не активна", "completed": False}
        
        if self.state == FormState.ASKING_NAME:
            return self._process_name(user_input)
        elif self.state == FormState.ASKING_PHONE:
            return self._process_phone(user_input)
        elif self.state == FormState.ASKING_EMAIL:
            return self._process_email(user_input)
        elif self.state == FormState.ASKING_DESCRIPTION:
            return self._process_description(user_input)
        
        return {"message": "Неизвестное состояние формы", "completed": False}
    
    def _process_name(self, name: str) -> Dict[str, Any]:
        """Обработка имени"""
        name = name.strip()
        if len(name) < 2:
            return {
                "message": "Пожалуйста, введите полное имя (минимум 2 символа)",
                "completed": False
            }
        
        self.data["name"] = name
        self.state = FormState.ASKING_PHONE
        
        return {
            "message": (
                f"Спасибо, {name}! 📞\n\n"
                "Теперь укажите ваш номер телефона для связи:"
            ),
            "completed": False
        }
    
    def _process_phone(self, phone: str) -> Dict[str, Any]:
        """Обработка телефона"""
        phone = phone.strip()
        
        # Простая валидация телефона
        phone_clean = re.sub(r'[^\d+]', '', phone)
        if len(phone_clean) < 10:
            return {
                "message": "Пожалуйста, введите корректный номер телефона",
                "completed": False
            }
        
        self.data["phone"] = phone
        self.state = FormState.ASKING_EMAIL
        
        return {
            "message": (
                "Отлично! 📧\n\n"
                "Теперь укажите ваш email (необязательно, можно пропустить, написав 'пропустить'):"
            ),
            "completed": False
        }
    
    def _process_email(self, email: str) -> Dict[str, Any]:
        """Обработка email"""
        email = email.strip().lower()
        
        if email.lower() in ['пропустить', 'нет', 'не нужно', 'skip']:
            self.data["email"] = None
        else:
            # Простая валидация email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return {
                    "message": "Пожалуйста, введите корректный email или напишите 'пропустить'",
                    "completed": False
                }
            self.data["email"] = email
        
        self.state = FormState.ASKING_DESCRIPTION
        
        return {
            "message": (
                "Хорошо! 📝\n\n"
                "Теперь опишите ваш вопрос или запрос подробнее:"
            ),
            "completed": False
        }
    
    def _process_description(self, description: str) -> Dict[str, Any]:
        """Обработка описания"""
        description = description.strip()
        if len(description) < 10:
            return {
                "message": "Пожалуйста, опишите ваш запрос подробнее (минимум 10 символов)",
                "completed": False
            }
        
        self.data["description"] = description
        self.state = FormState.COMPLETED
        
        return {
            "message": self._get_completion_message(),
            "completed": True,
            "data": self.data.copy()
        }
    
    def _get_completion_message(self) -> str:
        """Сообщение о завершении формы"""
        name = self.data["name"]
        phone = self.data["phone"]
        email = self.data.get("email", "не указан")
        
        return (
            f"✅ Спасибо, {name}! Ваша заявка принята.\n\n"
            f"📋 **Данные заявки:**\n"
            f"• Имя: {name}\n"
            f"• Телефон: {phone}\n"
            f"• Email: {email}\n"
            f"• Вопрос: {self.data['description']}\n\n"
            f"📞 Наш менеджер свяжется с вами в ближайшее время по телефону {phone}.\n\n"
            f"⏰ Время работы менеджеров: Пн-Пт 9:00-18:00"
        )
    
    def cancel_form(self) -> str:
        """
        Отмена заполнения формы
        
        Returns:
            str: Сообщение об отмене
        """
        self.state = FormState.IDLE
        self.data = {
            "name": None,
            "phone": None,
            "email": None,
            "description": None,
            "original_question": None
        }
        
        return "❌ Заполнение заявки отменено. Можете задать другой вопрос!"
    
    def get_current_state(self) -> FormState:
        """Получение текущего состояния формы"""
        return self.state
    
    def is_active(self) -> bool:
        """Проверка активности формы"""
        return self.state != FormState.IDLE and self.state != FormState.COMPLETED

class RequestFormManager:
    """Менеджер форм заявок для пользователей"""
    
    def __init__(self):
        self.forms: Dict[int, RequestForm] = {}
    
    def get_form(self, user_id: int) -> RequestForm:
        """
        Получение формы пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            RequestForm: Форма пользователя
        """
        if user_id not in self.forms:
            self.forms[user_id] = RequestForm()
        
        return self.forms[user_id]
    
    def start_form(self, user_id: int, original_question: str = None) -> str:
        """
        Начало заполнения формы для пользователя
        
        Args:
            user_id: ID пользователя
            original_question: Исходный вопрос
            
        Returns:
            str: Сообщение для пользователя
        """
        form = self.get_form(user_id)
        return form.start_form(original_question)
    
    def process_input(self, user_id: int, user_input: str) -> Dict[str, Any]:
        """
        Обработка ввода пользователя
        
        Args:
            user_id: ID пользователя
            user_input: Ввод пользователя
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        form = self.get_form(user_id)
        return form.process_input(user_input)
    
    def cancel_form(self, user_id: int) -> str:
        """
        Отмена формы пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Сообщение об отмене
        """
        form = self.get_form(user_id)
        return form.cancel_form()
    
    def is_user_filling_form(self, user_id: int) -> bool:
        """
        Проверка, заполняет ли пользователь форму
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если пользователь заполняет форму
        """
        form = self.get_form(user_id)
        return form.is_active()
    
    def clear_form(self, user_id: int):
        """
        Очистка формы пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.forms:
            del self.forms[user_id]
