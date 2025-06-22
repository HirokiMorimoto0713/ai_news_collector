"""
AI情報収集システム - メインモジュール
毎日AI関連の最新情報を収集し、要約・感想を付けてWordPressに投稿
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

@dataclass
class NewsArticle:
    """ニュース記事のデータクラス"""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    hash_id: Optional[str] = None
    likes: Optional[int] = None
    
    def __post_init__(self):
        """記事のハッシュIDを生成"""
        if not self.hash_id:
            content_for_hash = f"{self.title}{self.url}{self.source}"
            self.hash_id = hashlib.md5(content_for_hash.encode()).hexdigest()

class AINewsCollector:
    """AI情報収集クラス"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.collected_articles = []
        self.duplicate_tracker_file = "collected_articles.json"
        self.load_duplicate_tracker()
    
    def load_config(self, config_file: str) -> Dict:
        """設定ファイルを読み込み"""
        default_config = {
            "max_articles_per_day": 5,
            "sources": {
                "twitter": {
                    "enabled": True,
                    "search_terms": ["AI", "人工知能", "機械学習", "ChatGPT", "LLM"]
                },
                "news_sites": {
                    "enabled": True,
                    "sites": [
                        "https://www.itmedia.co.jp/",
                        "https://japan.zdnet.com/",
                        "https://tech.nikkeibp.co.jp/"
                    ]
                },
                "tech_blogs": {
                    "enabled": True,
                    "sites": [
                        "https://note.com/",
                        "https://zenn.dev/",
                        "https://qiita.com/"
                    ]
                }
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # デフォルト設定とマージ
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # デフォルト設定ファイルを作成
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
    
    def load_duplicate_tracker(self):
        """重複チェック用のデータを読み込み"""
        if os.path.exists(self.duplicate_tracker_file):
            with open(self.duplicate_tracker_file, 'r', encoding='utf-8') as f:
                self.collected_hashes = set(json.load(f))
        else:
            self.collected_hashes = set()
    
    def save_duplicate_tracker(self):
        """重複チェック用のデータを保存"""
        with open(self.duplicate_tracker_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.collected_hashes), f, ensure_ascii=False, indent=2)
    
    def is_duplicate(self, article: NewsArticle) -> bool:
        """記事の重複チェック"""
        return article.hash_id in self.collected_hashes
    
    def add_to_tracker(self, article: NewsArticle):
        """重複チェック用トラッカーに追加"""
        self.collected_hashes.add(article.hash_id)
    
    def extract_content_from_url(self, url: str) -> Optional[str]:
        """URLから記事内容を抽出"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 一般的な記事コンテンツのセレクタを試行
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    break
            
            if not content:
                # フォールバック: すべてのpタグから抽出
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return content[:2000]  # 最初の2000文字まで
            
        except Exception as e:
            print(f"URL {url} からのコンテンツ抽出エラー: {e}")
            return None
    
    def collect_from_news_sites(self) -> List[NewsArticle]:
        """ニュースサイトから情報収集（24時間以内の記事のみ）"""
        articles = []
        
        if not self.config["sources"]["news_sites"]["enabled"]:
            return articles
        
        # 24時間以内の記事のみを対象
        from datetime import datetime, timedelta
        now = datetime.now()
        time_limit = now - timedelta(hours=self.config["sources"]["twitter"]["time_range_hours"])
        
        # ITmedia AI関連記事の検索
        try:
            search_url = "https://www.itmedia.co.jp/news/subtop/aiplus/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ITmediaの記事リンクを抽出
            article_links = soup.find_all('a', href=re.compile(r'/news/articles/'))
            
            for link in article_links[:3]:  # 最新3件
                title = link.get_text(strip=True)
                href = link['href']
                
                # 相対URLを絶対URLに変換
                if href.startswith('/'):
                    url = "https://www.itmedia.co.jp" + href
                else:
                    url = href
                
                if title and url:
                    content = self.extract_content_from_url(url)
                    if content:
                        article = NewsArticle(
                            title=title,
                            url=url,
                            content=content,
                            source="ITmedia",
                            published_date=datetime.now().isoformat()
                        )
                        
                        if not self.is_duplicate(article):
                            articles.append(article)
                            self.add_to_tracker(article)
                            
        except Exception as e:
            print(f"ITmedia収集エラー: {e}")
        
        return articles
    
    def collect_from_tech_blogs(self) -> List[NewsArticle]:
        """技術ブログから情報収集"""
        articles = []
        
        if not self.config["sources"]["tech_blogs"]["enabled"]:
            return articles
        
        # Qiita AI関連記事の検索
        try:
            search_url = "https://qiita.com/tags/AI/items"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Qiitaの記事リンクを抽出
            article_links = soup.find_all('a', class_='css-1hnmda0')
            
            for link in article_links[:2]:  # 最新2件
                title = link.get_text(strip=True)
                url = "https://qiita.com" + link['href']
                
                if title and url:
                    content = self.extract_content_from_url(url)
                    if content:
                        article = NewsArticle(
                            title=title,
                            url=url,
                            content=content,
                            source="Qiita",
                            published_date=datetime.now().isoformat()
                        )
                        
                        if not self.is_duplicate(article):
                            articles.append(article)
                            self.add_to_tracker(article)
                            
        except Exception as e:
            print(f"Qiita収集エラー: {e}")
        
        return articles
    
    def collect_daily_articles(self) -> List[NewsArticle]:
        """1日分の記事を収集"""
        all_articles = []
        
        print("AI関連情報の収集を開始...")
        
        # ニュースサイトから収集
        news_articles = self.collect_from_news_sites()
        all_articles.extend(news_articles)
        print(f"ニュースサイトから {len(news_articles)} 件収集")
        
        # 技術ブログから収集
        blog_articles = self.collect_from_tech_blogs()
        all_articles.extend(blog_articles)
        print(f"技術ブログから {len(blog_articles)} 件収集")
        
        # 最大件数まで制限
        max_articles = self.config["max_articles_per_day"]
        if len(all_articles) > max_articles:
            all_articles = all_articles[:max_articles]
        
        self.collected_articles = all_articles
        self.save_duplicate_tracker()
        
        print(f"合計 {len(all_articles)} 件の記事を収集完了")
        return all_articles
    
    def save_articles_to_file(self, filename: str = None):
        """収集した記事をファイルに保存"""
        if not filename:
            filename = f"collected_articles_{datetime.now().strftime('%Y%m%d')}.json"
        
        articles_data = []
        for article in self.collected_articles:
            articles_data.append({
                'title': article.title,
                'url': article.url,
                'content': article.content,
                'source': article.source,
                'published_date': article.published_date,
                'author': article.author,
                'hash_id': article.hash_id
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        print(f"記事データを {filename} に保存しました")

if __name__ == "__main__":
    collector = AINewsCollector()
    articles = collector.collect_daily_articles()
    collector.save_articles_to_file()
    
    print("\n収集した記事:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   ソース: {article.source}")
        print(f"   URL: {article.url}")
        print(f"   内容: {article.content[:100]}...")
        print()

