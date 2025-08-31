"""
FAQ Manager Module for OptFM AI Bot
"""
import json
import logging
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class FAQManager:
    """Менеджер для работы с часто задаваемыми вопросами"""
    
    def __init__(self, faq_file: str = "data/faq.json"):
        """
        Инициализация FAQ менеджера
        
        Args:
            faq_file: Путь к файлу с FAQ данными
        """
        self.faq_file = Path(faq_file)
        self.faq_data = []
        self._load_faq()
        
    def _load_faq(self):
        """Загрузка FAQ данных из файла"""
        try:
            if self.faq_file.exists():
                with open(self.faq_file, 'r', encoding='utf-8') as f:
                    self.faq_data = json.load(f)
                logger.info(f"Загружено {len(self.faq_data)} FAQ записей")
            else:
                logger.warning(f"FAQ файл не найден: {self.faq_file}")
                self.faq_data = self._get_default_faq()
        except Exception as e:
            logger.error(f"Ошибка загрузки FAQ: {e}")
            self.faq_data = self._get_default_faq()
    
    def _get_default_faq(self) -> List[Dict]:
        """Возвращает базовый набор FAQ для OptFM"""
        return [
            {
                "id": 1,
                "question": "Какие продукты вы предлагаете?",
                "keywords": ["продукты", "товары", "ассортимент", "что продаете", "каталог", "есть", "предлагаете", "продаете"],
                "answer": "Компания OptFM предлагает широкий ассортимент продуктов для вашего бизнеса. У нас есть:\n\n• Промышленное оборудование\n• Электронные компоненты\n• Инструменты и материалы\n• Специализированные решения\n\nДля получения актуального прайса и подробной информации, напишите ваш конкретный запрос."
            },
            {
                "id": 2,
                "question": "Как с вами связаться?",
                "keywords": ["контакты", "связаться", "телефон", "email", "адрес", "где находитесь"],
                "answer": "Связаться с OptFM можно следующими способами:\n\n📞 Телефон: +7 (XXX) XXX-XX-XX\n📧 Email: info@optfm.ru\n🌐 Сайт: www.optfm.ru\n📍 Адрес: [Адрес офиса]\n\n⏰ Режим работы: Пн-Пт 9:00-18:00\n\nДля срочных вопросов оставьте заявку, и наш менеджер свяжется с вами в ближайшее время."
            },
            {
                "id": 3,
                "question": "Какие у вас цены?",
                "keywords": ["цены", "стоимость", "прайс", "сколько стоит", "цена", "у вас", "ваши", "стоит"],
                "answer": "Цены на наши продукты зависят от объема заказа, спецификации и текущих рыночных условий. Для получения актуального прайса:\n\n• Укажите конкретный продукт или категорию\n• Сообщите требуемое количество\n• Укажите сроки поставки\n\nЯ помогу найти подходящие варианты и передам ваш запрос менеджеру для расчета."
            },
            {
                "id": 4,
                "question": "Есть ли доставка?",
                "keywords": ["доставка", "отправка", "транспорт", "курьер", "самовывоз"],
                "answer": "Да, OptFM предоставляет различные варианты доставки:\n\n🚚 Доставка по городу\n📦 Отправка в регионы\n🏪 Самовывоз со склада\n\nСтоимость и сроки доставки зависят от:\n• Места назначения\n• Веса и габаритов\n• Срочности\n\nУточните детали заказа, и я предоставлю информацию по доставке."
            },
            {
                "id": 5,
                "question": "Какие гарантии вы предоставляете?",
                "keywords": ["гарантия", "возврат", "обмен", "качество", "сервис", "качеств", "гаранти"],
                "answer": "OptFM предоставляет полную гарантию на все продукты:\n\n✅ Гарантийный срок согласно техническим условиям\n✅ Возможность возврата в течение 14 дней\n✅ Техническая поддержка\n✅ Сервисное обслуживание\n\nВсе товары сертифицированы и соответствуют российским стандартам качества."
            },
            {
                "id": 6,
                "question": "Работаете ли вы с юридическими лицами?",
                "keywords": ["юридические лица", "организации", "компании", "бизнес", "опт"],
                "answer": "Да, OptFM работает как с физическими, так и с юридическими лицами:\n\n🏢 Для организаций:\n• Безналичный расчет\n• Договорные отношения\n• Специальные условия для постоянных клиентов\n• Отсрочка платежа (по согласованию)\n\n👤 Для частных лиц:\n• Наличный и безналичный расчет\n• Удобные способы оплаты\n\nОставьте заявку, и менеджер свяжется для обсуждения условий сотрудничества."
            }
        ]
    
    def search_faq(self, query: str) -> Optional[Dict]:
        """
        Поиск ответа в FAQ по запросу
        
        Args:
            query: Поисковый запрос пользователя
            
        Returns:
            Dict с найденным FAQ или None
        """
        if not query or not self.faq_data:
            return None
        
        # Нормализация запроса
        query_lower = query.lower().strip()
        query_words = re.findall(r'\w+', query_lower)
        
        logger.info(f"Поиск FAQ для запроса: '{query}' (слова: {query_words})")
        
        # Поиск по точному совпадению вопроса
        for faq in self.faq_data:
            if query_lower in faq["question"].lower():
                logger.info(f"Найдено точное совпадение: {faq['id']}")
                return faq
        
        # Поиск по ключевым словам
        best_match = None
        best_score = 0
        
        for faq in self.faq_data:
            score = self._calculate_keyword_score(query_words, faq["keywords"])
            logger.info(f"FAQ {faq['id']} - score: {score:.2f} (keywords: {faq['keywords']})")
            if score > best_score:
                best_score = score
                best_match = faq
        
        # Снижаем порог релевантности для лучшего поиска
        if best_score >= 0.1:  # Более мягкий порог
            logger.info(f"Найдено совпадение по ключевым словам: {best_match['id']} (score: {best_score:.2f})")
            return best_match
        
        logger.info(f"Совпадений не найдено (лучший score: {best_score:.2f})")
        return None
    
    def _calculate_keyword_score(self, query_words: List[str], keywords: List[str]) -> float:
        """
        Вычисление релевантности запроса к ключевым словам
        
        Args:
            query_words: Слова из запроса
            keywords: Список ключевых слов
            
        Returns:
            Оценка релевантности от 0 до 1
        """
        if not keywords or not query_words:
            return 0.0
        
        # Подсчитываем совпадения
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for word in query_words:
                # Проверяем различные варианты совпадений
                if (keyword_lower == word or 
                    keyword_lower in word or 
                    word in keyword_lower or
                    keyword_lower.startswith(word) or
                    word.startswith(keyword_lower)):
                    matches += 1
                    break
        
        score = matches / total_keywords if total_keywords > 0 else 0.0
        return score
    
    def get_all_faq(self) -> List[Dict]:
        """Возвращает все FAQ записи"""
        return self.faq_data.copy()
    
    def add_faq(self, question: str, answer: str, keywords: List[str] = None) -> bool:
        """
        Добавление нового FAQ
        
        Args:
            question: Вопрос
            answer: Ответ
            keywords: Ключевые слова
            
        Returns:
            True если добавлено успешно
        """
        try:
            new_id = max([faq["id"] for faq in self.faq_data], default=0) + 1
            new_faq = {
                "id": new_id,
                "question": question,
                "answer": answer,
                "keywords": keywords or []
            }
            
            self.faq_data.append(new_faq)
            self._save_faq()
            logger.info(f"Добавлен новый FAQ: {new_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления FAQ: {e}")
            return False
    
    def _save_faq(self):
        """Сохранение FAQ в файл"""
        try:
            # Создаем директорию если не существует
            self.faq_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.faq_file, 'w', encoding='utf-8') as f:
                json.dump(self.faq_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"FAQ сохранен в {self.faq_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения FAQ: {e}")
