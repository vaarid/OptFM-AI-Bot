"""
Enhanced FAQ Manager Module for OptFM AI Bot
Улучшенная версия с более умным поиском и обработкой запросов
"""
import json
import logging
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class EnhancedFAQManager:
    """Улучшенный менеджер для работы с часто задаваемыми вопросами"""
    
    def __init__(self, faq_file: str = "data/faq_enhanced.json"):
        """
        Инициализация улучшенного FAQ менеджера
        
        Args:
            faq_file: Путь к файлу с FAQ данными
        """
        self.faq_file = Path(faq_file)
        self.faq_data = []
        self._load_faq()
        
        # Создаем индекс для быстрого поиска
        self._build_search_index()
        
    def _load_faq(self):
        """Загрузка FAQ данных из файла"""
        try:
            if self.faq_file.exists():
                with open(self.faq_file, 'r', encoding='utf-8') as f:
                    self.faq_data = json.load(f)
                logger.info(f"Загружено {len(self.faq_data)} FAQ записей из {self.faq_file}")
            else:
                logger.warning(f"FAQ файл не найден: {self.faq_file}")
                self.faq_data = self._get_default_faq()
        except Exception as e:
            logger.error(f"Ошибка загрузки FAQ: {e}")
            self.faq_data = self._get_default_faq()
    
    def _build_search_index(self):
        """Создание индекса для быстрого поиска"""
        self.search_index = {}
        
        for faq in self.faq_data:
            # Индексируем по ключевым словам
            for keyword in faq.get("keywords", []):
                keyword_lower = keyword.lower()
                if keyword_lower not in self.search_index:
                    self.search_index[keyword_lower] = []
                self.search_index[keyword_lower].append(faq["id"])
            
            # Индексируем по словам из вопроса
            question_words = re.findall(r'\w+', faq["question"].lower())
            for word in question_words:
                if len(word) > 2:  # Игнорируем короткие слова
                    if word not in self.search_index:
                        self.search_index[word] = []
                    if faq["id"] not in self.search_index[word]:
                        self.search_index[word].append(faq["id"])
    
    def _get_default_faq(self) -> List[Dict]:
        """Возвращает базовый набор FAQ для OptFM (fallback)"""
        return [
            {
                "id": 1,
                "question": "Что такое OptFM?",
                "keywords": ["компания", "optfm", "fashion mobile", "чем занимаетесь"],
                "answer": "OptFM (Fashion Mobile) — это оптовая платформа с аксессуарами и комплектующими для мобильной и компьютерной электроники. Мы работаем на рынке уже 22 года."
            }
        ]
    
    def search_faq(self, query: str) -> Optional[Dict]:
        """
        Улучшенный поиск ответа в FAQ по запросу
        
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
        
        # 1. Поиск по точному совпадению вопроса
        exact_match = self._find_exact_match(query_lower)
        if exact_match:
            logger.info(f"Найдено точное совпадение: {exact_match['id']}")
            return exact_match
        
        # 2. Поиск по индексу ключевых слов
        keyword_match = self._find_by_keywords(query_words)
        if keyword_match:
            logger.info(f"Найдено совпадение по ключевым словам: {keyword_match['id']}")
            return keyword_match
        
        # 3. Поиск по сходству (fuzzy search)
        similarity_match = self._find_by_similarity(query_lower, query_words)
        if similarity_match:
            logger.info(f"Найдено совпадение по сходству: {similarity_match['id']}")
            return similarity_match
        
        logger.info("Совпадений не найдено")
        return None
    
    def _find_exact_match(self, query: str) -> Optional[Dict]:
        """Поиск точного совпадения"""
        for faq in self.faq_data:
            if query in faq["question"].lower():
                return faq
        return None
    
    def _find_by_keywords(self, query_words: List[str]) -> Optional[Dict]:
        """Поиск по ключевым словам с использованием индекса"""
        if not query_words:
            return None
        
        # Подсчитываем совпадения для каждого FAQ
        faq_scores = {}
        
        for word in query_words:
            if word in self.search_index:
                for faq_id in self.search_index[word]:
                    if faq_id not in faq_scores:
                        faq_scores[faq_id] = 0
                    faq_scores[faq_id] += 1
        
        # Находим FAQ с максимальным количеством совпадений
        if faq_scores:
            best_faq_id = max(faq_scores, key=faq_scores.get)
            best_score = faq_scores[best_faq_id]
            
            # Порог релевантности: минимум 1 совпадение
            if best_score >= 1:
                return self._get_faq_by_id(best_faq_id)
        
        return None
    
    def _find_by_similarity(self, query: str, query_words: List[str]) -> Optional[Dict]:
        """Поиск по сходству текста"""
        best_match = None
        best_score = 0
        
        for faq in self.faq_data:
            # Сравниваем с вопросом
            question_score = SequenceMatcher(None, query, faq["question"].lower()).ratio()
            
            # Сравниваем с ключевыми словами
            keyword_score = self._calculate_keyword_similarity(query_words, faq.get("keywords", []))
            
            # Общий скор
            total_score = (question_score * 0.6) + (keyword_score * 0.4)
            
            if total_score > best_score and total_score > 0.3:  # Порог сходства
                best_score = total_score
                best_match = faq
        
        return best_match
    
    def _calculate_keyword_similarity(self, query_words: List[str], keywords: List[str]) -> float:
        """Вычисление сходства по ключевым словам"""
        if not keywords or not query_words:
            return 0.0
        
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
                    word.startswith(keyword_lower) or
                    SequenceMatcher(None, keyword_lower, word).ratio() > 0.8):
                    matches += 1
                    break
        
        return matches / total_keywords if total_keywords > 0 else 0.0
    
    def _get_faq_by_id(self, faq_id: int) -> Optional[Dict]:
        """Получение FAQ по ID (приватный метод)"""
        for faq in self.faq_data:
            if faq["id"] == faq_id:
                return faq
        return None
    
    def get_faq_by_id(self, faq_id: int) -> Optional[Dict]:
        """
        Получение FAQ по ID (публичный метод)
        
        Args:
            faq_id: ID FAQ
            
        Returns:
            FAQ запись или None если не найдена
        """
        return self._get_faq_by_id(faq_id)
    
    def get_all_faq(self) -> List[Dict]:
        """Возвращает все FAQ записи"""
        return self.faq_data.copy()
    
    def get_faq_by_category(self, category: str) -> List[Dict]:
        """
        Получение FAQ по категории
        
        Args:
            category: Категория (например, 'доставка', 'оплата', 'контакты')
            
        Returns:
            Список FAQ в указанной категории
        """
        category_lower = category.lower()
        result = []
        
        for faq in self.faq_data:
            # Проверяем ключевые слова на принадлежность к категории
            keywords_lower = [kw.lower() for kw in faq.get("keywords", [])]
            if any(category_lower in kw or kw in category_lower for kw in keywords_lower):
                result.append(faq)
        
        return result
    
    def search_similar_questions(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Поиск похожих вопросов
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            Список похожих FAQ
        """
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        # Вычисляем сходство для всех FAQ
        similarities = []
        for faq in self.faq_data:
            question_score = SequenceMatcher(None, query_lower, faq["question"].lower()).ratio()
            keyword_score = self._calculate_keyword_similarity(query_words, faq.get("keywords", []))
            total_score = (question_score * 0.6) + (keyword_score * 0.4)
            
            if total_score > 0.1:  # Минимальный порог
                similarities.append((faq, total_score))
        
        # Сортируем по сходству и возвращаем топ результаты
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [faq for faq, score in similarities[:limit]]
    
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
            self._build_search_index()  # Перестраиваем индекс
            self._save_faq()
            logger.info(f"Добавлен новый FAQ: {new_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления FAQ: {e}")
            return False
    
    def update_faq(self, faq_id: int, question: str = None, answer: str = None, keywords: List[str] = None) -> bool:
        """
        Обновление существующего FAQ
        
        Args:
            faq_id: ID FAQ для обновления
            question: Новый вопрос (опционально)
            answer: Новый ответ (опционально)
            keywords: Новые ключевые слова (опционально)
            
        Returns:
            True если обновлено успешно
        """
        try:
            faq = self._get_faq_by_id(faq_id)
            if not faq:
                logger.error(f"FAQ с ID {faq_id} не найден")
                return False
            
            if question:
                faq["question"] = question
            if answer:
                faq["answer"] = answer
            if keywords:
                faq["keywords"] = keywords
            
            self._build_search_index()  # Перестраиваем индекс
            self._save_faq()
            logger.info(f"Обновлен FAQ: {faq_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления FAQ: {e}")
            return False
    
    def delete_faq(self, faq_id: int) -> bool:
        """
        Удаление FAQ
        
        Args:
            faq_id: ID FAQ для удаления
            
        Returns:
            True если удалено успешно
        """
        try:
            faq = self._get_faq_by_id(faq_id)
            if not faq:
                logger.error(f"FAQ с ID {faq_id} не найден")
                return False
            
            self.faq_data = [f for f in self.faq_data if f["id"] != faq_id]
            self._build_search_index()  # Перестраиваем индекс
            self._save_faq()
            logger.info(f"Удален FAQ: {faq_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления FAQ: {e}")
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
    
    def get_statistics(self) -> Dict:
        """Получение статистики FAQ"""
        total_faq = len(self.faq_data)
        total_keywords = sum(len(faq.get("keywords", [])) for faq in self.faq_data)
        avg_keywords = total_keywords / total_faq if total_faq > 0 else 0
        
        return {
            "total_faq": total_faq,
            "total_keywords": total_keywords,
            "average_keywords_per_faq": round(avg_keywords, 2),
            "search_index_size": len(self.search_index)
        }
