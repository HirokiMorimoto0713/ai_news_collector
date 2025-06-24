"""
Core modules for AI News Collector
"""

from .models import NewsArticle, ProcessedArticle
from .config import ConfigManager
from .logger import get_logger, setup_logging
from .exceptions import AINewsCollectorError, ConfigError, CollectionError

__all__ = [
    "NewsArticle",
    "ProcessedArticle",
    "ConfigManager", 
    "get_logger",
    "setup_logging",
    "AINewsCollectorError",
    "ConfigError",
    "CollectionError",
] 