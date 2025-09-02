"""
RAG менеджер для поиска товаров OptFM
"""
import logging
import chromadb
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime

from .price_parser import PriceParser
from .embeddings_manager import EmbeddingsManager

logger = logging.getLogger(__name__)

class ProductRAGManager:
    """RAG менеджер для поиска товаров OptFM"""
    
    def __init__(self, 
                 chroma_persist_directory: str = "data/chroma_db",
                 cache_dir: str = "data/price_cache"):
        """
        Инициализация RAG менеджера
        
        Args:
            chroma_persist_directory: Директория для ChromaDB
            cache_dir: Директория для кэша
        """
        self.chroma_persist_directory = chroma_persist_directory
        self.cache_dir = cache_dir
        
        # Создаем директории
        os.makedirs(chroma_persist_directory, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        
        # Инициализируем компоненты
        self.price_parser = PriceParser(cache_dir)
        self.embeddings_manager = EmbeddingsManager()
        self.chroma_client = None
        self.collection = None
        
        # Инициализируем ChromaDB
        self._init_chromadb()
        
    def _init_chromadb(self) -> None:
        """Инициализирует ChromaDB клиент и коллекцию"""
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_persist_directory)
            
            # Создаем или получаем коллекцию
            collection_name = "optfm_products"
            try:
                self.collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Подключились к существующей коллекции: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Товары OptFM для поиска"}
                )
                logger.info(f"Создана новая коллекция: {collection_name}")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации ChromaDB: {e}")
            raise
    
    def load_products_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Загружает товары из Excel файла
        
        Args:
            file_path: Путь к Excel файлу
            
        Returns:
            Список товаров
        """
        logger.info(f"Загружаем товары из файла: {file_path}")
        
        # Парсим Excel файл
        products = self.price_parser.parse_excel_file(file_path)
        
        # Создаем эмбеддинги
        products_with_embeddings = self.embeddings_manager.create_product_embeddings(products)
        
        # Сохраняем в кэш
        self.embeddings_manager.save_embeddings_cache(products_with_embeddings)
        
        # Индексируем в ChromaDB
        self._index_products_in_chromadb(products_with_embeddings)
        
        logger.info(f"Загружено и проиндексировано {len(products_with_embeddings)} товаров")
        return products_with_embeddings
    
    def _index_products_in_chromadb(self, products: List[Dict[str, Any]]) -> None:
        """
        Индексирует товары в ChromaDB
        
        Args:
            products: Список товаров с эмбеддингами
        """
        if not products:
            logger.warning("Нет товаров для индексации")
            return
        
        logger.info(f"Индексируем {len(products)} товаров в ChromaDB")
        
        # Подготавливаем данные для ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for product in products:
            if 'embedding' not in product:
                logger.warning(f"Товар {product.get('id', 'unknown')} не имеет эмбеддинга")
                continue
            
            # ID товара
            ids.append(product['id'])
            
            # Эмбеддинг
            embeddings.append(product['embedding'])
            
            # Документ для поиска
            document = self._create_document_text(product)
            documents.append(document)
            
            # Метаданные
            metadata = {
                "name": product.get('name', ''),
                "category": product.get('category', ''),
                "subcategory": product.get('subcategory', ''),
                "brand": product.get('brand', ''),
                "device_manufacturers": ','.join(product.get('device_manufacturers', [])),
                "price": str(product.get('price', '')),
                "description": product.get('description', ''),
                "status": product.get('metadata', {}).get('status', 'active')
            }
            metadatas.append(metadata)
        
        # Добавляем в коллекцию
        if ids:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Добавлено {len(ids)} товаров в ChromaDB")
    
    def _create_document_text(self, product: Dict[str, Any]) -> str:
        """
        Создает текст документа для ChromaDB
        
        Args:
            product: Данные товара
            
        Returns:
            Текст документа
        """
        parts = []
        
        if product.get('name'):
            parts.append(f"Название: {product['name']}")
        
        if product.get('category'):
            parts.append(f"Категория: {product['category']}")
        
        if product.get('subcategory'):
            parts.append(f"Подкатегория: {product['subcategory']}")
        
        if product.get('brand') and product['brand'] != 'Unknown':
            parts.append(f"Бренд: {product['brand']}")
        
        if product.get('description'):
            parts.append(f"Описание: {product['description']}")
        
        if product.get('price'):
            parts.append(f"Цена: {product['price']} ₽")
        
        return " | ".join(parts)
    
    def search_products(self, query: str, top_k: int = 10, 
                       category_filter: Optional[str] = None,
                       brand_filter: Optional[str] = None,
                       device_manufacturer_filter: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Поиск товаров по запросу с улучшенной логикой для производителей
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            category_filter: Фильтр по категории
            brand_filter: Фильтр по бренду
            device_manufacturer_filter: Фильтр по производителю техники
            min_price: Минимальная цена
            max_price: Максимальная цена
            
        Returns:
            Список найденных товаров
        """
        logger.info(f"Поиск товаров: '{query}' (top_k={top_k})")
        
        # Улучшенная логика поиска для производителей
        query_lower = query.lower().strip()
        
        # Если запрос похож на производителя, увеличиваем количество результатов
        # и применяем специальную логику
        is_manufacturer_search = self._is_manufacturer_query(query_lower)
        
        if is_manufacturer_search:
            # Для поиска по производителю увеличиваем количество результатов
            search_top_k = min(top_k * 2, 20)
            logger.info(f"Поиск по производителю '{query}', увеличен top_k до {search_top_k}")
        else:
            search_top_k = top_k
        
        # Создаем эмбеддинг для запроса
        query_embedding = self.embeddings_manager.get_embedding_for_query(query)
        
        # Подготавливаем фильтры для ChromaDB
        where_filter = {}
        if category_filter:
            where_filter["category"] = category_filter
        if brand_filter:
            where_filter["brand"] = brand_filter
        
        # Выполняем поиск в ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=search_top_k,
            where=where_filter if where_filter else None
        )
        
        # Формируем результат
        products = []
        if results['ids'] and results['ids'][0]:
            for i, product_id in enumerate(results['ids'][0]):
                product = {
                    "id": product_id,
                    "name": results['metadatas'][0][i].get('name', ''),
                    "category": results['metadatas'][0][i].get('category', ''),
                    "subcategory": results['metadatas'][0][i].get('subcategory', ''),
                    "brand": results['metadatas'][0][i].get('brand', ''),
                    "device_manufacturers": results['metadatas'][0][i].get('device_manufacturers', '').split(',') if results['metadatas'][0][i].get('device_manufacturers') else [],
                    "price": "Уточняйте у менеджера",  # Заглушка вместо реальной цены
                    "description": results['metadatas'][0][i].get('description', ''),
                    "similarity_score": results['distances'][0][i] if results['distances'] else 0.0,
                    "document": results['documents'][0][i] if results['documents'] else ''
                }
                products.append(product)
        
        # Улучшенная фильтрация для производителей
        if is_manufacturer_search or device_manufacturer_filter:
            filtered_products = []
            target_manufacturer = device_manufacturer_filter or query_lower
            
            for product in products:
                # Проверяем производителей в названии товара и в device_manufacturers
                product_manufacturers = [m.lower().strip() for m in product.get('device_manufacturers', [])]
                product_name_lower = product.get('name', '').lower()
                
                # Проверяем точное совпадение или частичное совпадение
                if (target_manufacturer in product_manufacturers or 
                    target_manufacturer in product_name_lower or
                    any(target_manufacturer in m for m in product_manufacturers)):
                    filtered_products.append(product)
            
            products = filtered_products
        
        # Ограничиваем количество результатов
        products = products[:top_k]
        
        logger.info(f"Найдено {len(products)} товаров")
        return products
    
    def _is_manufacturer_query(self, query: str) -> bool:
        """
        Определяет, является ли запрос поиском по производителю
        
        Args:
            query: Поисковый запрос
            
        Returns:
            True, если запрос похож на производителя
        """
        # Список известных производителей
        known_manufacturers = [
            'samsung', 'iphone', 'apple', 'xiaomi', 'huawei', 'honor', 'oppo', 'realme',
            'oneplus', 'nokia', 'motorola', 'lg', 'sony', 'asus', 'acer', 'lenovo',
            'hp', 'dell', 'toshiba', 'canon', 'nikon', 'panasonic', 'sharp', 'philips'
        ]
        
        # Проверяем точное совпадение
        if query in known_manufacturers:
            return True
        
        # Проверяем частичное совпадение
        for manufacturer in known_manufacturers:
            if manufacturer in query or query in manufacturer:
                return True
        
        return False
    
    def get_categories(self) -> List[str]:
        """Возвращает список всех категорий"""
        try:
            # Получаем все метаданные из коллекции
            results = self.collection.get()
            categories = set()
            
            for metadata in results['metadatas']:
                if metadata.get('category'):
                    categories.add(metadata['category'])
            
            return sorted(list(categories))
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []
    
    def get_brands(self) -> List[str]:
        """Возвращает список всех брендов"""
        try:
            results = self.collection.get()
            brands = set()
            
            for metadata in results['metadatas']:
                if metadata.get('brand') and metadata['brand'] != 'Unknown':
                    brands.add(metadata['brand'])
            
            return sorted(list(brands))
        except Exception as e:
            logger.error(f"Ошибка получения брендов: {e}")
            return []
    
    def get_device_manufacturers(self) -> List[str]:
        """Возвращает список всех производителей техники"""
        try:
            results = self.collection.get()
            manufacturers = set()
            
            for metadata in results['metadatas']:
                if metadata.get('device_manufacturers'):
                    manufacturer_list = metadata['device_manufacturers'].split(',')
                    for manufacturer in manufacturer_list:
                        if manufacturer.strip():
                            manufacturers.add(manufacturer.strip())
            
            return sorted(list(manufacturers))
        except Exception as e:
            logger.error(f"Ошибка получения производителей техники: {e}")
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает товар по точному ID
        
        Args:
            product_id: ID товара
            
        Returns:
            Данные товара или None, если не найден
        """
        try:
            results = self.collection.get(
                ids=[product_id],
                limit=1
            )
            
            if results['ids'] and results['ids'][0]:
                metadata = results['metadatas'][0]
                product = {
                    "id": product_id,
                    "name": metadata.get('name', ''),
                    "category": metadata.get('category', ''),
                    "subcategory": metadata.get('subcategory', ''),
                    "brand": metadata.get('brand', ''),
                    "device_manufacturers": metadata.get('device_manufacturers', '').split(',') if metadata.get('device_manufacturers') else [],
                    "price": "Уточняйте у менеджера",  # Заглушка вместо реальной цены
                    "description": metadata.get('description', ''),
                    "document": results['documents'][0] if results['documents'] else ''
                }
                return product
            
            return None
        except Exception as e:
            logger.error(f"Ошибка получения товара по ID {product_id}: {e}")
            return None
    
    def get_products_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает товары по категории
        
        Args:
            category: Название категории
            limit: Максимальное количество товаров
            
        Returns:
            Список товаров
        """
        try:
            results = self.collection.get(
                where={"category": category},
                limit=limit
            )
            
            products = []
            for i, product_id in enumerate(results['ids']):
                product = {
                    "id": product_id,
                    "name": results['metadatas'][i].get('name', ''),
                    "category": results['metadatas'][i].get('category', ''),
                    "subcategory": results['metadatas'][i].get('subcategory', ''),
                    "brand": results['metadatas'][i].get('brand', ''),
                    "price": "Уточняйте у менеджера",  # Заглушка вместо реальной цены
                    "description": results['metadatas'][i].get('description', '')
                }
                products.append(product)
            
            return products
        except Exception as e:
            logger.error(f"Ошибка получения товаров по категории {category}: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Возвращает статистику коллекции"""
        try:
            results = self.collection.get()
            total_products = len(results['ids']) if results['ids'] else 0
            
            # Подсчитываем статистику
            categories = {}
            brands = {}
            price_range = {"min": float('inf'), "max": 0}
            
            for metadata in results['metadatas']:
                # Категории
                category = metadata.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Бренды
                brand = metadata.get('brand', 'Unknown')
                brands[brand] = brands.get(brand, 0) + 1
                
                # Цены
                try:
                    price = float(metadata.get('price', 0))
                    if price > 0:
                        price_range["min"] = min(price_range["min"], price)
                        price_range["max"] = max(price_range["max"], price)
                except:
                    pass
            
            return {
                "total_products": total_products,
                "categories_count": len(categories),
                "brands_count": len(brands),
                "price_range": price_range if price_range["min"] != float('inf') else {"min": 0, "max": 0},
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}
    
    def clear_collection(self) -> None:
        """Очищает коллекцию"""
        try:
            # Получаем все ID из коллекции
            results = self.collection.get()
            if results['ids']:
                # Удаляем все документы
                self.collection.delete(ids=results['ids'])
                logger.info(f"Удалено {len(results['ids'])} документов из коллекции")
            else:
                logger.info("Коллекция уже пустая")
            
            logger.info("Коллекция очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки коллекции: {e}")
            raise
