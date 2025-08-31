#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенного FAQ Manager
"""
import sys
import os

# Добавляем src в путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from faq.enhanced_faq_manager import EnhancedFAQManager

def test_enhanced_faq():
    """Тестирование улучшенного FAQ Manager"""
    print("🧪 Тестирование улучшенного FAQ Manager для OptFM")
    print("=" * 60)
    
    # Инициализация FAQ Manager
    faq_manager = EnhancedFAQManager()
    
    # Показываем статистику
    stats = faq_manager.get_statistics()
    print(f"📊 Статистика FAQ:")
    print(f"   • Всего вопросов: {stats['total_faq']}")
    print(f"   • Всего ключевых слов: {stats['total_keywords']}")
    print(f"   • Среднее количество ключевых слов на вопрос: {stats['average_keywords_per_faq']}")
    print(f"   • Размер поискового индекса: {stats['search_index_size']}")
    print()
    
    # Тестовые запросы
    test_queries = [
        "какие товары у вас есть",
        "доставка",
        "оплата",
        "контакты",
        "гарантия",
        "цены",
        "регистрация",
        "опт",
        "розница",
        "возврат товара",
        "поступление товара",
        "специальные предложения",
        "ремонт телефонов",
        "api интеграция",
        "персональные данные",
        "рассылка",
        "посмотреть товар",
        "скидки",
        "сроки доставки",
        "качество товаров"
    ]
    
    print("🔍 Тестирование поиска:")
    print("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i:2d}. Запрос: '{query}'")
        
        # Поиск ответа
        result = faq_manager.search_faq(query)
        
        if result:
            print(f"    ✅ Найден ответ: {result['question']}")
            print(f"    📝 ID: {result['id']}")
        else:
            print(f"    ❌ Ответ не найден")
            
            # Поиск похожих вопросов
            similar = faq_manager.search_similar_questions(query, limit=2)
            if similar:
                print(f"    🔍 Похожие вопросы:")
                for j, sim_faq in enumerate(similar, 1):
                    print(f"       {j}. {sim_faq['question']}")
        
        print()
    
    # Тестирование поиска по категориям
    print("📂 Тестирование поиска по категориям:")
    print("-" * 60)
    
    categories = ["доставка", "оплата", "контакты", "гарантия", "опт"]
    
    for category in categories:
        category_faq = faq_manager.get_faq_by_category(category)
        print(f"Категория '{category}': {len(category_faq)} вопросов")
        for faq in category_faq:
            print(f"  • {faq['question']}")
        print()
    
    # Тестирование похожих вопросов
    print("🔍 Тестирование поиска похожих вопросов:")
    print("-" * 60)
    
    similar_test_queries = [
        "как доставить товар",
        "условия оплаты",
        "связаться с менеджером",
        "гарантийные обязательства",
        "оптовые цены"
    ]
    
    for query in similar_test_queries:
        print(f"Запрос: '{query}'")
        similar = faq_manager.search_similar_questions(query, limit=3)
        if similar:
            print("Похожие вопросы:")
            for i, faq in enumerate(similar, 1):
                print(f"  {i}. {faq['question']}")
        else:
            print("  Похожих вопросов не найдено")
        print()
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_enhanced_faq()
