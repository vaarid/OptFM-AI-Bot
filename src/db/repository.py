"""
Repository layer for database operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import logging

from .models import User, Request, Dialog, RequestStatus, UserSource

logger = logging.getLogger(__name__)

class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по Telegram ID
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[User]: Пользователь или None
        """
        return self.session.query(User).filter(User.telegram_id == telegram_id).first()
    
    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> User:
        """
        Создание нового пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия
            
        Returns:
            User: Созданный пользователь
        """
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            source=UserSource.TELEGRAM
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        logger.info(f"Created new user: {user.id} (telegram_id: {telegram_id})")
        return user
    
    def update_user_contacts(self, user_id: int, phone: str = None, email: str = None) -> User:
        """
        Обновление контактных данных пользователя
        
        Args:
            user_id: ID пользователя
            phone: Телефон
            email: Email
            
        Returns:
            User: Обновленный пользователь
        """
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        if phone:
            user.phone = phone
        if email:
            user.email = email
        
        user.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(user)
        
        logger.info(f"Updated user contacts: {user_id}")
        return user

class RequestRepository:
    """Репозиторий для работы с заявками"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_request(self, user_id: int, title: str, description: str = None) -> Request:
        """
        Создание новой заявки
        
        Args:
            user_id: ID пользователя
            title: Заголовок заявки
            description: Описание заявки
            
        Returns:
            Request: Созданная заявка
        """
        request = Request(
            user_id=user_id,
            title=title,
            description=description,
            status=RequestStatus.NEW
        )
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        
        logger.info(f"Created new request: {request.id} for user: {user_id}")
        return request
    
    def get_user_requests(self, user_id: int) -> List[Request]:
        """
        Получение всех заявок пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Request]: Список заявок
        """
        return self.session.query(Request).filter(Request.user_id == user_id).all()
    
    def get_new_requests(self) -> List[Request]:
        """
        Получение всех новых заявок
        
        Returns:
            List[Request]: Список новых заявок
        """
        return self.session.query(Request).filter(Request.status == RequestStatus.NEW).all()
    
    def update_request_status(self, request_id: int, status: RequestStatus, 
                            manager_notes: str = None) -> Request:
        """
        Обновление статуса заявки
        
        Args:
            request_id: ID заявки
            status: Новый статус
            manager_notes: Заметки менеджера
            
        Returns:
            Request: Обновленная заявка
        """
        request = self.session.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise ValueError(f"Request with id {request_id} not found")
        
        request.status = status
        if manager_notes:
            request.manager_notes = manager_notes
        
        request.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(request)
        
        logger.info(f"Updated request status: {request_id} -> {status.value}")
        return request

class DialogRepository:
    """Репозиторий для работы с диалогами"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add_dialog(self, user_id: int, message: str, response: str, 
                  is_question: bool = True) -> Dialog:
        """
        Добавление записи диалога
        
        Args:
            user_id: ID пользователя
            message: Сообщение пользователя
            response: Ответ бота
            is_question: Является ли сообщение вопросом
            
        Returns:
            Dialog: Созданная запись диалога
        """
        dialog = Dialog(
            user_id=user_id,
            message=message,
            response=response,
            is_question=is_question
        )
        self.session.add(dialog)
        self.session.commit()
        self.session.refresh(dialog)
        
        return dialog
    
    def get_user_dialogs(self, user_id: int, limit: int = 10) -> List[Dialog]:
        """
        Получение последних диалогов пользователя
        
        Args:
            user_id: ID пользователя
            limit: Количество записей
            
        Returns:
            List[Dialog]: Список диалогов
        """
        return self.session.query(Dialog).filter(
            Dialog.user_id == user_id
        ).order_by(Dialog.created_at.desc()).limit(limit).all()
