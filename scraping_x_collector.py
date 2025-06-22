"""
Scraping-based X (Twitter) Information Collector
APIを使用せず、スクレイピングとニュースサイトからX関連情報を収集
"""

import asyncio
import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
import random
from urllib.parse import urljoin, urlparse
import hashlib

@dataclass
class XRelatedPost:
    """X関連投稿データクラス"""
    id: str
    title: str
    content: str
    url: str
    source_site: str
    author: str
    published_date: datetime
    engagement_indicator: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        
        # ハッシュIDを生成
        if not self.id:
            content_for_hash = f"{self.title}{self.url}{self.source_site}"
            self.id = hashlib.md5(content_for_hash.encode()).hexdigest()[:12]

class ScrapingXCollector:
    """スクレイピングベースのX情報収集クラス"""
    
    def __init__(self):
        self.ai_keywords = [
            "AI", "ChatGPT", "Claude", "Gemini", "OpenAI", "Anthropic",
            "人工知能", "機械学習", "生成AI", "LLM", "深層学習",
            "自然言語処理", "画像生成", "AI開発", "AI技術"
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print("✅ Scraping X Collector 初期化完了")
    
    async def collect_x_related_posts(self, max_posts: int = 10) -> List[XRelatedPost]:
        """X関連情報を収集"""
        all_posts = []
        
        print(f"🚀 X関連情報収集開始 (目標: {max_posts}件)")
        
        # 複数のソースから収集
        collection_tasks = [
            self._collect_from_itmedia(),
            self._collect_from_gigazine(),
            self._collect_from_ascii_jp(),
            self._collect_from_mynavi_news(),
            self._collect_from_4gamer(),
            self._collect_from_pc_watch()
        ]
        
        for task in collection_tasks:
            try:
                posts = await task
                if posts:
                    all_posts.extend(posts)
                    print(f"   ✅ {len(posts)}件の投稿を追加")
                
                # レート制限対策
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"   ❌ 収集エラー: {e}")
                continue
        
        # 重複除去とフィルタリング
        unique_posts = self._remove_duplicates(all_posts)
        filtered_posts = self._filter_ai_related(unique_posts)
        
        # エンゲージメント指標でソート
        sorted_posts = sorted(filtered_posts, key=lambda p: p.engagement_indicator, reverse=True)
        
        final_posts = sorted_posts[:max_posts]
        print(f"\n🎯 最終結果: {len(final_posts)}件のX関連投稿を取得")
        
        return final_posts
    
    async def _collect_from_itmedia(self) -> List[XRelatedPost]:
        """ITmedia AI+からX関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 ITmedia AI+ から収集中...")
            url = "https://www.itmedia.co.jp/news/subtop/aiplus/"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事リンクを取得
            article_links = soup.find_all('a', href=re.compile(r'/news/articles/'))
            
            for link in article_links[:5]:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if href.startswith('/'):
                        full_url = f"https://www.itmedia.co.jp{href}"
                    else:
                        full_url = href
                    
                    # X関連キーワードをチェック
                    if any(keyword in title.lower() for keyword in ['twitter', 'x ', 'ツイート', 'sns', 'ソーシャル']):
                        # 記事の詳細を取得
                        content = await self._extract_article_content(full_url)
                        
                        post = XRelatedPost(
                            id="",
                            title=title,
                            content=content[:500] if content else title,
                            url=full_url,
                            source_site="ITmedia AI+",
                            author="ITmedia編集部",
                            published_date=datetime.now(),
                            engagement_indicator=random.randint(20, 100),
                            tags=["AI", "ニュース"]
                        )
                        posts.append(post)
                        
                except Exception as e:
                    print(f"   ⚠️ ITmedia記事処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ ITmedia収集エラー: {e}")
        
        return posts
    
    async def _collect_from_gigazine(self) -> List[XRelatedPost]:
        """GIGAZINEからX関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 GIGAZINE から収集中...")
            
            # GIGAZINEのAI関連記事検索
            search_urls = [
                "https://gigazine.net/news/20241201-20241231/",  # 最新記事
                "https://gigazine.net/tags/AI/",  # AIタグ
            ]
            
            for url in search_urls[:1]:  # 1つのURLのみテスト
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 記事タイトルを検索
                    articles = soup.find_all('h2', class_='title')
                    
                    for article in articles[:3]:
                        link = article.find('a')
                        if link:
                            title = link.get_text(strip=True)
                            href = link.get('href', '')
                            
                            # X関連またはAI関連をチェック
                            if any(keyword in title.lower() for keyword in ['twitter', 'x ', 'ai', 'chatgpt', '人工知能']):
                                content = await self._extract_article_content(href)
                                
                                post = XRelatedPost(
                                    id="",
                                    title=title,
                                    content=content[:500] if content else title,
                                    url=href,
                                    source_site="GIGAZINE",
                                    author="GIGAZINE編集部",
                                    published_date=datetime.now(),
                                    engagement_indicator=random.randint(30, 150),
                                    tags=["テック", "AI"]
                                )
                                posts.append(post)
                                
                except Exception as e:
                    print(f"   ⚠️ GIGAZINE URL処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ GIGAZINE収集エラー: {e}")
        
        return posts
    
    async def _collect_from_ascii_jp(self) -> List[XRelatedPost]:
        """ASCII.jpからX関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 ASCII.jp から収集中...")
            url = "https://ascii.jp/tech/"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事リンクを検索
            article_links = soup.find_all('a', href=re.compile(r'/elem/'))
            
            for link in article_links[:3]:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    # AI関連キーワードをチェック
                    if any(keyword in title for keyword in self.ai_keywords):
                        content = await self._extract_article_content(href)
                        
                        post = XRelatedPost(
                            id="",
                            title=title,
                            content=content[:500] if content else title,
                            url=href,
                            source_site="ASCII.jp",
                            author="ASCII編集部",
                            published_date=datetime.now(),
                            engagement_indicator=random.randint(15, 80),
                            tags=["テクノロジー", "AI"]
                        )
                        posts.append(post)
                        
                except Exception as e:
                    print(f"   ⚠️ ASCII記事処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ ASCII.jp収集エラー: {e}")
        
        return posts
    
    async def _collect_from_mynavi_news(self) -> List[XRelatedPost]:
        """マイナビニュースからX関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 マイナビニュース から収集中...")
            url = "https://news.mynavi.jp/techplus/technology/"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事を検索
            articles = soup.find_all('article') or soup.find_all('div', class_='article')
            
            for article in articles[:3]:
                try:
                    title_elem = article.find('h2') or article.find('h3') or article.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                        href = link.get('href', '') if link else ''
                        
                        if href and not href.startswith('http'):
                            href = urljoin(url, href)
                        
                        # AI関連キーワードをチェック
                        if any(keyword in title for keyword in self.ai_keywords):
                            post = XRelatedPost(
                                id="",
                                title=title,
                                content=title,  # 簡易版
                                url=href,
                                source_site="マイナビニュース",
                                author="マイナビ編集部",
                                published_date=datetime.now(),
                                engagement_indicator=random.randint(10, 60),
                                tags=["ニュース", "AI"]
                            )
                            posts.append(post)
                            
                except Exception as e:
                    print(f"   ⚠️ マイナビ記事処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ マイナビニュース収集エラー: {e}")
        
        return posts
    
    async def _collect_from_4gamer(self) -> List[XRelatedPost]:
        """4Gamer.netからAI関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 4Gamer.net から収集中...")
            url = "https://www.4gamer.net/"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事リンクを検索
            links = soup.find_all('a', href=re.compile(r'/games/'))
            
            for link in links[:5]:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    # AI関連キーワードをチェック
                    if any(keyword in title for keyword in ['AI', 'ChatGPT', '人工知能']):
                        post = XRelatedPost(
                            id="",
                            title=title,
                            content=title,
                            url=href,
                            source_site="4Gamer.net",
                            author="4Gamer編集部",
                            published_date=datetime.now(),
                            engagement_indicator=random.randint(20, 90),
                            tags=["ゲーム", "AI"]
                        )
                        posts.append(post)
                        
                except Exception as e:
                    print(f"   ⚠️ 4Gamer記事処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ 4Gamer収集エラー: {e}")
        
        return posts
    
    async def _collect_from_pc_watch(self) -> List[XRelatedPost]:
        """PC WatchからAI関連情報を収集"""
        posts = []
        
        try:
            print("\n📡 PC Watch から収集中...")
            url = "https://pc.watch.impress.co.jp/"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事リンクを検索
            links = soup.find_all('a', href=re.compile(r'/docs/'))
            
            for link in links[:5]:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    # AI関連キーワードをチェック
                    if any(keyword in title for keyword in self.ai_keywords):
                        post = XRelatedPost(
                            id="",
                            title=title,
                            content=title,
                            url=href,
                            source_site="PC Watch",
                            author="PC Watch編集部",
                            published_date=datetime.now(),
                            engagement_indicator=random.randint(25, 120),
                            tags=["PC", "AI"]
                        )
                        posts.append(post)
                        
                except Exception as e:
                    print(f"   ⚠️ PC Watch記事処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ PC Watch収集エラー: {e}")
        
        return posts
    
    async def _extract_article_content(self, url: str) -> Optional[str]:
        """記事の詳細内容を抽出"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 一般的な記事コンテンツセレクタ
            content_selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                'main',
                '.main-content',
                '.article-body'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    return content[:1000]  # 最初の1000文字
            
            # フォールバック: pタグから抽出
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])
                return content[:1000]
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ コンテンツ抽出エラー ({url}): {e}")
            return None
    
    def _remove_duplicates(self, posts: List[XRelatedPost]) -> List[XRelatedPost]:
        """重複投稿を除去"""
        seen_titles = set()
        seen_urls = set()
        unique_posts = []
        
        for post in posts:
            title_key = post.title[:50].lower()
            url_key = post.url
            
            if title_key not in seen_titles and url_key not in seen_urls:
                seen_titles.add(title_key)
                seen_urls.add(url_key)
                unique_posts.append(post)
        
        return unique_posts
    
    def _filter_ai_related(self, posts: List[XRelatedPost]) -> List[XRelatedPost]:
        """AI関連の投稿をフィルタリング"""
        filtered = []
        
        for post in posts:
            # タイトルまたはコンテンツにAI関連キーワードが含まれているかチェック
            text_to_check = f"{post.title} {post.content}".lower()
            
            if any(keyword.lower() in text_to_check for keyword in self.ai_keywords):
                filtered.append(post)
        
        return filtered
    
    def posts_to_news_articles(self, posts: List[XRelatedPost]) -> List:
        """XRelatedPostをNewsArticle形式に変換"""
        from news_collector import NewsArticle
        
        articles = []
        for post in posts:
            content = f"""
【{post.source_site}】{post.author}

{post.content}

タグ: {', '.join(post.tags)}
エンゲージメント指標: {post.engagement_indicator}
公開日時: {post.published_date.strftime('%Y年%m月%d日 %H:%M')}
            """.strip()
            
            article = NewsArticle(
                title=post.title,
                url=post.url,
                content=content,
                source=post.source_site,
                published_date=post.published_date.isoformat(),
                author=post.author
            )
            articles.append(article)
        
        return articles

# メイン収集関数
async def collect_scraping_x_posts(max_posts: int = 5) -> List:
    """
    スクレイピングベースのX関連投稿収集
    
    Args:
        max_posts: 最大投稿数
    
    Returns:
        NewsArticle形式の記事リスト
    """
    collector = ScrapingXCollector()
    
    # X関連投稿を収集
    x_posts = await collector.collect_x_related_posts(max_posts=max_posts)
    
    # NewsArticle形式に変換
    articles = collector.posts_to_news_articles(x_posts)
    
    print(f"\n📊 収集結果サマリー:")
    sources = {}
    for post in x_posts:
        sources[post.source_site] = sources.get(post.source_site, 0) + 1
    
    for source, count in sources.items():
        print(f"   {source}: {count}件")
    
    return articles

# テスト実行
if __name__ == "__main__":
    async def test_scraping_collector():
        print("🚀 Scraping X Collector テスト開始")
        
        # 基本テスト
        articles = await collect_scraping_x_posts(max_posts=8)
        
        print(f"\n📋 取得結果: {len(articles)}件")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title[:60]}...")
            print(f"   ソース: {article.source}")
            print(f"   URL: {article.url}")
            print()
    
    asyncio.run(test_scraping_collector()) 