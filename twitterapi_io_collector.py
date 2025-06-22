"""
twitterapi.io を使用したX投稿収集モジュール
レート制限が緩く、安定したX投稿収集を提供
"""

import os
import requests
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

@dataclass
class TwitterAPIPost:
    """twitterapi.io からの投稿データクラス"""
    id: str
    text: str
    author_username: str
    author_name: str
    created_at: datetime
    public_metrics: dict
    url: str

class TwitterAPIIOCollector:
    """twitterapi.io を使用した投稿収集クラス"""
    
    def __init__(self):
        """twitterapi.io 認証情報の初期化"""
        self.api_key = os.getenv('TWITTERAPI_IO_KEY')
        
        if not self.api_key:
            raise ValueError("twitterapi.io APIキーが設定されていません。環境変数TWITTERAPI_IO_KEYを設定してください。")
        
        self.base_url = "https://api.twitterapi.io/twitter"
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def search_ai_posts(self, max_results: int = 10, hours_back: int = 24) -> List[TwitterAPIPost]:
        """AI関連のX投稿を検索"""
        try:
            # AI関連キーワードでの検索クエリ
            search_terms = [
                "AI OR ChatGPT OR Claude OR OpenAI OR Anthropic",
                "機械学習 OR 人工知能 OR 生成AI OR LLM",
                "Gemini AI OR GPT OR 深層学習"
            ]
            
            all_posts = []
            
            for query in search_terms:
                try:
                    # twitterapi.io の検索エンドポイント（Advanced Search使用）
                    params = {
                        'query': f'{query} -is:retweet -is:reply lang:ja',
                        'product': 'Top',
                        'count': max_results // len(search_terms)
                    }
                    
                    response = requests.get(
                        f"{self.base_url}/search",
                        headers=self.headers,
                        params=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = self._parse_response(data)
                        all_posts.extend(posts)
                        print(f"検索クエリ '{query[:30]}...': {len(posts)}件取得")
                    else:
                        print(f"検索エラー: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"検索クエリエラー ({query[:30]}...): {e}")
                    continue
            
            # 重複除去
            unique_posts = self._remove_duplicates(all_posts)
            print(f"twitterapi.io: {len(unique_posts)}件の投稿を取得しました")
            return unique_posts[:max_results]
            
        except Exception as e:
            print(f"twitterapi.io 検索エラー: {e}")
            return []
    
    def _parse_response(self, data: dict) -> List[TwitterAPIPost]:
        """APIレスポンスをパース"""
        posts = []
        
        # twitterapi.ioのレスポンス形式に対応
        if 'statuses' in data:
            tweets = data['statuses']
        elif 'data' in data:
            tweets = data['data']
        else:
            return posts
        
        # 投稿データの処理
        for tweet in tweets:
            try:
                # twitterapi.ioの形式に対応
                user = tweet.get('user', {})
                
                # 日時をパース
                created_at_str = tweet.get('created_at', '')
                if created_at_str:
                    try:
                        # Twitter APIの日時形式をパース
                        created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                        created_at = created_at.replace(tzinfo=None)
                    except:
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()
                
                post = TwitterAPIPost(
                    id=tweet.get('id_str', str(tweet.get('id', ''))),
                    text=tweet.get('text', ''),
                    author_username=user.get('screen_name', ''),
                    author_name=user.get('name', ''),
                    created_at=created_at,
                    public_metrics={
                        'like_count': tweet.get('favorite_count', 0),
                        'retweet_count': tweet.get('retweet_count', 0),
                        'reply_count': tweet.get('reply_count', 0)
                    },
                    url=f"https://twitter.com/{user.get('screen_name', '')}/status/{tweet.get('id_str', tweet.get('id', ''))}"
                )
                posts.append(post)
                
            except Exception as e:
                print(f"投稿パースエラー: {e}")
                continue
        
        return posts
    
    def _remove_duplicates(self, posts: List[TwitterAPIPost]) -> List[TwitterAPIPost]:
        """重複投稿を除去"""
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
        
        return unique_posts
    
    def filter_high_engagement_posts(self, posts: List[TwitterAPIPost], min_likes: int = 10) -> List[TwitterAPIPost]:
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
    
    def posts_to_news_articles(self, posts: List[TwitterAPIPost]) -> List:
        """TwitterAPIPostをNewsArticle形式に変換"""
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

async def collect_x_posts_twitterapi_io(max_articles: int = 5, min_likes: int = 10) -> List:
    """twitterapi.io を使用してAI関連投稿を収集"""
    try:
        collector = TwitterAPIIOCollector()
        
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
        
        print(f"twitterapi.io 収集完了: {len(articles)}件の記事を生成")
        return articles
        
    except Exception as e:
        print(f"twitterapi.io 収集エラー: {e}")
        return []

if __name__ == "__main__":
    # テスト実行
    async def test_twitterapi_io():
        print("=== twitterapi.io テスト ===")
        articles = await collect_x_posts_twitterapi_io(max_articles=3, min_likes=1)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   ソース: {article.source}")
            print(f"   内容: {article.content[:200]}...")
    
    asyncio.run(test_twitterapi_io()) 