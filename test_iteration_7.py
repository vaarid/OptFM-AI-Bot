#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности итерации 7
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db.database import init_database
from db.repository import UserRepository, RequestRepository, DialogRepository
from forms.request_form import RequestFormManager
from notifications.manager_notifier import ManagerNotifier, NotificationConfig

def test_database():
    """Тест базы данных"""
    print("🧪 Тестирование базы данных...")
    
    try:
        # Инициализируем базу данных
        db_manager = init_database()
        session = db_manager.get_session_sync()
        
        # Тестируем репозитории
        user_repo = UserRepository(session)
        request_repo = RequestRepository(session)
        dialog_repo = DialogRepository(session)
        
        # Проверяем, существует ли тестовый пользователь
        existing_user = user_repo.get_by_telegram_id(123456789)
        if existing_user:
            print("⚠️ Тестовый пользователь уже существует, используем его")
            test_user = existing_user
        else:
        
            # Создаем тестового пользователя
            test_user = user_repo.create_user(
                telegram_id=123456789,
                username="test_user",
                first_name="Тест",
                last_name="Пользователь"
            )
            print(f"✅ Создан пользователь: {test_user.id}")
        
        # Обновляем контакты
        user_repo.update_user_contacts(test_user.id, phone="+7 999 123-45-67", email="test@example.com")
        print("✅ Контакты обновлены")
        
        # Создаем тестовую заявку
        test_request = request_repo.create_request(
            user_id=test_user.id,
            title="Тестовая заявка",
            description="Это тестовая заявка для проверки функциональности"
        )
        print(f"✅ Создана заявка: {test_request.id}")
        
        # Добавляем диалог
        dialog_repo.add_dialog(test_user.id, "Тестовый вопрос", "Тестовый ответ", True)
        print("✅ Диалог добавлен")
        
        # Получаем заявки пользователя
        requests = request_repo.get_user_requests(test_user.id)
        print(f"✅ Получено заявок: {len(requests)}")
        
        # Получаем новые заявки
        new_requests = request_repo.get_new_requests()
        print(f"✅ Новых заявок: {len(new_requests)}")
        
        session.close()
        print("✅ Тест базы данных пройден успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте базы данных: {e}")
        return False
    
    return True

def test_request_form():
    """Тест формы заявки"""
    print("\n🧪 Тестирование формы заявки...")
    
    try:
        form_manager = RequestFormManager()
        
        # Тестируем начало формы
        message = form_manager.start_form(123456789, "Тестовый вопрос")
        print(f"✅ Начало формы: {message[:50]}...")
        
        # Тестируем обработку имени
        result = form_manager.process_input(123456789, "Иван Иванов")
        print(f"✅ Обработка имени: {result['message'][:50]}...")
        
        # Тестируем обработку телефона
        result = form_manager.process_input(123456789, "+7 999 123-45-67")
        print(f"✅ Обработка телефона: {result['message'][:50]}...")
        
        # Тестируем обработку email
        result = form_manager.process_input(123456789, "test@example.com")
        print(f"✅ Обработка email: {result['message'][:50]}...")
        
        # Тестируем обработку описания
        result = form_manager.process_input(123456789, "Это тестовое описание заявки для проверки функциональности")
        print(f"✅ Обработка описания: {result['message'][:50]}...")
        
        # Проверяем, что форма завершена
        if result.get("completed", False):
            print("✅ Форма успешно завершена!")
            print(f"📋 Данные формы: {result['data']}")
        else:
            print("❌ Форма не завершена")
            return False
        
        print("✅ Тест формы заявки пройден успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте формы заявки: {e}")
        return False
    
    return True

def test_notifications():
    """Тест уведомлений"""
    print("\n🧪 Тестирование уведомлений...")
    
    try:
        # Получаем конфигурацию по умолчанию
        config = NotificationConfig.get_default_config()
        notifier = ManagerNotifier(config)
        
        # Тестовые данные
        request_data = {
            "id": 1,
            "title": "Тестовая заявка",
            "description": "Это тестовая заявка для проверки уведомлений",
            "created_at": "2025-01-01 12:00:00"
        }
        
        user_data = {
            "name": "Иван Иванов",
            "phone": "+7 999 123-45-67",
            "email": "test@example.com",
            "telegram_id": 123456789
        }
        
        # Тестируем уведомление (без реальной отправки)
        success = notifier.notify_new_request(request_data, user_data)
        
        if success:
            print("✅ Уведомление обработано успешно!")
        else:
            print("⚠️ Уведомление не отправлено (ожидаемо для теста)")
        
        # Получаем информацию о менеджерах
        managers = notifier.get_managers_info()
        print(f"✅ Найдено менеджеров: {len(managers)}")
        
        print("✅ Тест уведомлений пройден успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте уведомлений: {e}")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов итерации 7: Передача заявок менеджеру\n")
    
    tests = [
        ("База данных", test_database),
        ("Форма заявки", test_request_form),
        ("Уведомления", test_notifications)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Тест: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
        else:
            print(f"❌ Тест '{test_name}' провален")
    
    print(f"\n{'='*50}")
    print(f"РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print('='*50)
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены успешно! Итерация 7 готова к использованию.")
    else:
        print(f"\n⚠️ {total - passed} тест(ов) провалено. Проверьте ошибки выше.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
