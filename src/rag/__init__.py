"""
RAG (Retrieval-Augmented Generation) модуль для OptFM AI Bot
"""

from .price_parser import PriceParser
from .product_rag_manager import ProductRAGManager
from .embeddings_manager import EmbeddingsManager

__all__ = ['PriceParser', 'ProductRAGManager', 'EmbeddingsManager']
