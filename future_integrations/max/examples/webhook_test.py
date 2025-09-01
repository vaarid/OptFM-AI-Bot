#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с MAX мессенджером

Этот скрипт поможет протестировать webhook обработчик и MAX бота
без необходимости настройки реального MAX API.
"""
import asyncio
import json
import aiohttp
import time
from typing import Dict, Any

# Конфигурация для тестирования
TEST_CONFIG = {
    "base_url": "http://localhost:8000",  # URL вашего FastAPI сервера
    "webhook_path": "/webhook/max/",
    "status_path": "/webhook/max/status",
    "test_path": "/webhook/max/test",
}

# Тестовые данные
TEST_MESSAGES = [
    {
        "description": "Приветствие",
        "message": {
            "message_id": 1,
            "from": {
                "id": "test_user_1",
                "first_name": "Иван",
                "username": "ivan_test"
            },
            "chat": {
                "id": "test_chat_1",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "Привет!"
        }
    },
    {
        "description": "Вопрос о товарах",
        "message": {
            "message_id": 2,
            "from": {
                "id": "test_user_2",
                "first_name": "Анна",
                "username": "anna_test"
            },
            "chat": {
                "id": "test_chat_2",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "Какие у вас есть товары?"
        }
    },
    {
        "description": "Вопрос о ценах",
        "message": {
            "message_id": 3,
            "from": {
                "id": "test_user_3",
                "first_name": "Петр",
                "username": "petr_test"
            },
            "chat": {
                "id": "test_chat_3",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "Сколько стоит доставка?"
        }
    },
    {
        "description": "Прощание",
        "message": {
            "message_id": 4,
            "from": {
                "id": "test_user_4",
                "first_name": "Мария",
                "username": "maria_test"
            },
            "chat": {
                "id": "test_chat_4",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "Спасибо, до свидания!"
        }
    },
    {
        "description": "Короткое сообщение",
        "message": {
            "message_id": 5,
            "from": {
                "id": "test_user_5",
                "first_name": "Алексей",
                "username": "alex_test"
            },
            "chat": {
                "id": "test_chat_5",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "ок"
        }
    }
]

class MaxWebhookTester:
    """Класс для тестирования MAX webhook'ов"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_server_status(self) -> bool:
        """
        Проверка доступности сервера
        
        Returns:
            bool: True если сервер доступен
        """
        try:
            url = f"{self.base_url}/"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Сервер доступен: {data}")
                    return True
                else:
                    print(f"❌ Сервер недоступен: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Ошибка подключения к серверу: {e}")
            return False
    
    async def check_max_status(self) -> Dict[str, Any]:
        """
        Проверка статуса MAX интеграции
        
        Returns:
            dict: Статус интеграции
        """
        try:
            url = f"{self.base_url}{TEST_CONFIG['status_path']}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    status = await response.json()
                    print("📊 Статус MAX интеграции:")
                    for key, value in status.items():
                        print(f"   {key}: {value}")
                    return status
                else:
                    print(f"❌ Ошибка получения статуса: HTTP {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ Ошибка проверки статуса: {e}")
            return {}
    
    async def test_webhook_message(self, test_data: Dict[str, Any]) -> bool:
        """
        Тест обработки сообщения через webhook
        
        Args:
            test_data: Тестовые данные сообщения
            
        Returns:
            bool: True если тест прошел успешно
        """
        try:
            url = f"{self.base_url}{TEST_CONFIG['webhook_path']}"
            
            # Формируем payload как от настоящего MAX webhook'а
            payload = {"message": test_data["message"]}
            
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ {test_data['description']}: {result}")
                    return True
                else:
                    print(f"❌ {test_data['description']}: HTTP {response.status} - {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка тестирования {test_data['description']}: {e}")
            return False
    
    async def test_direct_processing(self, test_data: Dict[str, Any]) -> bool:
        """
        Тест прямой обработки сообщения (без отправки в MAX)
        
        Args:
            test_data: Тестовые данные
            
        Returns:
            bool: True если тест прошел успешно
        """
        try:
            url = f"{self.base_url}{TEST_CONFIG['test_path']}"
            
            # Извлекаем данные для тестового эндпоинта
            message = test_data["message"]
            payload = {
                "text": message["text"],
                "user_name": message["from"]["first_name"],
                "user_id": message["from"]["id"],
                "chat_id": message["chat"]["id"]
            }
            
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ Тест {test_data['description']}:")
                    print(f"   Запрос: {payload['text']}")
                    print(f"   Ответ: {result['bot_response'][:100]}...")
                    return True
                else:
                    print(f"❌ Тест {test_data['description']}: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка прямого тестирования {test_data['description']}: {e}")
            return False

async def run_basic_tests():
    """Запуск базовых тестов"""
    print("🧪 Запуск тестов MAX webhook'а")
    print("=" * 50)
    
    async with MaxWebhookTester(TEST_CONFIG["base_url"]) as tester:
        # Проверка доступности сервера
        print("\n1️⃣ Проверка доступности сервера...")
        if not await tester.check_server_status():
            print("❌ Сервер недоступен. Убедитесь что FastAPI запущен на localhost:8000")
            return False
        
        # Проверка статуса MAX интеграции
        print("\n2️⃣ Проверка статуса MAX интеграции...")
        status = await tester.check_max_status()
        
        # Проверка прямой обработки сообщений
        print("\n3️⃣ Тестирование прямой обработки сообщений...")
        success_count = 0
        
        for test_data in TEST_MESSAGES:
            success = await tester.test_direct_processing(test_data)
            if success:
                success_count += 1
            await asyncio.sleep(0.5)  # Небольшая пауза между тестами
        
        print(f"\n✅ Успешно: {success_count}/{len(TEST_MESSAGES)} тестов")
        
        # Тестирование webhook'ов (если MAX настроен)
        if status.get("api_key_configured"):
            print("\n4️⃣ Тестирование webhook обработчика...")
            webhook_success = 0
            
            for test_data in TEST_MESSAGES:
                success = await tester.test_webhook_message(test_data)
                if success:
                    webhook_success += 1
                await asyncio.sleep(0.5)
            
            print(f"\n✅ Webhook тесты: {webhook_success}/{len(TEST_MESSAGES)}")
        else:
            print("\n⚠️ MAX API не настроен, webhook тесты пропущены")
        
        return True

async def run_load_test():
    """Нагрузочное тестирование"""
    print("\n🚀 Запуск нагрузочного тестирования...")
    print("=" * 50)
    
    async with MaxWebhookTester(TEST_CONFIG["base_url"]) as tester:
        tasks = []
        start_time = time.time()
        
        # Создаем множество одновременных запросов
        for i in range(10):
            for test_data in TEST_MESSAGES[:2]:  # Только первые 2 сообщения
                tasks.append(tester.test_direct_processing(test_data))
        
        # Выполняем все задачи одновременно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        successful = sum(1 for r in results if r is True)
        
        print(f"⏱️ Время выполнения: {end_time - start_time:.2f} секунд")
        print(f"✅ Успешных запросов: {successful}/{len(tasks)}")
        print(f"🚀 RPS: {len(tasks)/(end_time - start_time):.2f}")

async def test_error_cases():
    """Тестирование обработки ошибок"""
    print("\n🔍 Тестирование обработки ошибок...")
    print("=" * 50)
    
    async with MaxWebhookTester(TEST_CONFIG["base_url"]) as tester:
        error_tests = [
            {
                "description": "Пустой payload",
                "payload": {}
            },
            {
                "description": "Некорректный JSON",
                "payload": {"invalid": "data"}
            },
            {
                "description": "Сообщение без текста",
                "payload": {
                    "message": {
                        "message_id": 999,
                        "from": {"id": "test", "first_name": "Test"},
                        "chat": {"id": "test", "type": "private"},
                        "date": int(time.time())
                        # Нет поля "text"
                    }
                }
            }
        ]
        
        for test in error_tests:
            try:
                url = f"{tester.base_url}{TEST_CONFIG['webhook_path']}"
                async with tester.session.post(url, json=test["payload"]) as response:
                    result = await response.json()
                    print(f"📝 {test['description']}: HTTP {response.status} - {result}")
            except Exception as e:
                print(f"❌ {test['description']}: Ошибка - {e}")

def print_setup_instructions():
    """Вывод инструкций по настройке"""
    print("\n📋 ИНСТРУКЦИИ ПО НАСТРОЙКЕ")
    print("=" * 50)
    print("1. Убедитесь что FastAPI сервер запущен:")
    print("   python src/main.py")
    print()
    print("2. Для полного тестирования добавьте в .env:")
    print("   MAX_API_KEY=your_api_key_here")
    print()
    print("3. Запустите этот скрипт:")
    print("   python future_integrations/max/examples/webhook_test.py")
    print()
    print("4. Для проверки в браузере откройте:")
    print("   http://localhost:8000/webhook/max/status")

async def main():
    """Основная функция"""
    print("🤖 Тестирование интеграции OptFM Bot с MAX мессенджером")
    print("=" * 60)
    
    try:
        # Базовые тесты
        await run_basic_tests()
        
        # Тесты ошибок
        await test_error_cases()
        
        # Нагрузочное тестирование
        choice = input("\n❓ Запустить нагрузочное тестирование? (y/n): ")
        if choice.lower() in ['y', 'yes', 'да']:
            await run_load_test()
        
        print("\n🎉 Тестирование завершено!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
    
    print_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main())
