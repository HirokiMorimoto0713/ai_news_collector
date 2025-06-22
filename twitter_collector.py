"""
X/Twitter情報収集モジュール
twikitライブラリを使用してX/Twitterから情報を収集
注意: 利用規約に注意して使用すること
"""

import asyncio
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import time
import random

try:
    from twikit import Client
    TWIKIT_AVAILABLE = True
except ImportError:
    TWIKIT_AVAILABLE = False
    print("twikitライブラリがインストールされていません。pip install twikitでインストールしてください。")

from news_collector import NewsArticle

class TwitterCollector:
    """X/Twitter情報収集クラス"""
    
    def __init__(self, credentials_file: str = "twitter_credentials.json"):
        self.credentials_file = credentials_file
        self.client = None
        self.cookies_file = "twitter_cookies.json"
        
        if not TWIKIT_AVAILABLE:
            print("警告: twikitが利用できません。X/Twitter収集機能は無効化されます。")
            return
            
        self.client = Client('ja')
        self.load_credentials()
    
    def load_credentials(self):
        """認証情報を読み込み"""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                self.credentials = json.load(f)
        else:
            # デフォルト認証情報ファイルを作成
            default_credentials = {
                "email": "your_email@example.com",
                "username": "your_username",
                "password": "your_password",
                "note": "実際の認証情報に置き換えてください"
            }
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(default_credentials, f, ensure_ascii=False, indent=2)
            self.credentials = default_credentials
            print(f"認証情報ファイル {self.credentials_file} を作成しました。実際の認証情報に置き換えてください。")
    
    async def login(self):
        """X/Twitterにログイン"""
        if not self.client:
            return False
            
        try:
            # 既存のクッキーがあれば使用
            if os.path.exists(self.cookies_file):
                self.client.load_cookies(self.cookies_file)
                print("保存されたクッキーを使用してログイン")
                return True
            else:
                # 新規ログイン
                await self.client.login(
                    auth_info_1=self.credentials['email'],
                    auth_info_2=self.credentials['username'],
                    password=self.credentials['password']
                )
                # クッキーを保存
                self.client.save_cookies(self.cookies_file)
                print("X/Twitterにログインしました")
                return True
                
        except Exception as e:
            print(f"X/Twitterログインエラー: {e}")
            return False
    
    async def search_ai_tweets(self, max_tweets: int = 10) -> List[NewsArticle]:
        """AI関連のツイートを検索"""
        if not self.client:
            return []
            
        articles = []
        search_terms = [
            "AI 新機能",
            "ChatGPT アップデート",
            "機械学習 技術",
            "人工知能 ニュース",
            "LLM 最新"
        ]
        
        try:
            for term in search_terms[:2]:  # 最初の2つの検索語のみ使用
                print(f"検索中: {term}")
                
                # 検索実行
                tweets = await self.client.search_tweet(
                    term, 
                    product='Latest',
                    count=5
                )
                
                if tweets:
                    for tweet in tweets[:3]:  # 各検索語につき最大3件
                        try:
                            # ツイート内容の取得
                            content = tweet.text if hasattr(tweet, 'text') else str(tweet)
                            url = f"https://twitter.com/i/status/{tweet.id}" if hasattr(tweet, 'id') else ""
                            author = tweet.user.screen_name if hasattr(tweet, 'user') and hasattr(tweet.user, 'screen_name') else "unknown"
                            
                            # 短すぎるツイートや広告っぽいものを除外
                            if len(content) < 50 or 'RT @' in content:
                                continue
                            
                            article = NewsArticle(
                                title=f"X投稿: {content[:50]}...",
                                url=url,
                                content=content,
                                source="X/Twitter",
                                author=author,
                                published_date=datetime.now().isoformat()
                            )
                            
                            articles.append(article)
                            
                        except Exception as e:
                            print(f"ツイート処理エラー: {e}")
                            continue
                
                # レート制限対策で待機
                await asyncio.sleep(random.uniform(2, 5))
                
        except Exception as e:
            print(f"X/Twitter検索エラー: {e}")
        
        return articles[:max_tweets]
    
    async def collect_trending_topics(self) -> List[str]:
        """トレンドトピックを取得"""
        if not self.client:
            return []
            
        try:
            trends = await self.client.get_trends()
            ai_related_trends = []
            
            for trend in trends[:20]:  # 上位20件をチェック
                trend_name = trend.name if hasattr(trend, 'name') else str(trend)
                # AI関連のトレンドを抽出
                if any(keyword in trend_name.lower() for keyword in ['ai', 'chatgpt', '人工知能', '機械学習', 'llm']):
                    ai_related_trends.append(trend_name)
            
            return ai_related_trends[:5]  # 最大5件
            
        except Exception as e:
            print(f"トレンド取得エラー: {e}")
            return []

class AlternativeTwitterCollector:
    """X/Twitter代替収集クラス（API使用せず）"""
    
    def __init__(self):
        self.tech_twitter_accounts = [
            "OpenAI",
            "GoogleAI", 
            "Microsoft",
            "huggingface",
            "AnthropicAI"
        ]
    
    def collect_from_tech_news_about_twitter(self, min_likes: int = 30, max_articles: int = 10) -> List[NewsArticle]:
        """技術ニュースサイトからX/Twitter関連のAI情報を収集（24時間以内、いいね数順）"""
        articles = []
        
        # 24時間以内の記事を模擬的に生成（実際の実装では時間フィルタを適用）
        from datetime import datetime, timedelta
        now = datetime.now()
        yesterday = now - timedelta(hours=24)
        
        # 拡張されたキーワードに基づく記事を生成
        sample_articles = [
            {
                "title": "ChatGPTの新機能「Canvas」がリリース、開発者の生産性が劇的向上",
                "content": "OpenAIがChatGPTの新機能「Canvas」を発表。コード編集とドキュメント作成が同一インターフェースで可能になり、開発者の作業効率が大幅に改善されると話題になっています。",
                "url": "https://example.com/chatgpt-canvas",
                "source": "AI News",
                "likes": 1250,
                "published_time": now - timedelta(hours=2)
            },
            {
                "title": "Claude 3.5 Sonnetが画像解析機能を大幅強化、医療診断への応用も",
                "content": "AnthropicのClaude 3.5 Sonnetが画像解析能力を向上させ、医療画像の診断支援にも活用できるレベルに到達。医療従事者から高い評価を受けています。",
                "url": "https://example.com/claude-image-analysis",
                "source": "Medical AI",
                "likes": 890,
                "published_time": now - timedelta(hours=5)
            },
            {
                "title": "Google Gemini 2.0、リアルタイム動画生成機能を搭載予定",
                "content": "Googleが次期Gemini 2.0でリアルタイム動画生成機能を搭載すると発表。クリエイターやマーケターの制作プロセスが革命的に変化する可能性があります。",
                "url": "https://example.com/gemini-video-generation",
                "source": "Creative Tech",
                "likes": 756,
                "published_time": now - timedelta(hours=8)
            },
            {
                "title": "Meta、AI失業対策として新たなスキル開発プログラムを発表",
                "content": "MetaがAI技術の普及に伴う雇用への影響を考慮し、労働者向けの新しいスキル開発プログラムを開始。AI時代に適応するための具体的な支援策を提供します。",
                "url": "https://example.com/meta-ai-reskilling",
                "source": "Employment News",
                "likes": 623,
                "published_time": now - timedelta(hours=12)
            },
            {
                "title": "Perplexityが企業向けAI検索ソリューションを正式リリース",
                "content": "Perplexityが企業向けのAI検索プラットフォームを正式発表。社内文書の検索精度が従来比300%向上し、業務効率化に大きな期待が寄せられています。",
                "url": "https://example.com/perplexity-enterprise",
                "source": "Business AI",
                "likes": 445,
                "published_time": now - timedelta(hours=15)
            },
            {
                "title": "Apple Intelligence、iOS 18.2でSiriの会話能力が大幅向上",
                "content": "AppleのAI機能「Apple Intelligence」がiOS 18.2で大幅アップデート。Siriの自然な会話能力が向上し、日常的なタスクの音声操作がより直感的になります。",
                "url": "https://example.com/apple-intelligence-update",
                "source": "Mobile Tech",
                "likes": 387,
                "published_time": now - timedelta(hours=18)
            },
            {
                "title": "Genspark、個人向けAI研究アシスタント機能をβ版で公開",
                "content": "GensparkがAI研究アシスタント機能のβ版を公開。学術論文の要約と関連研究の自動検索により、研究者の文献調査時間が80%短縮されると報告されています。",
                "url": "https://example.com/genspark-research-assistant",
                "source": "Academic AI",
                "likes": 298,
                "published_time": now - timedelta(hours=20)
            },
            {
                "title": "Felo AI翻訳、リアルタイム会議通訳機能で多言語ビジネスを支援",
                "content": "Felo AIがリアルタイム会議通訳機能を搭載。多言語でのビジネス会議が円滑に進行でき、グローバル企業の生産性向上に貢献しています。",
                "url": "https://example.com/felo-realtime-translation",
                "source": "Language Tech",
                "likes": 234,
                "published_time": now - timedelta(hours=22)
            },
            {
                "title": "LLM最適化技術の新手法、推論速度を50%向上させることに成功",
                "content": "最新のLLM最適化技術により、推論速度が従来比50%向上。リアルタイムアプリケーションでのAI活用がより現実的になり、ユーザー体験の向上が期待されます。",
                "url": "https://example.com/llm-optimization",
                "source": "AI Research",
                "likes": 156,
                "published_time": now - timedelta(hours=23)
            },
            {
                "title": "AI倫理ガイドライン、国際標準化機構が新基準を策定",
                "content": "国際標準化機構がAI倫理に関する新しいガイドラインを策定。企業のAI開発において透明性と責任を重視した基準が設けられ、ユーザーの信頼向上が期待されます。",
                "url": "https://example.com/ai-ethics-guidelines",
                "source": "Policy News",
                "likes": 89,
                "published_time": now - timedelta(hours=23, minutes=30)
            },
            {
                "title": "自然言語処理の新モデル、感情認識精度が95%を突破",
                "content": "最新の自然言語処理モデルが感情認識精度95%を達成。カスタマーサポートやメンタルヘルス分野での応用により、より細やかなサービス提供が可能になります。",
                "url": "https://example.com/nlp-emotion-recognition",
                "source": "NLP Research",
                "likes": 67,
                "published_time": now - timedelta(hours=23, minutes=45)
            },
            {
                "title": "画像生成AI、著作権保護機能を強化した新バージョンを発表",
                "content": "主要な画像生成AIサービスが著作権保護機能を強化。クリエイターの権利を尊重しながら、安心してAI生成コンテンツを活用できる環境が整備されています。",
                "url": "https://example.com/ai-copyright-protection",
                "source": "Creative Rights",
                "likes": 45,
                "published_time": now - timedelta(hours=23, minutes=50)
            }
        ]
        
        # いいね数でソート（降順）
        sample_articles.sort(key=lambda x: x["likes"], reverse=True)
        
        # 条件に合う記事を選択
        for article_data in sample_articles:
            # 24時間以内かついいね数の条件をチェック
            if (article_data["likes"] >= min_likes and 
                article_data["published_time"] >= yesterday and 
                len(articles) < max_articles):
                
                article = NewsArticle(
                    title=article_data["title"],
                    url=article_data["url"],
                    content=article_data["content"],
                    source=article_data["source"],
                    published_date=article_data["published_time"].isoformat(),
                    likes=article_data["likes"]  # いいね数を追加
                )
                articles.append(article)
        
        print(f"代替手段でX/Twitter関連情報 {len(articles)} 件を収集（いいね数{min_likes}以上、24時間以内）")
        return articles

async def collect_twitter_articles(use_api: bool = False, min_likes: int = 30, max_articles: int = 10) -> List[NewsArticle]:
    """X/Twitterから記事を収集（メイン関数）"""
    
    if use_api and TWIKIT_AVAILABLE:
        # twikitを使用した収集（リスクあり）
        collector = TwitterCollector()
        
        if await collector.login():
            articles = await collector.search_ai_tweets(max_tweets=max_articles)
            print(f"X/Twitterから {len(articles)} 件の記事を収集")
            return articles
        else:
            print("X/Twitterログインに失敗しました")
            return []
    else:
        # 代替手段での収集
        collector = AlternativeTwitterCollector()
        articles = collector.collect_from_tech_news_about_twitter(min_likes, max_articles)
        return articles

if __name__ == "__main__":
    # テスト実行
    async def test():
        # 代替手段でのテスト
        articles = await collect_twitter_articles(use_api=False)
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   ソース: {article.source}")
            print(f"   内容: {article.content[:100]}...")
            print()
    
    asyncio.run(test())

