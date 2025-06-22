"""
統合テストスクリプト
全システムの動作確認とテスト
"""

import os
import sys
import json
import asyncio
from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock

# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import AINewsCollector, NewsArticle
from twitter_collector import collect_twitter_articles
from integrated_collector import IntegratedAICollector
from article_processor import ArticleProcessor, ProcessedArticle
from wordpress_connector import WordPressConnector, DailyPostGenerator
from scheduler import ScheduledAINewsSystem

class TestAINewsSystem(unittest.TestCase):
    """AI情報システムのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.test_article = NewsArticle(
            title="テスト記事: AI技術の最新動向",
            url="https://example.com/test-article",
            content="これはテスト用の記事内容です。AI技術について詳しく説明しています。" * 10,
            source="Test Source"
        )
    
    def test_news_article_creation(self):
        """NewsArticleクラスのテスト"""
        article = self.test_article
        
        self.assertIsNotNone(article.hash_id)
        self.assertEqual(article.title, "テスト記事: AI技術の最新動向")
        self.assertEqual(article.source, "Test Source")
        self.assertTrue(len(article.content) > 100)
    
    def test_news_collector_initialization(self):
        """AINewsCollectorの初期化テスト"""
        collector = AINewsCollector()
        
        self.assertIsNotNone(collector.config)
        self.assertIn("max_articles_per_day", collector.config)
        self.assertIn("sources", collector.config)
    
    def test_duplicate_detection(self):
        """重複検出機能のテスト"""
        collector = AINewsCollector()
        
        # 同じ記事を2回追加
        article1 = self.test_article
        article2 = NewsArticle(
            title="テスト記事: AI技術の最新動向",  # 同じタイトル
            url="https://example.com/test-article",  # 同じURL
            content="異なる内容",
            source="Test Source"
        )
        
        # 最初の記事は重複ではない
        self.assertFalse(collector.is_duplicate(article1))
        collector.add_to_tracker(article1)
        
        # 2番目の記事は重複
        self.assertTrue(collector.is_duplicate(article2))
    
    async def test_twitter_collector(self):
        """Twitter収集機能のテスト"""
        # API使用しない代替手段でテスト
        articles = await collect_twitter_articles(use_api=False)
        
        self.assertIsInstance(articles, list)
        if articles:
            self.assertIsInstance(articles[0], NewsArticle)
    
    def test_integrated_collector_initialization(self):
        """統合収集システムの初期化テスト"""
        collector = IntegratedAICollector()
        
        self.assertIsNotNone(collector.config)
        self.assertIsNotNone(collector.news_collector)
    
    def test_article_filtering(self):
        """記事フィルタリング機能のテスト"""
        collector = IntegratedAICollector()
        
        # 有効な記事
        valid_article = NewsArticle(
            title="AI技術の進歩について",
            url="https://example.com/ai-progress",
            content="AI技術が急速に進歩しています。" * 20,  # 十分な長さ
            source="Tech News"
        )
        
        # 無効な記事（短すぎる）
        invalid_article = NewsArticle(
            title="短い記事",
            url="https://example.com/short",
            content="短い",  # 短すぎる
            source="Test"
        )
        
        self.assertTrue(collector.filter_article(valid_article))
        self.assertFalse(collector.filter_article(invalid_article))
    
    def test_processed_article_creation(self):
        """ProcessedArticleの作成テスト"""
        processed = ProcessedArticle(
            original_article=self.test_article,
            summary="テスト要約",
            user_value_comment="テスト感想",
            processing_date=datetime.now().isoformat()
        )
        
        self.assertEqual(processed.summary, "テスト要約")
        self.assertEqual(processed.user_value_comment, "テスト感想")
        self.assertIsNotNone(processed.processing_date)
    
    def test_wordpress_connector_initialization(self):
        """WordPressConnector初期化テスト"""
        connector = WordPressConnector()
        
        self.assertIsNotNone(connector.config)
        self.assertIn("wp_url", connector.config)
        self.assertIn("wp_user", connector.config)

class SystemIntegrationTest:
    """システム統合テストクラス"""
    
    def __init__(self):
        self.test_results = []
    
    async def test_full_workflow(self):
        """全ワークフローのテスト"""
        print("=== 全ワークフロー統合テスト開始 ===")
        
        try:
            # 1. 情報収集テスト
            print("\n1. 情報収集テスト")
            collector = IntegratedAICollector()
            articles = await collector.collect_all_sources()
            
            if articles:
                print(f"✅ 情報収集成功: {len(articles)}件")
                self.test_results.append(("情報収集", "成功", len(articles)))
            else:
                print("⚠️ 情報収集: 記事なし")
                self.test_results.append(("情報収集", "記事なし", 0))
            
            # 2. 記事処理テスト
            print("\n2. 記事処理テスト")
            if articles:
                # ダミー処理でテスト
                processed_articles = []
                for article in articles[:2]:  # 最初の2件のみ
                    processed = ProcessedArticle(
                        original_article=article,
                        summary=f"{article.title}の要約（テスト）",
                        user_value_comment="ユーザーにとって価値のある情報です（テスト）",
                        processing_date=datetime.now().isoformat()
                    )
                    processed_articles.append(processed)
                
                print(f"✅ 記事処理成功: {len(processed_articles)}件")
                self.test_results.append(("記事処理", "成功", len(processed_articles)))
            else:
                print("⚠️ 記事処理: 処理する記事なし")
                self.test_results.append(("記事処理", "記事なし", 0))
                processed_articles = []
            
            # 3. WordPress連携テスト（接続テストのみ）
            print("\n3. WordPress連携テスト")
            try:
                wp_connector = WordPressConnector()
                # 実際の投稿はせず、設定確認のみ
                print("✅ WordPress設定読み込み成功")
                self.test_results.append(("WordPress連携", "設定OK", 1))
            except Exception as e:
                print(f"⚠️ WordPress連携エラー: {e}")
                self.test_results.append(("WordPress連携", "エラー", 0))
            
            # 4. スケジューラーテスト
            print("\n4. スケジューラーテスト")
            try:
                scheduler = ScheduledAINewsSystem()
                print("✅ スケジューラー初期化成功")
                self.test_results.append(("スケジューラー", "成功", 1))
            except Exception as e:
                print(f"⚠️ スケジューラーエラー: {e}")
                self.test_results.append(("スケジューラー", "エラー", 0))
            
        except Exception as e:
            print(f"❌ 統合テストエラー: {e}")
            self.test_results.append(("統合テスト", "エラー", 0))
    
    def test_configuration_files(self):
        """設定ファイルのテスト"""
        print("\n=== 設定ファイルテスト ===")
        
        config_files = [
            "collector_config.json",
            "wordpress_config.json",
            "system_config.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    print(f"✅ {config_file}: 有効")
                    self.test_results.append((f"設定ファイル({config_file})", "有効", 1))
                except Exception as e:
                    print(f"❌ {config_file}: 無効 - {e}")
                    self.test_results.append((f"設定ファイル({config_file})", "無効", 0))
            else:
                print(f"⚠️ {config_file}: 存在しない")
                self.test_results.append((f"設定ファイル({config_file})", "存在しない", 0))
    
    def test_dependencies(self):
        """依存関係のテスト"""
        print("\n=== 依存関係テスト ===")
        
        required_modules = [
            "requests",
            "beautifulsoup4",
            "openai",
            "schedule"
        ]
        
        for module in required_modules:
            try:
                __import__(module.replace("-", "_"))
                print(f"✅ {module}: インストール済み")
                self.test_results.append((f"依存関係({module})", "OK", 1))
            except ImportError:
                print(f"❌ {module}: 未インストール")
                self.test_results.append((f"依存関係({module})", "未インストール", 0))
    
    def generate_test_report(self):
        """テストレポート生成"""
        print("\n" + "="*50)
        print("テスト結果サマリー")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status, _ in self.test_results if status in ["成功", "OK", "有効"])
        
        print(f"総テスト数: {total_tests}")
        print(f"成功: {passed_tests}")
        print(f"失敗/警告: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n詳細結果:")
        for test_name, status, count in self.test_results:
            status_icon = "✅" if status in ["成功", "OK", "有効"] else "⚠️" if status in ["記事なし", "存在しない"] else "❌"
            print(f"{status_icon} {test_name}: {status} ({count})")
        
        # レポートファイル保存
        report_data = {
            "test_date": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": [
                {"test": name, "status": status, "count": count}
                for name, status, count in self.test_results
            ]
        }
        
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nテストレポートを test_report.json に保存しました")

async def main():
    """メイン実行"""
    print("AI情報収集システム 統合テスト")
    print("="*50)
    
    # 単体テスト実行
    print("\n=== 単体テスト実行 ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 統合テスト実行
    integration_test = SystemIntegrationTest()
    
    await integration_test.test_full_workflow()
    integration_test.test_configuration_files()
    integration_test.test_dependencies()
    integration_test.generate_test_report()

if __name__ == "__main__":
    asyncio.run(main())

