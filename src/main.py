"""
OptFM AI Bot - Main Application Entry Point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="OptFM AI Bot",
    description="Интеллектуальный бот для OptFM",
    version="1.0.0"
)

# Настройка CORS для web-виджета
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работы API"""
    return {"message": "OptFM AI Bot is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья сервиса"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
