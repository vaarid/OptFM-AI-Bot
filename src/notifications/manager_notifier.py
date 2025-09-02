"""
Manager notification system for OptFM AI Bot
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class ManagerNotifier:
    """Класс для уведомления менеджеров о новых заявках"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация уведомлений
        
        Args:
            config: Конфигурация уведомлений
        """
        self.config = config
        self.managers = config.get("managers", [])
        self.email_config = config.get("email", {})
        self.telegram_config = config.get("telegram", {})
        
        logger.info(f"Manager notifier initialized with {len(self.managers)} managers")
    
    def notify_new_request(self, request_data: Dict[str, Any], user_data: Dict[str, Any]) -> bool:
        """
        Уведомление о новой заявке
        
        Args:
            request_data: Данные заявки
            user_data: Данные пользователя
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            # Формируем сообщение
            message = self._format_request_message(request_data, user_data)
            
            # Отправляем уведомления
            success = True
            
            # Email уведомления
            if self.email_config.get("enabled", False):
                email_success = self._send_email_notification(message, request_data)
                success = success and email_success
            
            # Telegram уведомления (если настроены)
            if self.telegram_config.get("enabled", False):
                telegram_success = self._send_telegram_notification(message, request_data)
                success = success and telegram_success
            
            # Логируем результат
            if success:
                logger.info(f"Notification sent successfully for request {request_data.get('id')}")
            else:
                logger.warning(f"Failed to send notification for request {request_data.get('id')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _format_request_message(self, request_data: Dict[str, Any], user_data: Dict[str, Any]) -> str:
        """
        Форматирование сообщения о заявке
        
        Args:
            request_data: Данные заявки
            user_data: Данные пользователя
            
        Returns:
            str: Отформатированное сообщение
        """
        request_id = request_data.get("id", "N/A")
        title = request_data.get("title", "Без заголовка")
        description = request_data.get("description", "Без описания")
        created_at = request_data.get("created_at", datetime.now())
        
        # Обрабатываем created_at как строку или datetime
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
        
        name = user_data.get("name", "Не указано")
        phone = user_data.get("phone", "Не указано")
        email = user_data.get("email", "Не указано")
        telegram_id = user_data.get("telegram_id", "Не указано")
        
        message = f"""
🚨 **НОВАЯ ЗАЯВКА #{request_id}**

📋 **Детали заявки:**
• Заголовок: {title}
• Описание: {description}
• Дата создания: {created_at.strftime('%d.%m.%Y %H:%M')}

👤 **Данные клиента:**
• Имя: {name}
• Телефон: {phone}
• Email: {email}
• Telegram ID: {telegram_id}

📞 **Рекомендуемые действия:**
1. Связаться с клиентом по телефону {phone}
2. Уточнить детали запроса
3. Предложить решение или консультацию
4. Обновить статус заявки в системе

⏰ **Время работы:** Пн-Пт 9:00-18:00
        """
        
        return message.strip()
    
    def _send_email_notification(self, message: str, request_data: Dict[str, Any]) -> bool:
        """
        Отправка email уведомления
        
        Args:
            message: Сообщение
            request_data: Данные заявки
            
        Returns:
            bool: True если отправлено успешно
        """
        try:
            smtp_server = self.email_config.get("smtp_server")
            smtp_port = self.email_config.get("smtp_port", 587)
            username = self.email_config.get("username")
            password = self.email_config.get("password")
            from_email = self.email_config.get("from_email")
            
            if not all([smtp_server, username, password, from_email]):
                logger.warning("Email configuration incomplete")
                return False
            
            # Создаем сообщение
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['Subject'] = f"Новая заявка #{request_data.get('id', 'N/A')} - OptFM Bot"
            
            # Добавляем текст сообщения
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # Отправляем всем менеджерам
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                
                for manager in self.managers:
                    manager_email = manager.get("email")
                    if manager_email:
                        msg['To'] = manager_email
                        server.send_message(msg)
                        logger.info(f"Email notification sent to {manager_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _send_telegram_notification(self, message: str, request_data: Dict[str, Any]) -> bool:
        """
        Отправка Telegram уведомления (заглушка для будущей реализации)
        
        Args:
            message: Сообщение
            request_data: Данные заявки
            
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # TODO: Реализовать отправку в Telegram
            # Пока просто логируем
            logger.info(f"Telegram notification would be sent: {message[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error sending telegram notification: {e}")
            return False
    
    def get_managers_info(self) -> List[Dict[str, Any]]:
        """
        Получение информации о менеджерах
        
        Returns:
            List[Dict[str, Any]]: Список менеджеров
        """
        return self.managers.copy()

class NotificationConfig:
    """Конфигурация уведомлений"""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        Получение конфигурации по умолчанию
        
        Returns:
            Dict[str, Any]: Конфигурация уведомлений
        """
        return {
            "managers": [
                {
                    "name": "Зарубина Анна",
                    "email": "anna@optfm.ru",
                    "phone": "+7 920 350-88-86",
                    "telegram_id": None
                },
                {
                    "name": "Мальцев Александр", 
                    "email": "alexander@optfm.ru",
                    "phone": "+7 920 352-07-79",
                    "telegram_id": None
                },
                {
                    "name": "Кочеткова Ульяна",
                    "email": "ulyana@optfm.ru", 
                    "phone": "+7 930 357-13-10",
                    "telegram_id": None
                }
            ],
            "email": {
                "enabled": False,  # По умолчанию отключено
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "bot@optfm.ru"
            },
            "telegram": {
                "enabled": False,  # По умолчанию отключено
                "bot_token": "",
                "chat_ids": []
            }
        }
