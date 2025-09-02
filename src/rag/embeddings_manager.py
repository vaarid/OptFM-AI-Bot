"""
Менеджер для работы с эмбеддингами товаров
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Менеджер для создания и управления эмбеддингами товаров"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Инициализация менеджера эмбеддингов
        
        Args:
            model_name: Название модели для создания эмбеддингов
        """
        self.model_name = model_name
        self.model = None
        self.cache_dir = "data/price_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def load_model(self) -> None:
        """Загружает модель для создания эмбеддингов"""
        if self.model is None:
            logger.info(f"Загружаем модель: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Модель загружена успешно")
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Создает эмбеддинги для списка текстов
        
        Args:
            texts: Список текстов для создания эмбеддингов
            
        Returns:
            Массив эмбеддингов
        """
        self.load_model()
        
        logger.info(f"Создаем эмбеддинги для {len(texts)} текстов")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        logger.info(f"Эмбеддинги созданы: {embeddings.shape}")
        
        return embeddings
    
    def create_product_embeddings(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Создает эмбеддинги для товаров
        
        Args:
            products: Список товаров
            
        Returns:
            Список товаров с эмбеддингами
        """
        logger.info(f"Создаем эмбеддинги для {len(products)} товаров")
        
        # Подготавливаем тексты для эмбеддингов
        texts = []
        for product in products:
            # Создаем текст для поиска из названия, категории и описания
            search_text = self._create_search_text(product)
            texts.append(search_text)
        
        # Создаем эмбеддинги
        embeddings = self.create_embeddings(texts)
        
        # Добавляем эмбеддинги к товарам
        for i, product in enumerate(products):
            product['embedding'] = embeddings[i].tolist()
            product['search_text'] = texts[i]
        
        logger.info("Эмбеддинги добавлены к товарам")
        return products
    
    def _create_search_text(self, product: Dict[str, Any]) -> str:
        """
        Создает текст для поиска из данных товара
        
        Args:
            product: Данные товара
            
        Returns:
            Текст для создания эмбеддинга
        """
        parts = []
        
        # Добавляем название товара
        if product.get('name'):
            parts.append(product['name'])
        
        # Добавляем категорию
        if product.get('category'):
            parts.append(product['category'])
        
        # Добавляем подкатегорию
        if product.get('subcategory'):
            parts.append(product['subcategory'])
        
        # Добавляем бренд
        if product.get('brand') and product['brand'] != 'Unknown':
            parts.append(product['brand'])
        
        # Добавляем производителей техники
        if product.get('device_manufacturers'):
            for manufacturer in product['device_manufacturers']:
                parts.append(manufacturer)
                # Добавляем варианты написания
                if manufacturer == 'IPHONE':
                    parts.append('iPhone')
                    parts.append('айфон')
                elif manufacturer == 'SAMSUNG':
                    parts.append('Samsung')
                elif manufacturer == 'XIAOMI':
                    parts.append('Xiaomi')
                elif manufacturer == 'HUAWEI':
                    parts.append('Huawei')
                elif manufacturer == 'APPLE':
                    parts.append('Apple')
                    parts.append('Эппл')
        
        # Добавляем описание
        if product.get('description'):
            parts.append(product['description'])
        
        return " ".join(parts)
    
    def save_embeddings_cache(self, products: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Сохраняет товары с эмбеддингами в кэш
        
        Args:
            products: Список товаров с эмбеддингами
            filename: Имя файла (если None, генерируется автоматически)
            
        Returns:
            Путь к сохраненному файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"embeddings_cache_{timestamp}.pkl"
        
        cache_path = os.path.join(self.cache_dir, filename)
        
        cache_data = {
            "products": products,
            "model_name": self.model_name,
            "created_at": datetime.now().isoformat(),
            "total_products": len(products)
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
        
        logger.info(f"Кэш эмбеддингов сохранен: {cache_path}")
        return cache_path
    
    def load_embeddings_cache(self, filename: str) -> List[Dict[str, Any]]:
        """
        Загружает товары с эмбеддингами из кэша
        
        Args:
            filename: Имя файла кэша
            
        Returns:
            Список товаров с эмбеддингами
        """
        cache_path = os.path.join(self.cache_dir, filename)
        
        if not os.path.exists(cache_path):
            raise FileNotFoundError(f"Файл кэша не найден: {cache_path}")
        
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        logger.info(f"Загружен кэш эмбеддингов: {len(cache_data['products'])} товаров")
        return cache_data['products']
    
    def get_embedding_for_query(self, query: str) -> np.ndarray:
        """
        Создает эмбеддинг для поискового запроса
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Эмбеддинг запроса
        """
        self.load_model()
        
        logger.debug(f"Создаем эмбеддинг для запроса: {query}")
        embedding = self.model.encode([query])
        return embedding[0]
    
    def calculate_similarity(self, query_embedding: np.ndarray, product_embedding: np.ndarray) -> float:
        """
        Вычисляет косинусное сходство между запросом и товаром
        
        Args:
            query_embedding: Эмбеддинг запроса
            product_embedding: Эмбеддинг товара
            
        Returns:
            Значение сходства (0-1)
        """
        # Нормализуем векторы
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        product_norm = product_embedding / np.linalg.norm(product_embedding)
        
        # Вычисляем косинусное сходство
        similarity = np.dot(query_norm, product_norm)
        return float(similarity)
    
    def find_similar_products(self, query: str, products: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Находит похожие товары для запроса
        
        Args:
            query: Поисковый запрос
            products: Список товаров с эмбеддингами
            top_k: Количество результатов
            
        Returns:
            Список товаров, отсортированных по сходству
        """
        if not products:
            return []
        
        # Создаем эмбеддинг для запроса
        query_embedding = self.get_embedding_for_query(query)
        
        # Вычисляем сходство для всех товаров
        similarities = []
        for product in products:
            if 'embedding' not in product:
                logger.warning(f"Товар {product.get('id', 'unknown')} не имеет эмбеддинга")
                continue
            
            product_embedding = np.array(product['embedding'])
            similarity = self.calculate_similarity(query_embedding, product_embedding)
            similarities.append((similarity, product))
        
        # Сортируем по сходству (убывание)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Возвращаем top_k результатов
        results = []
        for similarity, product in similarities[:top_k]:
            product_copy = product.copy()
            product_copy['similarity_score'] = similarity
            results.append(product_copy)
        
        logger.info(f"Найдено {len(results)} похожих товаров для запроса: {query}")
        return results
    
    def get_cache_files(self) -> List[str]:
        """Возвращает список файлов кэша эмбеддингов"""
        if not os.path.exists(self.cache_dir):
            return []
        
        return [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
