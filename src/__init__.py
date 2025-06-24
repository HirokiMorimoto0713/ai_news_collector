"""
AI News Collector - 自動AI情報収集・投稿システム

このパッケージは、AI関連のニュースを自動収集し、
要約・感想を生成してWordPressに投稿するシステムです。
"""

__version__ = "2.0.0"
__author__ = "AI News Collector Team"
__description__ = "Automated AI news collection and publishing system"

from .core.models import NewsArticle, ProcessedArticle
from .core.config import ConfigManager
from .core.logger import get_logger

__all__ = [
    "NewsArticle",
    "ProcessedArticle", 
    "ConfigManager",
    "get_logger",
] 