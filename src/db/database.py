"""
Database connection and session management for OptFM AI Bot
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, database_url: str = None):
        """
        Инициализация менеджера базы данных
        
        Args:
            database_url: URL подключения к базе данных
        """
        if database_url:
            self.database_url = database_url
        else:
            # Используем SQLite для разработки
            self.database_url = "sqlite:///./optfm_bot.db"
        
        # Создаем движок базы данных
        if "sqlite" in self.database_url:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(self.database_url)
        
        # Создаем фабрику сессий
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Создаем таблицы
        self.create_tables()
        
        logger.info(f"Database initialized with URL: {self.database_url}")
    
    def create_tables(self):
        """Создание таблиц в базе данных"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """
        Генератор для получения сессии базы данных
        
        Yields:
            Session: Сессия базы данных
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """
        Получение синхронной сессии базы данных
        
        Returns:
            Session: Сессия базы данных
        """
        return self.SessionLocal()

# Глобальный экземпляр менеджера базы данных
db_manager: DatabaseManager = None

def init_database(database_url: str = None) -> DatabaseManager:
    """
    Инициализация базы данных
    
    Args:
        database_url: URL подключения к базе данных
        
    Returns:
        DatabaseManager: Менеджер базы данных
    """
    global db_manager
    db_manager = DatabaseManager(database_url)
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для FastAPI для получения сессии базы данных
    
    Yields:
        Session: Сессия базы данных
    """
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    yield from db_manager.get_session()
