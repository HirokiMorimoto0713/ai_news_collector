#!/usr/bin/env python3
"""
AI News Collector - Refactored Main Application

リファクタリングされたAI情報収集・投稿システムのメインエントリーポイント
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.logger import setup_logging, get_logger, log_system_info
from src.core.models import CollectionStats
from src.core.exceptions import AINewsCollectorError
from src.utils.file_utils import create_data_structure


class AINewsSystem:
    """リファクタリングされたAI情報収集・投稿システム"""
    
    def __init__(self):
        """システムの初期化"""
        # 設定管理の初期化
        self.config = ConfigManager()
        
        # ログシステムの初期化
        system_config = self.config.get_system_config()
        self.logger = setup_logging(
            log_level=system_config['log_level'],
            log_file=system_config['log_file']
        )
        
        # システム情報をログに記録
        log_system_info()
        
        # データ構造を作成
        create_data_structure()
        
        # 統計情報
        self.stats = CollectionStats()
        
        # 設定概要を表示
        self.config.print_config_summary()
    
    def validate_configuration(self) -> bool:
        """設定の検証"""
        logger = get_logger("validation")
        
        # 必須設定の確認
        required_keys = [
            'wordpress.url',
            'wordpress.user', 
            'wordpress.app_pass',
            'openai.api_key'
        ]
        
        missing_keys = self.config.validate_required_settings(required_keys)
        
        if missing_keys:
            logger.error("Missing required configuration keys:")
            for key in missing_keys:
                logger.error(f"  - {key}")
            logger.error("Please configure these settings before running the system.")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    async def collect_articles(self):
        """記事の収集"""
        logger = get_logger("collector")
        logger.info("Starting article collection...")
        
        try:
            # 既存のコレクターを使用（互換性のため）
            from integrated_collector import IntegratedAICollector
            
            collector = IntegratedAICollector()
            articles = await collector.collect_all_articles()
            
            self.stats.total_collected = len(articles)
            logger.info(f"Collected {len(articles)} articles")
            
            return articles
            
        except Exception as e:
            logger.error(f"Article collection failed: {e}")
            raise AINewsCollectorError(f"Collection failed: {e}")
    
    async def process_articles(self, articles):
        """記事の処理"""
        logger = get_logger("processor")
        logger.info(f"Processing {len(articles)} articles...")
        
        try:
            # 既存のプロセッサーを使用（互換性のため）
            from article_processor import ArticleProcessor
            
            processor = ArticleProcessor()
            processed_articles = []
            
            for i, article in enumerate(articles, 1):
                try:
                    logger.info(f"Processing article {i}/{len(articles)}: {article.title}")
                    processed = processor.process_article(article)
                    
                    if processed:
                        processed_articles.append(processed)
                        self.stats.successful_processed += 1
                    else:
                        self.stats.failed_processed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process article {i}: {e}")
                    self.stats.failed_processed += 1
                    continue
            
            logger.info(f"Successfully processed {len(processed_articles)} articles")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Article processing failed: {e}")
            raise AINewsCollectorError(f"Processing failed: {e}")
    
    async def publish_articles(self, processed_articles):
        """記事の投稿"""
        logger = get_logger("publisher")
        logger.info(f"Publishing {len(processed_articles)} articles...")
        
        try:
            # 既存のWordPressコネクターを使用（互換性のため）
            from wordpress_connector import WordPressConnector, DailyPostGenerator
            
            wp_connector = WordPressConnector()
            post_generator = DailyPostGenerator(wp_connector)
            
            # 日次投稿として公開
            post_info = post_generator.publish_daily_post(processed_articles)
            
            if post_info:
                self.stats.published_count = 1
                logger.info(f"Successfully published post: {post_info['link']}")
                return post_info
            else:
                logger.error("Failed to publish articles")
                return None
                
        except Exception as e:
            logger.error(f"Article publishing failed: {e}")
            raise AINewsCollectorError(f"Publishing failed: {e}")
    
    def check_daily_limit(self) -> bool:
        """日次投稿制限のチェック"""
        logger = get_logger("limiter")
        
        try:
            from datetime import datetime
            import json
            import os
            
            today = datetime.now().strftime('%Y-%m-%d')
            count_file = f"daily_posts_{today}.json"
            
            max_posts = self.config.get('collection.max_articles_per_day', 1)
            
            if os.path.exists(count_file):
                with open(count_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_count = data.get('count', 0)
                    
                    if current_count >= max_posts:
                        logger.info(f"Daily limit reached: {current_count}/{max_posts}")
                        return False
            
            logger.info("Daily limit check passed")
            return True
            
        except Exception as e:
            logger.error(f"Daily limit check failed: {e}")
            return True  # エラー時は続行
    
    def update_daily_count(self):
        """日次投稿数の更新"""
        try:
            from datetime import datetime
            import json
            import os
            
            today = datetime.now().strftime('%Y-%m-%d')
            count_file = f"daily_posts_{today}.json"
            
            current_count = 0
            if os.path.exists(count_file):
                with open(count_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_count = data.get('count', 0)
            
            # カウントを更新
            data = {
                'date': today,
                'count': current_count + 1,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(count_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger = get_logger("limiter")
            logger.error(f"Failed to update daily count: {e}")
    
    async def run(self):
        """メインの実行ループ"""
        logger = get_logger("main")
        logger.info("=== AI News Collector System Started ===")
        
        try:
            # 設定の検証
            if not self.validate_configuration():
                return False
            
            # 日次制限のチェック
            if not self.check_daily_limit():
                logger.info("Daily posting limit reached. Skipping execution.")
                return True
            
            # 記事の収集
            articles = await self.collect_articles()
            
            if not articles:
                logger.info("No articles collected. Ending execution.")
                return True
            
            # 記事の処理
            processed_articles = await self.process_articles(articles)
            
            if not processed_articles:
                logger.info("No articles processed successfully. Ending execution.")
                return True
            
            # 記事の投稿
            post_info = await self.publish_articles(processed_articles)
            
            if post_info:
                # 日次カウントを更新
                self.update_daily_count()
                logger.info("=== System execution completed successfully ===")
                return True
            else:
                logger.error("Publishing failed")
                return False
                
        except AINewsCollectorError as e:
            logger.error(f"System error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False
        
        finally:
            # 統計情報をログに出力
            logger.info("=== Execution Statistics ===")
            logger.info(f"Total collected: {self.stats.total_collected}")
            logger.info(f"Successfully processed: {self.stats.successful_processed}")
            logger.info(f"Failed to process: {self.stats.failed_processed}")
            logger.info(f"Published: {self.stats.published_count}")


async def main():
    """メイン関数"""
    system = AINewsSystem()
    success = await system.run()
    
    # 終了コードを設定
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 