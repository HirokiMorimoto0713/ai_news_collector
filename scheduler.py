"""
スケジュール実行・重複除外モジュール
cronジョブとして実行される日次処理
"""

import os
import sys
import json
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_collector import IntegratedAICollector
from article_processor import ArticleProcessor, BlogPostGenerator
from wordpress_connector import WordPressConnector, DailyPostGenerator

class ScheduledAINewsSystem:
    """スケジュール実行AI情報システム"""
    
    def __init__(self, config_file: str = "system_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
        # 各コンポーネントの初期化
        self.collector = IntegratedAICollector()
        self.processor = None  # OpenAI APIキーが設定されている場合のみ初期化
        self.wp_connector = None  # WordPress設定が正しい場合のみ初期化
        self.post_generator = None
        
        self.initialize_components()
    
    def load_config(self) -> Dict:
        """システム設定を読み込み"""
        default_config = {
            "schedule": {
                "collection_time": "09:00",
                "posting_time": "10:00",
                "timezone": "Asia/Tokyo"
            },
            "duplicate_prevention": {
                "enabled": True,
                "history_days": 30,
                "similarity_threshold": 0.8
            },
            "error_handling": {
                "max_retries": 3,
                "retry_delay_minutes": 5,
                "notification_email": None
            },
            "logging": {
                "level": "INFO",
                "file": "ai_news_system.log",
                "max_size_mb": 10
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # デフォルト設定とマージ
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
    
    def setup_logging(self):
        """ログ設定"""
        log_config = self.config["logging"]
        
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config["file"], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def initialize_components(self):
        """各コンポーネントの初期化"""
        try:
            # OpenAI APIキーが設定されている場合のみ初期化
            if os.getenv('OPENAI_API_KEY'):
                self.processor = ArticleProcessor()
                self.logger.info("記事処理モジュールを初期化しました")
            else:
                self.logger.warning("OPENAI_API_KEYが設定されていません。ダミー処理を使用します")
            
            # WordPress設定の確認
            self.wp_connector = WordPressConnector()
            if self.wp_connector.test_connection():
                self.post_generator = DailyPostGenerator(self.wp_connector)
                self.logger.info("WordPress連携モジュールを初期化しました")
            else:
                self.logger.warning("WordPress接続に失敗しました。投稿機能は無効化されます")
                
        except Exception as e:
            self.logger.error(f"コンポーネント初期化エラー: {e}")
    
    def check_duplicate_by_content(self, new_articles: List, history_file: str = "article_history.json") -> List:
        """コンテンツベースの重複チェック"""
        if not self.config["duplicate_prevention"]["enabled"]:
            return new_articles
        
        # 履歴ファイルの読み込み
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.warning(f"履歴ファイル読み込みエラー: {e}")
        
        # 古い履歴を削除（設定日数より古いもの）
        cutoff_date = datetime.now() - timedelta(days=self.config["duplicate_prevention"]["history_days"])
        history = [
            h for h in history 
            if datetime.fromisoformat(h.get('date', '1970-01-01')) > cutoff_date
        ]
        
        # 重複チェック
        unique_articles = []
        for article in new_articles:
            is_duplicate = False
            
            # タイトルとURLでの重複チェック
            for hist_item in history:
                if (article.title == hist_item.get('title') or 
                    article.url == hist_item.get('url')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                # 履歴に追加
                history.append({
                    'title': article.title,
                    'url': article.url,
                    'source': article.source,
                    'date': datetime.now().isoformat(),
                    'hash_id': article.hash_id
                })
        
        # 履歴ファイルの更新
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"履歴ファイル保存エラー: {e}")
        
        self.logger.info(f"重複チェック完了: {len(new_articles)} -> {len(unique_articles)} 件")
        return unique_articles
    
    async def daily_collection_job(self):
        """日次情報収集ジョブ"""
        self.logger.info("=== 日次情報収集開始 ===")
        
        try:
            # 情報収集
            articles = await self.collector.collect_all_sources()
            
            if not articles:
                self.logger.warning("収集された記事がありません")
                return []
            
            # 重複除外
            unique_articles = self.check_duplicate_by_content(articles)
            
            if not unique_articles:
                self.logger.info("重複除外後、新しい記事がありません")
                return []
            
            # 収集結果の保存
            filename = self.collector.save_collected_articles()
            self.logger.info(f"収集完了: {len(unique_articles)}件の記事を保存 ({filename})")
            
            return unique_articles
            
        except Exception as e:
            self.logger.error(f"情報収集エラー: {e}")
            return []
    
    def daily_processing_job(self, articles: List):
        """日次記事処理ジョブ"""
        if not articles:
            self.logger.info("処理する記事がありません")
            return []
        
        self.logger.info(f"=== {len(articles)}件の記事処理開始 ===")
        
        try:
            if self.processor:
                # OpenAI APIを使用した処理
                processed_articles = self.processor.process_articles_batch(articles)
                filename = self.processor.save_processed_articles(processed_articles)
                self.logger.info(f"記事処理完了: {filename}")
            else:
                # ダミー処理
                from article_processor import ProcessedArticle
                processed_articles = []
                for article in articles:
                    processed = ProcessedArticle(
                        original_article=article,
                        summary=f"{article.title}の要約（ダミー）",
                        user_value_comment="ユーザーにとって価値のある情報です（ダミー）",
                        processing_date=datetime.now().isoformat()
                    )
                    processed_articles.append(processed)
                
                self.logger.info(f"ダミー処理完了: {len(processed_articles)}件")
            
            return processed_articles
            
        except Exception as e:
            self.logger.error(f"記事処理エラー: {e}")
            return []
    
    async def daily_posting_job(self, processed_articles: List):
        """日次投稿ジョブ（新しいDailyAIPublisherを使用）"""
        if not processed_articles:
            self.logger.info("投稿する記事がありません")
            return
        
        self.logger.info(f"=== {len(processed_articles)}件の記事投稿開始 ===")
        
        try:
            # 新しい投稿システムを使用
            from daily_publisher import DailyAIPublisher
            publisher = DailyAIPublisher()
            
            # 既に処理済みの記事を直接投稿
            post_content = publisher.post_generator.generate_daily_post_content(processed_articles)
            
            post_info = publisher.wp_connector.create_post(
                title=post_content['title'],
                content=post_content['content'],
                excerpt=post_content['excerpt'],
                tags=["AI", "技術動向", "まとめ", "最新情報", "自動投稿"]
            )
            
            if post_info:
                self.logger.info(f"WordPress投稿成功: {post_info['link']}")
                
                # 詳細ログを保存
                publisher.save_publication_log(post_info, processed_articles, post_content)
                return post_info
            else:
                self.logger.error("WordPress投稿失敗")
                return None
                
        except Exception as e:
            self.logger.error(f"投稿エラー: {e}")
            return None
    
    async def run_daily_workflow(self):
        """日次ワークフロー実行"""
        self.logger.info("=== 日次ワークフロー開始 ===")
        
        # 1. 情報収集
        articles = await self.daily_collection_job()
        
        # 2. 記事処理
        processed_articles = self.daily_processing_job(articles)
        
        # 3. WordPress投稿
        await self.daily_posting_job(processed_articles)
        
        self.logger.info("=== 日次ワークフロー完了 ===")
    
    def setup_schedule(self):
        """スケジュール設定"""
        collection_time = self.config["schedule"]["collection_time"]
        posting_time = self.config["schedule"]["posting_time"]
        
        # 情報収集スケジュール（9時）
        schedule.every().day.at(collection_time).do(
            lambda: asyncio.run(self.daily_collection_job())
        )
        
        # 投稿スケジュール（10時）
        schedule.every().day.at(posting_time).do(
            lambda: asyncio.run(self.run_daily_workflow())
        )
        
        self.logger.info(f"スケジュール設定完了: 収集 {collection_time}, 投稿 {posting_time}")
    
    def run_scheduler(self):
        """スケジューラー実行"""
        self.setup_schedule()
        self.logger.info("スケジューラー開始")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分間隔でチェック

def main():
    """メイン実行"""
    system = ScheduledAINewsSystem()
    
    # コマンドライン引数での実行モード判定
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "collect":
            # 情報収集のみ実行
            asyncio.run(system.daily_collection_job())
        elif mode == "workflow":
            # 全ワークフロー実行
            asyncio.run(system.run_daily_workflow())
        elif mode == "schedule":
            # スケジューラー実行
            system.run_scheduler()
        else:
            print("使用方法: python scheduler.py [collect|workflow|schedule]")
    else:
        # デフォルト: 全ワークフロー実行
        asyncio.run(system.run_daily_workflow())

if __name__ == "__main__":
    main()

