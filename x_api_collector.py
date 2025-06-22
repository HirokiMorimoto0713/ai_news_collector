"""
X API v2を使用した実際のX投稿収集
"""

import os
import tweepy
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

@dataclass
class XPost:
    """X投稿データクラス"""
    id: str
    text: str
    author_username: str
    author_name: str
    created_at: datetime
    public_metrics: dict
    url: str
    
class XAPICollector:
    """X API v2を使用した投稿収集クラス"""
    
    def __init__(self):
        """X API認証情報の初期化"""
        self.api_key = os.getenv('X_API_KEY')
        self.api_secret = os.getenv('X_API_SECRET')
        self.bearer_token = os.getenv('X_BEARER_TOKEN')
        self.access_token = os.getenv('X_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        
        if not all([self.api_key, self.api_secret, self.bearer_token, 
                   self.access_token, self.access_token_secret]):
            raise ValueError("X API認証情報が不足しています。.envファイルを確認してください。")
        
        # Tweepy クライアント初期化
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
    def search_ai_posts(self, max_results: int = 10, hours_back: int = 24) -> List[XPost]:
        """AI関連のX投稿を検索"""
        try:
            # 24時間前の日時を計算
            since_time = datetime.now() - timedelta(hours=hours_back)
            since_str = since_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # AI関連キーワードでの検索クエリ
            query = """
            (AI OR ChatGPT OR Claude OR "Gemini AI" OR OpenAI OR Anthropic OR 
             "機械学習" OR "人工知能" OR "生成AI" OR "LLM" OR "深層学習") 
            -is:retweet -is:reply lang:ja
            """
            
            # X API v2で検索実行
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id', 'context_annotations'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id'],
                start_time=since_str
            )
            
            if not tweets.data:
                print("検索結果が見つかりませんでした")
                return []
            
            # ユーザー情報のマッピング
            users = {}
            if tweets.includes and 'users' in tweets.includes:
                for user in tweets.includes['users']:
                    users[user.id] = user
            
            # XPost オブジェクトに変換
            x_posts = []
            for tweet in tweets.data:
                author = users.get(tweet.author_id)
                if author:
                    post = XPost(
                        id=tweet.id,
                        text=tweet.text,
                        author_username=author.username,
                        author_name=author.name,
                        created_at=tweet.created_at,
                        public_metrics=tweet.public_metrics,
                        url=f"https://twitter.com/{author.username}/status/{tweet.id}"
                    )
                    x_posts.append(post)
            
            print(f"X API: {len(x_posts)}件の投稿を取得しました")
            return x_posts
            
        except Exception as e:
            print(f"X API検索エラー: {e}")
            return []
    
    def filter_high_engagement_posts(self, posts: List[XPost], min_likes: int = 10) -> List[XPost]:
        """エンゲージメントが高い投稿をフィルタリング"""
        filtered_posts = []
        
        for post in posts:
            likes = post.public_metrics.get('like_count', 0)
            retweets = post.public_metrics.get('retweet_count', 0)
            replies = post.public_metrics.get('reply_count', 0)
            
            # エンゲージメントスコア計算
            engagement_score = likes + (retweets * 2) + (replies * 3)
            
            if likes >= min_likes or engagement_score >= 20:
                filtered_posts.append(post)
        
        print(f"エンゲージメントフィルタ: {len(filtered_posts)}件が条件を満たしました")
        return filtered_posts
    
    def posts_to_news_articles(self, posts: List[XPost]) -> List:
        """XPostをNewsArticle形式に変換"""
        from news_collector import NewsArticle
        
        articles = []
        for post in posts:
            # 投稿テキストを要約形式に整形
            content = f"""
            【X投稿】{post.author_name} (@{post.author_username})
            
            {post.text}
            
            エンゲージメント:
            - いいね: {post.public_metrics.get('like_count', 0)}件
            - リツイート: {post.public_metrics.get('retweet_count', 0)}件
            - 返信: {post.public_metrics.get('reply_count', 0)}件
            
            投稿日時: {post.created_at.strftime('%Y年%m月%d日 %H:%M')}
            """
            
            article = NewsArticle(
                title=f"【X話題】{post.text[:50]}...",
                url=post.url,
                content=content.strip(),
                source=f"X (@{post.author_username})",
                published_date=post.created_at.isoformat()
            )
            articles.append(article)
        
        return articles

async def collect_x_posts_api(max_articles: int = 5, min_likes: int = 10) -> List:
    """X API v2を使用してAI関連投稿を収集"""
    try:
        collector = XAPICollector()
        
        # AI関連投稿を検索
        posts = collector.search_ai_posts(max_results=20, hours_back=24)
        
        if not posts:
            return []
        
        # エンゲージメントでフィルタリング
        filtered_posts = collector.filter_high_engagement_posts(posts, min_likes=min_likes)
        
        # 最大記事数まで制限
        limited_posts = filtered_posts[:max_articles]
        
        # NewsArticle形式に変換
        articles = collector.posts_to_news_articles(limited_posts)
        
        print(f"X API収集完了: {len(articles)}件の記事を生成")
        return articles
        
    except Exception as e:
        print(f"X API収集エラー: {e}")
        return []

if __name__ == "__main__":
    # テスト実行
    async def test_x_api():
        print("=== X API v2 テスト ===")
        articles = await collect_x_posts_api(max_articles=3, min_likes=0)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   ソース: {article.source}")
            print(f"   内容: {article.content[:200]}...")
    
    asyncio.run(test_x_api()) 