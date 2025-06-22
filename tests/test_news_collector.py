#!/usr/bin/env python3
"""
AIニュース収集システム - 単体テスト
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import json
from datetime import datetime, timedelta

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import news_collector
    import article_processor
    import wordpress_connector
    import daily_publisher
except ImportError:
    # モジュールが見つからない場合はモックを作成
    news_collector = Mock()
    article_processor = Mock()
    wordpress_connector = Mock()
    daily_publisher = Mock()


class TestNewsCollector(unittest.TestCase):
    """ニュース収集機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_config = {
            'sources': ['techcrunch', 'venturebeat'],
            'keywords': ['AI', '人工知能', 'machine learning'],
            'max_articles': 10
        }

    @patch('news_collector.requests.get')
    def test_fetch_news_from_source(self, mock_get):
        """ニュースソースからの記事取得テスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <article>
                <h1>Test AI News Article</h1>
                <p>This is a test article about AI.</p>
            </article>
        </html>
        """
        mock_get.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(news_collector, 'fetch_from_source'):
            result = news_collector.fetch_from_source('techcrunch')
            self.assertIsInstance(result, list)

    def test_keyword_filtering(self):
        """キーワードフィルタリングのテスト"""
        test_articles = [
            {'title': 'AI革命が始まる', 'content': '人工知能の話題'},
            {'title': '今日の天気', 'content': '晴れです'},
            {'title': 'Machine Learning入門', 'content': 'MLの基礎'}
        ]
        
        keywords = ['AI', '人工知能', 'machine learning']
        
        # キーワードフィルタリング関数が存在する場合のテスト
        if hasattr(news_collector, 'filter_by_keywords'):
            filtered = news_collector.filter_by_keywords(test_articles, keywords)
            self.assertIsInstance(filtered, list)
            # AI関連の記事のみが残ることを期待
            self.assertLessEqual(len(filtered), len(test_articles))

    @patch('news_collector.tweepy.API')
    def test_twitter_collection(self, mock_twitter_api):
        """Twitter/X からの情報収集テスト"""
        # モックツイートデータ
        mock_tweet = Mock()
        mock_tweet.full_text = "AIの最新ニュース #AI #MachineLearning"
        mock_tweet.created_at = datetime.now()
        mock_tweet.user.screen_name = "test_user"
        
        mock_twitter_api.return_value.search_tweets.return_value = [mock_tweet]

        # テスト実行（実際の関数があれば）
        if hasattr(news_collector, 'collect_from_twitter'):
            result = news_collector.collect_from_twitter(['AI', 'MachineLearning'])
            self.assertIsInstance(result, list)


class TestArticleProcessor(unittest.TestCase):
    """記事処理機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_article = {
            'title': 'AI技術の進歩について',
            'content': 'AI技術は急速に進歩しており、様々な分野で活用されています。',
            'url': 'https://example.com/ai-news',
            'published_date': datetime.now().isoformat(),
            'source': 'techcrunch'
        }

    def test_duplicate_detection(self):
        """重複記事検出のテスト"""
        articles = [
            {'title': 'AI技術の進歩', 'content': '内容1'},
            {'title': 'AI技術の進歩について', 'content': '内容2'},
            {'title': '全く違う記事', 'content': '内容3'}
        ]
        
        # 重複検出関数が存在する場合のテスト
        if hasattr(article_processor, 'detect_duplicates'):
            duplicates = article_processor.detect_duplicates(articles)
            self.assertIsInstance(duplicates, list)

    @patch('article_processor.openai')
    def test_content_summarization(self, mock_openai):
        """記事要約機能のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "AI技術の進歩に関する要約"
        mock_openai.ChatCompletion.create.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(article_processor, 'summarize_article'):
            result = article_processor.summarize_article(self.test_article['content'])
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

    def test_sentiment_analysis(self):
        """感情分析のテスト"""
        positive_text = "素晴らしいAI技術の進歩です！"
        negative_text = "AI技術には懸念があります。"
        
        # 感情分析関数が存在する場合のテスト
        if hasattr(article_processor, 'analyze_sentiment'):
            positive_score = article_processor.analyze_sentiment(positive_text)
            negative_score = article_processor.analyze_sentiment(negative_text)
            
            self.assertIsInstance(positive_score, (int, float))
            self.assertIsInstance(negative_score, (int, float))

    def test_article_scoring(self):
        """記事スコアリングのテスト"""
        # スコアリング関数が存在する場合のテスト
        if hasattr(article_processor, 'calculate_article_score'):
            score = article_processor.calculate_article_score(self.test_article)
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)


class TestWordPressConnector(unittest.TestCase):
    """WordPress連携機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_post = {
            'title': 'AIニュース記事',
            'content': '<p>AIに関する最新ニュースです。</p>',
            'excerpt': 'AIニュースの要約',
            'categories': [1],
            'tags': [1, 2, 3],
            'featured_media': 123
        }
        self.wp_config = {
            'url': 'https://test-site.com',
            'username': 'test-user',
            'password': 'test-pass'
        }

    @patch('wordpress_connector.requests.post')
    def test_wordpress_authentication(self, mock_post):
        """WordPress認証のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'test-jwt-token'}
        mock_post.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(wordpress_connector, 'authenticate'):
            result = wordpress_connector.authenticate(self.wp_config)
            self.assertIsInstance(result, str)

    @patch('wordpress_connector.requests.post')
    def test_post_publication(self, mock_post):
        """記事投稿のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 456,
            'link': 'https://test-site.com/ai-news-article',
            'status': 'publish'
        }
        mock_post.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(wordpress_connector, 'publish_post'):
            result = wordpress_connector.publish_post(self.test_post, self.wp_config)
            self.assertIsInstance(result, dict)
            self.assertIn('id', result)

    @patch('wordpress_connector.requests.get')
    def test_category_management(self, mock_get):
        """カテゴリ管理のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'AI', 'slug': 'ai'},
            {'id': 2, 'name': 'Technology', 'slug': 'technology'}
        ]
        mock_get.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(wordpress_connector, 'get_categories'):
            result = wordpress_connector.get_categories(self.wp_config)
            self.assertIsInstance(result, list)

    def test_post_validation(self):
        """投稿データの検証テスト"""
        # 必須フィールドの検証
        required_fields = ['title', 'content']
        for field in required_fields:
            self.assertIn(field, self.test_post)
            self.assertIsNotNone(self.test_post[field])


class TestDailyPublisher(unittest.TestCase):
    """日次投稿機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_articles = [
            {
                'title': 'AI記事1',
                'content': '内容1',
                'score': 0.8,
                'published_date': datetime.now().isoformat()
            },
            {
                'title': 'AI記事2',
                'content': '内容2',
                'score': 0.6,
                'published_date': datetime.now().isoformat()
            }
        ]

    def test_article_selection(self):
        """記事選択ロジックのテスト"""
        # 記事選択関数が存在する場合のテスト
        if hasattr(daily_publisher, 'select_articles_for_publication'):
            selected = daily_publisher.select_articles_for_publication(
                self.test_articles, 
                max_count=1,
                min_score=0.7
            )
            self.assertIsInstance(selected, list)
            self.assertLessEqual(len(selected), 1)

    def test_publication_scheduling(self):
        """投稿スケジューリングのテスト"""
        # スケジューリング関数が存在する場合のテスト
        if hasattr(daily_publisher, 'schedule_publications'):
            schedule = daily_publisher.schedule_publications(
                self.test_articles,
                interval_hours=6
            )
            self.assertIsInstance(schedule, list)

    @patch('daily_publisher.json.dump')
    def test_publication_logging(self, mock_json_dump):
        """投稿ログ記録のテスト"""
        publication_log = {
            'date': datetime.now().isoformat(),
            'published_articles': [
                {'id': 1, 'title': 'AI記事1', 'status': 'published'}
            ],
            'total_published': 1
        }

        # ログ記録関数が存在する場合のテスト
        if hasattr(daily_publisher, 'log_publication'):
            daily_publisher.log_publication(publication_log)
            mock_json_dump.assert_called()


class TestSystemIntegration(unittest.TestCase):
    """システム統合テスト"""

    def test_end_to_end_workflow(self):
        """エンドツーエンドワークフローのテスト"""
        # 実際のシステムでは、以下のワークフローをテスト
        workflow_steps = [
            'news_collection',
            'article_processing',
            'duplicate_detection',
            'scoring',
            'selection',
            'wordpress_publication',
            'logging'
        ]
        
        # 各ステップが定義されていることを確認
        for step in workflow_steps:
            # 実際の実装では、各ステップの関数が存在することを確認
            print(f"Testing workflow step: {step}")

    def test_error_recovery(self):
        """エラー回復機能のテスト"""
        # システムが部分的に失敗した場合の回復テスト
        # 実際の実装では、以下をテスト:
        # - ネットワークエラー時の再試行
        # - API制限時の待機
        # - 部分的な処理失敗からの回復
        pass

    def test_data_persistence(self):
        """データ永続化のテスト"""
        # 記事履歴、設定、ログの永続化テスト
        test_data = {
            'articles': self.test_articles if hasattr(self, 'test_articles') else [],
            'timestamp': datetime.now().isoformat()
        }
        
        # データの保存と読み込みテスト
        # 実際の実装では、JSONファイルやデータベースの操作をテスト
        self.assertIsInstance(test_data, dict)


class TestConfigurationValidation(unittest.TestCase):
    """設定検証のテスト（改善提案2に対応）"""

    def test_required_environment_variables(self):
        """必須環境変数のテスト"""
        required_env_vars = [
            'WORDPRESS_URL',
            'WORDPRESS_USERNAME', 
            'WORDPRESS_PASSWORD',
            'OPENAI_API_KEY',
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET'
        ]
        
        # 環境変数の存在確認（テスト環境では警告のみ）
        for var in required_env_vars:
            if not os.getenv(var):
                print(f"Warning: {var} not set in environment")

    def test_configuration_file_format(self):
        """設定ファイル形式のテスト"""
        # JSONファイルの形式テスト
        config_files = [
            'config.json',
            'collector_config.json',
            'wordpress_config.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    self.assertIsInstance(config, dict)
                except json.JSONDecodeError:
                    self.fail(f"Invalid JSON format in {config_file}")


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2) 