"""
Data models for AI News Collector
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class NewsArticle:
    """ニュース記事のデータクラス"""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    hash_id: Optional[str] = field(default=None, init=False)
    likes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    
    def __post_init__(self):
        """記事のハッシュIDを生成"""
        if not self.hash_id:
            content_for_hash = f"{self.title}{self.url}{self.source}"
            self.hash_id = hashlib.md5(content_for_hash.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'source': self.source,
            'published_date': self.published_date,
            'author': self.author,
            'hash_id': self.hash_id,
            'likes': self.likes,
            'tags': self.tags,
            'image_url': self.image_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsArticle':
        """辞書からインスタンスを作成"""
        return cls(
            title=data['title'],
            url=data['url'],
            content=data['content'],
            source=data['source'],
            published_date=data.get('published_date'),
            author=data.get('author'),
            likes=data.get('likes'),
            tags=data.get('tags', []),
            image_url=data.get('image_url')
        )


@dataclass
class ProcessedArticle:
    """処理済み記事のデータクラス"""
    original_article: NewsArticle
    summary: str
    user_value_comment: str
    processing_date: str
    translated_title: str = ""
    content_preview: str = ""
    featured_image_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'title': self.original_article.title,
            'translated_title': self.translated_title,
            'url': self.original_article.url,
            'source': self.original_article.source,
            'original_content': self.original_article.content,
            'content_preview': self.content_preview,
            'summary': self.summary,
            'user_value_comment': self.user_value_comment,
            'processing_date': self.processing_date,
            'hash_id': self.original_article.hash_id,
            'featured_image_url': self.featured_image_url,
            'tags': self.original_article.tags,
            'author': self.original_article.author,
            'published_date': self.original_article.published_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedArticle':
        """辞書からインスタンスを作成"""
        original_article = NewsArticle(
            title=data['title'],
            url=data['url'],
            content=data.get('original_content', ''),
            source=data['source'],
            published_date=data.get('published_date'),
            author=data.get('author'),
            tags=data.get('tags', [])
        )
        
        return cls(
            original_article=original_article,
            summary=data['summary'],
            user_value_comment=data['user_value_comment'],
            processing_date=data['processing_date'],
            translated_title=data.get('translated_title', ''),
            content_preview=data.get('content_preview', ''),
            featured_image_url=data.get('featured_image_url')
        )


@dataclass
class CollectionStats:
    """収集統計のデータクラス"""
    total_collected: int = 0
    successful_processed: int = 0
    failed_processed: int = 0
    duplicates_filtered: int = 0
    published_count: int = 0
    collection_time: Optional[datetime] = None
    sources: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'total_collected': self.total_collected,
            'successful_processed': self.successful_processed,
            'failed_processed': self.failed_processed,
            'duplicates_filtered': self.duplicates_filtered,
            'published_count': self.published_count,
            'collection_time': self.collection_time.isoformat() if self.collection_time else None,
            'sources': self.sources
        } 