"""
Парсер для Excel файлов прайса OptFM
"""
import pandas as pd
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceParser:
    """Парсер для обработки Excel файлов прайса OptFM"""
    
    def __init__(self, cache_dir: str = "data/price_cache"):
        """
        Инициализация парсера
        
        Args:
            cache_dir: Директория для кэширования обработанных данных
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def parse_excel_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Парсит Excel файл прайса и возвращает структурированные данные
        
        Args:
            file_path: Путь к Excel файлу
            
        Returns:
            Список товаров в структурированном виде
        """
        logger.info(f"Начинаем парсинг файла: {file_path}")
        
        try:
            # Читаем файл без заголовков
            df = pd.read_excel(file_path, header=None)
            logger.info(f"Файл загружен: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # Ищем заголовки таблицы
            headers_row = self._find_headers_row(df)
            if headers_row is None:
                raise ValueError("Не удалось найти заголовки таблицы")
            
            logger.info(f"Заголовки найдены в строке {headers_row}")
            
            # Извлекаем данные товаров
            products = self._extract_products(df, headers_row)
            logger.info(f"Извлечено {len(products)} товаров")
            
            # Сохраняем в кэш
            self._save_to_cache(products, file_path)
            
            return products
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге файла {file_path}: {e}")
            raise
    
    def _find_headers_row(self, df: pd.DataFrame) -> Optional[int]:
        """
        Ищет строку с заголовками таблицы
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Номер строки с заголовками или None
        """
        for i in range(min(20, len(df))):
            row = df.iloc[i]
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            
            # Ищем признаки заголовков
            if any(keyword in row_str.lower() for keyword in ['номенклатура', 'код', 'наименование']):
                logger.info(f"Найдены заголовки в строке {i}: {row_str}")
                return i
        
        return None
    
    def _extract_products(self, df: pd.DataFrame, headers_row: int) -> List[Dict[str, Any]]:
        """
        Извлекает данные товаров из таблицы
        
        Args:
            df: DataFrame с данными
            headers_row: Номер строки с заголовками
            
        Returns:
            Список товаров
        """
        products = []
        current_category = ""
        current_subcategory = ""
        
        # Получаем заголовки
        headers = df.iloc[headers_row]
        
        # Обрабатываем строки после заголовков
        for i in range(headers_row + 1, len(df)):
            row = df.iloc[i]
            
            # Пропускаем пустые строки
            if row.isna().all():
                continue
            
            # Извлекаем данные из строки
            name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            code = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            price = row.iloc[4] if pd.notna(row.iloc[4]) else None
            
            # Определяем тип строки
            if self._is_category(name):
                current_category = name
                logger.debug(f"Найдена категория: {current_category}")
                continue
            elif self._is_subcategory(name):
                current_subcategory = name
                logger.debug(f"Найдена подкатегория: {current_subcategory}")
                continue
            elif self._is_product(name, code, price):
                # Создаем объект товара
                product = {
                    "id": code,
                    "name": name,
                    "category": current_category,
                    "subcategory": current_subcategory,
                    "price": float(price) if price is not None else None,
                    "brand": self._extract_brand(name),
                    "device_manufacturers": self._extract_device_manufacturers(name),
                    "description": self._create_description(name),
                    "metadata": {
                        "status": "active",
                        "last_updated": datetime.now().isoformat(),
                        "source_file": "price_excel"
                    }
                }
                products.append(product)
        
        return products
    
    def _is_category(self, name: str) -> bool:
        """Определяет, является ли строка категорией"""
        if not name or pd.isna(name):
            return False
        
        # Категории обычно короткие и не содержат коды товаров
        name_lower = name.lower()
        return (
            len(name) < 50 and
            not any(char.isdigit() for char in name) and
            not name.startswith('УТ-') and
            not name.startswith('ФМ-') and
            name not in ['nan', 'None']
        )
    
    def _is_subcategory(self, name: str) -> bool:
        """Определяет, является ли строка подкатегорией"""
        if not name or pd.isna(name):
            return False
        
        # Подкатегории содержат дефис или являются короткими описаниями
        name_lower = name.lower()
        return (
            len(name) < 100 and
            (' - ' in name or name.count('-') == 1) and
            not name.startswith('УТ-') and
            not name.startswith('ФМ-') and
            name not in ['nan', 'None']
        )
    
    def _is_product(self, name: str, code: str, price) -> bool:
        """Определяет, является ли строка товаром"""
        if not name or pd.isna(name) or name in ['nan', 'None']:
            return False
        
        # Товары имеют код и обычно цену
        return (
            len(name) > 10 and
            (code.startswith('УТ-') or code.startswith('ФМ-') or len(code) > 5) and
            price is not None
        )
    
    def _extract_brand(self, name: str) -> str:
        """Извлекает бренд из названия товара"""
        # Простая логика извлечения бренда
        words = name.split()
        for word in words:
            if word.isupper() and len(word) > 2:
                return word
        return "Unknown"
    
    def _extract_device_manufacturers(self, name: str) -> List[str]:
        """Извлекает производителей техники из названия товара"""
        # Список известных производителей техники
        known_manufacturers = [
            'APPLE', 'IPHONE', 'IPAD', 'MACBOOK', 'MAC',
            'SAMSUNG', 'GALAXY', 'NOTE',
            'XIAOMI', 'REDMI', 'POCO', 'MI',
            'HUAWEI', 'HONOR', 'P30', 'P40', 'MATE',
            'OPPO', 'REALME', 'ONEPLUS',
            'VIVO', 'IQOO',
            'NOKIA', 'LUMIA',
            'SONY', 'XPERIA',
            'LG', 'G', 'V',
            'MOTOROLA', 'MOTO',
            'ASUS', 'ZENFONE', 'ROG',
            'LENOVO', 'THINKPAD',
            'DELL', 'LATITUDE', 'INSPIRON',
            'HP', 'PAVILION', 'ELITEBOOK',
            'ACER', 'ASPIRE', 'PREDATOR',
            'MSI', 'GAMING',
            'RAZER', 'BLADE',
            'GOOGLE', 'PIXEL',
            'NINTENDO', 'SWITCH',
            'PLAYSTATION', 'PS4', 'PS5',
            'XBOX', 'MICROSOFT',
            'CANON', 'NIKON',
            'DJI', 'DRONE',
            'GO PRO', 'HERO',
            'JBL', 'BOSE', 'SENNHEISER',
            'BEATS', 'AIRPODS',
            'JABRA', 'PLANTRONICS',
            'LOGITECH',
            'STEELSERIES', 'HYPERX'
        ]
        
        found_manufacturers = []
        name_upper = name.upper()
        
        # Ищем производителей в названии
        for manufacturer in known_manufacturers:
            if manufacturer in name_upper:
                found_manufacturers.append(manufacturer)
        
        # Также ищем паттерны типа "для iPhone", "совместим с Samsung"
        import re
        patterns = [
            r'для\s+([A-Z][A-Za-z]+)',
            r'совместим\s+с\s+([A-Z][A-Za-z]+)',
            r'подходит\s+для\s+([A-Z][A-Za-z]+)',
            r'([A-Z][A-Za-z]+)\s+совместимость',
            r'([A-Z][A-Za-z]+)\s+адаптер',
            r'([A-Z][A-Za-z]+)\s+кабель',
            r'([A-Z][A-Za-z]+)\s+чехол',
            r'([A-Z][A-Za-z]+)\s+стекло'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, name, re.IGNORECASE)
            for match in matches:
                if match.upper() in known_manufacturers:
                    found_manufacturers.append(match.upper())
        
        # Убираем дубликаты и возвращаем
        return list(set(found_manufacturers))
    
    def _create_description(self, name: str) -> str:
        """Создает описание товара из названия"""
        # Убираем бренд и создаем описание
        words = name.split()
        if len(words) > 3:
            return " ".join(words[1:])
        return name
    
    def _save_to_cache(self, products: List[Dict[str, Any]], source_file: str) -> None:
        """
        Сохраняет обработанные данные в кэш
        
        Args:
            products: Список товаров
            source_file: Исходный файл
        """
        cache_file = os.path.join(
            self.cache_dir, 
            f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        cache_data = {
            "source_file": source_file,
            "processed_at": datetime.now().isoformat(),
            "total_products": len(products),
            "products": products
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Данные сохранены в кэш: {cache_file}")
    
    def load_from_cache(self, cache_file: str) -> List[Dict[str, Any]]:
        """
        Загружает данные из кэша
        
        Args:
            cache_file: Имя файла кэша
            
        Returns:
            Список товаров
        """
        cache_path = os.path.join(self.cache_dir, cache_file)
        
        if not os.path.exists(cache_path):
            raise FileNotFoundError(f"Файл кэша не найден: {cache_path}")
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        logger.info(f"Загружено {len(cache_data['products'])} товаров из кэша")
        return cache_data['products']
    
    def get_cache_files(self) -> List[str]:
        """Возвращает список файлов кэша"""
        if not os.path.exists(self.cache_dir):
            return []
        
        return [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
