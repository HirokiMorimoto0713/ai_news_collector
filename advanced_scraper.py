"""
高度なWebスクレイピングシステム
- 並列処理による高速化
- キャッシュ機能
- 強化されたエラーハンドリング
- レート制限対応
- User-Agentローテーション
"""

import asyncio
import aiohttp
import json
import os
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AdvancedArticle:
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[str] = None
    scraped_at: str = None
    cache_key: str = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
        if self.cache_key is None:
            self.cache_key = hashlib.md5(self.url.encode()).hexdigest()

class AdvancedScraper:
    def __init__(self, cache_dir: str = "cache", max_concurrent: int = 10):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_concurrent = max_concurrent
        self.session = None
        
        # User-Agentローテーション
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        # レート制限設定（サイトごと）
        self.rate_limits = {
            'default': 1.0,  # 1秒間隔
            'aggressive': 0.5,  # 0.5秒間隔
            'conservative': 2.0,  # 2秒間隔
            'premium': 0.1  # 0.1秒間隔（プレミアムサイト用）
        }
        
        # サイト別設定
        self.site_configs = self._load_site_configs()
        
        # 最後のアクセス時間記録
        self.last_access = {}
    
    def _load_site_configs(self) -> Dict:
        """サイト別設定を読み込み"""
        from simple_scraper import SimpleScraper
        simple_scraper = SimpleScraper()
        return simple_scraper.sources
    
    def _get_random_user_agent(self) -> str:
        """ランダムなUser-Agentを取得"""
        return random.choice(self.user_agents)
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """キャッシュファイルパスを取得"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 6) -> bool:
        """キャッシュの有効性をチェック"""
        if not cache_path.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_time < timedelta(hours=max_age_hours)
    
    def _load_from_cache(self, cache_key: str) -> Optional[AdvancedArticle]:
        """キャッシュから記事を読み込み"""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AdvancedArticle(**data)
            except Exception as e:
                logger.warning(f"キャッシュ読み込みエラー {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, article: AdvancedArticle):
        """記事をキャッシュに保存"""
        try:
            cache_path = self._get_cache_path(article.cache_key)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(article), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー {article.cache_key}: {e}")
    
    async def _wait_for_rate_limit(self, site_key: str):
        """レート制限を適用"""
        rate_limit = self.rate_limits.get('default', 1.0)
        
        # サイト固有の設定があれば使用
        if site_key in self.site_configs:
            rate_type = self.site_configs[site_key].get('rate_limit', 'default')
            rate_limit = self.rate_limits.get(rate_type, rate_limit)
        
        last_time = self.last_access.get(site_key, 0)
        elapsed = time.time() - last_time
        
        if elapsed < rate_limit:
            wait_time = rate_limit - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_access[site_key] = time.time()
    
    async def _get_page_content(self, url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
        """ページの内容を非同期で取得"""
        try:
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            async with self.session.get(url, headers=headers, timeout=timeout_config) as response:
                if response.status == 200:
                    content = await response.text()
                    return BeautifulSoup(content, 'html.parser')
                else:
                    logger.warning(f"HTTP {response.status}: {url}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"タイムアウト: {url}")
        except Exception as e:
            logger.warning(f"ページ取得エラー ({url}): {e}")
        
        return None
    
    async def _extract_article_content(self, url: str, content_selector: str) -> str:
        """記事の本文を非同期で抽出"""
        soup = await self._get_page_content(url)
        if not soup:
            return ""
        
        try:
            # 複数のセレクターを試行
            selectors = content_selector.split(', ')
            content_parts = []
            
            for selector in selectors:
                elements = soup.select(selector.strip())
                for element in elements[:15]:  # 最初の15個まで
                    text = element.get_text(strip=True)
                    if text and len(text) > 30:  # 意味のあるテキストのみ
                        content_parts.append(text)
            
            # 一般的なセレクターも試行
            if not content_parts:
                generic_selectors = [
                    'article p', '.content p', '.post p', '.entry-content p',
                    'main p', '.article-body p', '.post-content p', 'p'
                ]
                
                for selector in generic_selectors:
                    elements = soup.select(selector)
                    for element in elements[:20]:
                        text = element.get_text(strip=True)
                        if text and len(text) > 40:
                            content_parts.append(text)
                    if content_parts:
                        break
            
            return ' '.join(content_parts[:10])  # 最初の10段落まで
            
        except Exception as e:
            logger.warning(f"本文抽出エラー ({url}): {e}")
            return ""
    
    async def _collect_from_source(self, source_name: str, source_config: dict) -> List[AdvancedArticle]:
        """特定の情報源から記事を非同期で収集"""
        articles = []
        
        try:
            logger.info(f"🔍 {source_name}から記事を収集中...")
            
            # レート制限適用
            await self._wait_for_rate_limit(source_name)
            
            # 検索ページを取得
            soup = await self._get_page_content(source_config['search_url'])
            if not soup:
                logger.warning(f"❌ {source_name}: 検索ページの取得に失敗")
                return articles
            
            # 記事リンクを取得
            article_links = soup.select(source_config['article_selector'])
            
            # 並列処理用のタスクを作成
            tasks = []
            max_articles = source_config.get('max_articles', 3)
            
            for i, link in enumerate(article_links[:max_articles * 2]):  # 余分に取得
                if len(tasks) >= max_articles:
                    break
                
                try:
                    href = link.get('href')
                    if not href or not isinstance(href, str):
                        continue
                    
                    # 相対URLを絶対URLに変換
                    if href.startswith('/'):
                        article_url = source_config['base_url'] + href
                    elif href.startswith('http'):
                        article_url = href
                    else:
                        continue
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # AI関連キーワードをチェック
                    ai_keywords = [
                        'AI', 'ai', 'Ai', '人工知能', 'ChatGPT', 'GPT', 'LLM', 
                        '機械学習', 'ディープラーニング', 'OpenAI', 'Google', 'Meta',
                        'Claude', 'Gemini', 'Anthropic', '生成AI', 'Copilot',
                        'Microsoft', 'Amazon', 'Tesla', 'NVIDIA', 'robot', 'Robot',
                        'automation', 'neural', 'algorithm', 'data science'
                    ]
                    
                    if not any(keyword in title for keyword in ai_keywords):
                        continue
                    
                    # キャッシュチェック
                    cache_key = hashlib.md5(article_url.encode()).hexdigest()
                    cached_article = self._load_from_cache(cache_key)
                    
                    if cached_article:
                        logger.info(f"📋 キャッシュから取得: {title[:50]}...")
                        articles.append(cached_article)
                        continue
                    
                    # 非同期タスクを作成
                    task = self._process_article(article_url, title, source_name, source_config)
                    tasks.append(task)
                    
                except Exception as e:
                    logger.warning(f"記事リンク処理エラー: {e}")
                    continue
            
            # 並列実行
            if tasks:
                logger.info(f"⚡ {len(tasks)}件の記事を並列処理中...")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, AdvancedArticle):
                        articles.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"記事処理エラー: {result}")
            
            logger.info(f"✅ {source_name}: {len(articles)} 件の記事を収集")
            return articles
            
        except Exception as e:
            logger.error(f"❌ {source_name}収集エラー: {e}")
            return articles
    
    async def _process_article(self, url: str, title: str, source: str, source_config: dict) -> Optional[AdvancedArticle]:
        """個別記事を処理"""
        try:
            # レート制限適用
            await self._wait_for_rate_limit(source)
            
            logger.info(f"📄 記事処理中: {title[:50]}...")
            
            # 本文を取得
            content = await self._extract_article_content(url, source_config['content_selector'])
            
            if not content or len(content) < 100:
                logger.warning(f"⚠️  本文が短すぎます: {title[:30]}...")
                return None
            
            # 記事オブジェクトを作成
            article = AdvancedArticle(
                title=title,
                url=url,
                content=content,
                source=source,
                published_date=datetime.now().isoformat()
            )
            
            # キャッシュに保存
            self._save_to_cache(article)
            
            logger.info(f"✅ 記事処理完了: {title[:50]}...")
            return article
            
        except Exception as e:
            logger.warning(f"記事処理エラー ({url}): {e}")
            return None
    
    async def collect_all_articles(self, max_total_articles: int = 20) -> List[AdvancedArticle]:
        """全ソースから記事を並列収集"""
        all_articles = []
        
        logger.info("🚀 高度スクレイピング開始")
        
        # セッション作成
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # 並列処理用のタスクを作成
            tasks = []
            
            for source_name, source_config in self.site_configs.items():
                task = self._collect_from_source(source_name, source_config)
                tasks.append(task)
            
            # セマフォで同時実行数を制限
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            # 並列実行
            logger.info(f"⚡ {len(tasks)}サイトを並列処理中...")
            results = await asyncio.gather(*[limited_task(task) for task in tasks], return_exceptions=True)
            
            # 結果をまとめる
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"サイト収集エラー: {result}")
        
        # 重複除去
        unique_articles = self._remove_duplicates(all_articles)
        
        # 最大件数まで制限
        final_articles = unique_articles[:max_total_articles]
        
        logger.info(f"🎉 高度スクレイピング完了: {len(final_articles)}件の記事を収集")
        return final_articles
    
    def _remove_duplicates(self, articles: List[AdvancedArticle]) -> List[AdvancedArticle]:
        """重複記事を除去"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # URLとタイトルの両方でチェック
            title_key = article.title.lower().strip()
            
            if article.url not in seen_urls and title_key not in seen_titles:
                seen_urls.add(article.url)
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        logger.info(f"📊 重複除去: {len(articles)} → {len(unique_articles)} 件")
        return unique_articles
    
    def clear_cache(self, max_age_days: int = 7):
        """古いキャッシュを削除"""
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_time:
                    cache_file.unlink()
                    deleted_count += 1
            
            logger.info(f"🗑️  古いキャッシュを削除: {deleted_count} 件")
            
        except Exception as e:
            logger.warning(f"キャッシュ削除エラー: {e}")

# 使用例
async def main():
    scraper = AdvancedScraper(max_concurrent=15)
    
    # 古いキャッシュを削除
    scraper.clear_cache(max_age_days=1)
    
    # 記事を収集
    articles = await scraper.collect_all_articles(max_total_articles=25)
    
    print(f"収集完了: {len(articles)} 件")
    for article in articles[:5]:  # 最初の5件を表示
        print(f"- {article.title} ({article.source})")

if __name__ == "__main__":
    asyncio.run(main()) 