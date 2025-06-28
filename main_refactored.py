#!/usr/bin/env python3
"""
AI News Collector - Refactored Main Application
統一された設定管理、エラーハンドリング、ログシステムを使用した改良版
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# コアモジュールのインポート
from src.core.config import ConfigManager
from src.core.logger import LoggerManager
from src.core.models import NewsArticle, ProcessedArticle, CollectionStats
from src.core.exceptions import ConfigurationError, APIError, ProcessingError

# 既存モジュールのインポート（互換性のため）
from simple_scraper import SimpleScraper
from article_processor import ArticleProcessor
from wordpress_connector import WordPressConnector

class AINewsCollectorRefactored:
    """リファクタリング版 AI News Collector メインクラス"""
    
    def __init__(self):
        """初期化"""
        try:
            # 設定管理の初期化
            self.config = ConfigManager()
            
            # ログ管理の初期化
            self.logger_manager = LoggerManager()
            self.logger = self.logger_manager.get_logger("main")
            
            # システム情報のログ出力
            self._log_system_info()
            
            # 設定の検証
            self._validate_configuration()
            
            # コンポーネントの初期化
            self._initialize_components()
            
            # 統計情報の初期化
            self.stats = CollectionStats()
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            sys.exit(1)
    
    def _log_system_info(self):
        """システム情報をログ出力"""
        system_logger = self.logger_manager.get_logger("system")
        system_logger.info("=== AI News Collector System Started ===")
        system_logger.info(f"Python Version: {sys.version}")
        system_logger.info(f"Working Directory: {os.getcwd()}")
        system_logger.info(f"Start Time: {self.config.system.start_time}")
        
        # 設定サマリーの出力
        config_logger = self.logger_manager.get_logger("config")
        config_logger.info("=== Configuration Summary ===")
        config_logger.info(f"WordPress URL: {self.config.wordpress.url}")
        config_logger.info(f"WordPress User: {self.config.wordpress.user}")
        config_logger.info(f"OpenAI API Key: {'configured' if self.config.openai.api_key and self.config.openai.api_key != 'YOUR_OPENAI_API_KEY_HERE' else 'not configured'}")
        config_logger.info(f"Max articles per day: {self.config.collection.max_articles_per_day}")
        config_logger.info(f"Log level: {self.config.system.log_level}")
        config_logger.info("=" * 30)
    
    def _validate_configuration(self):
        """設定の検証"""
        validation_logger = self.logger_manager.get_logger("validation")
        
        errors = []
        
        # OpenAI API キーの検証
        if not self.config.openai.api_key or self.config.openai.api_key == "YOUR_OPENAI_API_KEY_HERE":
            errors.append("OpenAI API キーが設定されていません")
        
        # WordPress設定の検証
        if not self.config.wordpress.url or "your-wordpress-site.com" in self.config.wordpress.url:
            errors.append("WordPress URLが設定されていません")
        
        if not self.config.wordpress.user or self.config.wordpress.user == "YOUR_WP_USERNAME":
            errors.append("WordPress ユーザー名が設定されていません")
        
        if not self.config.wordpress.app_password:
            errors.append("WordPress アプリケーションパスワードが設定されていません")
        
        if errors:
            for error in errors:
                validation_logger.error(error)
            raise ConfigurationError(f"設定エラーが {len(errors)} 件あります: {', '.join(errors)}")
        
        validation_logger.info("Configuration validation passed")
    
    def _initialize_components(self):
        """各コンポーネントの初期化"""
        try:
            # 記事収集器の初期化
            self.scraper = SimpleScraper()
            
            # 記事処理器の初期化
            self.processor = ArticleProcessor(
                openai_api_key=self.config.openai.api_key
            )
            
            # WordPress接続器の初期化（既存のconfig fileを使用）
            self.wordpress = WordPressConnector("wordpress_config.json")
            
        except Exception as e:
            self.logger.error(f"コンポーネント初期化エラー: {e}")
            raise ConfigurationError(f"コンポーネント初期化に失敗しました: {e}")
    
    def _check_daily_limit(self) -> bool:
        """日次投稿制限のチェック"""
        limiter_logger = self.logger_manager.get_logger("limiter")
        
        try:
            from datetime import date
            import json
            
            today = date.today().strftime("%Y-%m-%d")
            daily_file = f"daily_posts_{today}.json"
            
            if os.path.exists(daily_file):
                with open(daily_file, 'r', encoding='utf-8') as f:
                    daily_data = json.load(f)
                    posts_today = daily_data.get('posts_count', 0)
                    
                    if posts_today >= self.config.collection.max_articles_per_day:
                        limiter_logger.info(f"Daily limit reached: {posts_today}/{self.config.collection.max_articles_per_day}")
                        return False
            
            limiter_logger.info("Daily limit check passed")
            return True
            
        except Exception as e:
            limiter_logger.error(f"Failed to check daily limit: {e}")
            return True  # エラー時は実行を継続
    
    def _update_daily_count(self):
        """日次投稿数の更新"""
        limiter_logger = self.logger_manager.get_logger("limiter")
        
        try:
            import json
            from datetime import date, datetime
            
            today = date.today().strftime("%Y-%m-%d")
            daily_file = f"daily_posts_{today}.json"
            
            daily_data = {
                'date': today,
                'posts_count': 1,
                'last_post_time': datetime.now().isoformat(),
                'max_posts_per_day': self.config.collection.max_articles_per_day
            }
            
            if os.path.exists(daily_file):
                with open(daily_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    daily_data['posts_count'] = existing_data.get('posts_count', 0) + 1
            
            with open(daily_file, 'w', encoding='utf-8') as f:
                json.dump(daily_data, f, ensure_ascii=False, indent=2)
                
            limiter_logger.info(f"Updated daily count: {daily_data['posts_count']}/{self.config.collection.max_articles_per_day}")
            
        except Exception as e:
            limiter_logger.error(f"Failed to update daily count: {e}")
    
    async def collect_articles(self) -> List[NewsArticle]:
        """記事の収集"""
        collector_logger = self.logger_manager.get_logger("collector")
        collector_logger.info("Starting article collection...")
        
        try:
            # 既存のsimple_scraperを使用
            articles_data = self.scraper.collect_articles()
            
            # NewsArticleオブジェクトに変換
            articles = []
            for data in articles_data:
                article = NewsArticle(
                    title=data.get('title', ''),
                    url=data.get('url', ''),
                    content=data.get('content', ''),
                    source=data.get('source', 'unknown'),
                    published_date=data.get('published_date')
                )
                articles.append(article)
            
            self.stats.articles_collected = len(articles)
            collector_logger.info(f"Collected {len(articles)} articles")
            return articles
            
        except Exception as e:
            collector_logger.error(f"Article collection failed: {e}")
            raise APIError(f"記事収集に失敗しました: {e}")
    
    async def process_articles(self, articles: List[NewsArticle]) -> List[ProcessedArticle]:
        """記事の処理"""
        processor_logger = self.logger_manager.get_logger("processor")
        processor_logger.info(f"Processing {len(articles)} articles...")
        
        processed_articles = []
        
        for i, article in enumerate(articles, 1):
            try:
                processor_logger.info(f"Processing article {i}/{len(articles)}: {article.title}")
                
                # 既存のarticle_processorを使用
                processed_content = await self.processor.process_article(article.content)
                
                processed_article = ProcessedArticle(
                    original_article=article,
                    processed_content=processed_content,
                    processing_metadata={
                        'processing_time': 'unknown',
                        'model_used': self.config.openai.model,
                        'processing_index': i
                    }
                )
                
                processed_articles.append(processed_article)
                self.stats.articles_processed += 1
                
            except Exception as e:
                processor_logger.error(f"Failed to process article {i}: {e}")
                self.stats.articles_failed += 1
                continue
        
        processor_logger.info(f"Successfully processed {len(processed_articles)} articles")
        return processed_articles
    
    async def publish_articles(self, processed_articles: List[ProcessedArticle]) -> int:
        """記事の投稿"""
        publisher_logger = self.logger_manager.get_logger("publisher")
        publisher_logger.info(f"Publishing {len(processed_articles)} articles...")
        
        try:
            # 統合記事の作成と投稿（既存のWordPressConnectorを使用）
            if processed_articles:
                # 最初の記事を使って統合記事を作成
                post_data = {
                    'title': f"AI News Today - {len(processed_articles)} articles - {date.today().strftime('%Y-%m-%d')}",
                    'content': '\n\n'.join([article.processed_content for article in processed_articles]),
                    'status': 'publish',
                    'categories': [self.config.wordpress.category_id],
                    'tags': self.config.wordpress.tags
                }
                
                post_url = self.wordpress.post_article(post_data)
                
                if post_url:
                    publisher_logger.info(f"Successfully published post: {post_url}")
                    self.stats.articles_published = 1
                    return 1
                else:
                    publisher_logger.error("Failed to publish post")
                    return 0
            
            return 0
            
        except Exception as e:
            publisher_logger.error(f"Publishing failed: {e}")
            raise APIError(f"記事投稿に失敗しました: {e}")
    
    async def run(self):
        """メイン実行ループ"""
        self.logger.info("=== AI News Collector System Started ===")
        
        try:
            # 日次制限のチェック
            if not self._check_daily_limit():
                self.logger.info("Daily posting limit reached. Skipping execution.")
                return
            
            # 記事の収集
            articles = await self.collect_articles()
            
            if not articles:
                self.logger.warning("No articles collected. Exiting.")
                return
            
            # 記事の処理
            processed_articles = await self.process_articles(articles)
            
            if not processed_articles:
                self.logger.warning("No articles processed successfully. Exiting.")
                return
            
            # 記事の投稿
            published_count = await self.publish_articles(processed_articles)
            
            if published_count > 0:
                # 日次カウンターの更新
                self._update_daily_count()
                self.logger.info("=== System execution completed successfully ===")
            else:
                self.logger.warning("No articles were published")
            
        except Exception as e:
            self.logger.error(f"System execution failed: {e}")
            raise
        
        finally:
            # 統計情報の出力
            self._log_statistics()
    
    def _log_statistics(self):
        """実行統計の出力"""
        self.logger.info("=== Execution Statistics ===")
        self.logger.info(f"Total collected: {self.stats.articles_collected}")
        self.logger.info(f"Successfully processed: {self.stats.articles_processed}")
        self.logger.info(f"Failed to process: {self.stats.articles_failed}")
        self.logger.info(f"Published: {self.stats.articles_published}")

async def main():
    """非同期メイン関数"""
    try:
        collector = AINewsCollectorRefactored()
        await collector.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  実行が中断されました")
        sys.exit(130)
        
    except Exception as e:
        print(f"❌ システムエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main()) 