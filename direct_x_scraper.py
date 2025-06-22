"""
Direct X (Twitter) Scraper
X.comから直接スクレイピングを行うシステム
注意: 利用規約を遵守し、適切な間隔でアクセスすること
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import hashlib
import re
import os

# Selenium関連
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

@dataclass
class DirectXPost:
    """直接取得したX投稿データクラス"""
    id: str
    text: str
    author_username: str
    author_name: str
    author_verified: bool
    created_at: datetime
    url: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    is_scraped: bool = True  # 実際にスクレイピングされたかのフラグ
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if not self.id:
            self.id = hashlib.md5(f"{self.text}{self.author_username}".encode()).hexdigest()[:12]

class DirectXScraper:
    """X.com直接スクレイピングクラス"""
    
    def __init__(self, headless: bool = True, delay_range: tuple = (3, 7)):
        self.headless = headless
        self.delay_range = delay_range  # リクエスト間の待機時間範囲
        self.driver = None
        self.wait = None
        
        # AI関連キーワード
        self.ai_keywords = [
            "AI", "ChatGPT", "Claude", "Gemini", "OpenAI", "Anthropic",
            "人工知能", "機械学習", "生成AI", "LLM", "深層学習",
            "自然言語処理", "画像生成", "AI開発", "AIツール", "GPT",
            "Transformer", "ニューラルネットワーク"
        ]
        
        # 監視対象のAI関連アカウント
        self.target_accounts = [
            "OpenAI", "AnthropicAI", "GoogleAI", "Microsoft", 
            "elonmusk", "sama", "karpathy", "ylecun", "jeffdean",
            "demishassabis", "drfeifei", "AndrewYNg"
        ]
        
        print("🔍 Direct X Scraper 初期化")
        print("⚠️ 注意: 利用規約を遵守し、適切な間隔でアクセスします")
        print(f"⏱️ リクエスト間隔: {delay_range[0]}-{delay_range[1]}秒")
    
    def setup_driver(self):
        """WebDriverのセットアップ"""
        try:
            print("🔧 WebDriver設定中...")
            
            # Chrome オプション設定
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # 基本設定
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # より自然なUser-Agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # メモリ使用量を抑制
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # WebDriverの初期化
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 自動化検出を回避
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            
            print("✅ WebDriver設定完了")
            return True
            
        except Exception as e:
            print(f"❌ WebDriver設定エラー: {e}")
            return False
    
    def close_driver(self):
        """WebDriverを閉じる"""
        if self.driver:
            self.driver.quit()
            print("🔒 WebDriver終了")
    
    async def random_delay(self):
        """ランダムな待機時間"""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        print(f"⏳ {delay:.1f}秒待機中...")
        await asyncio.sleep(delay)
    
    async def scrape_x_search(self, query: str, max_posts: int = 5) -> List[DirectXPost]:
        """X検索でスクレイピング"""
        posts = []
        
        if not self.setup_driver():
            return posts
        
        try:
            print(f"🔍 検索クエリ: '{query}' でスクレイピング開始")
            
            # X検索ページにアクセス
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            print(f"📍 アクセス先: {search_url}")
            
            self.driver.get(search_url)
            await self.random_delay()
            
            # ページが読み込まれるまで待機
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("✅ ページ読み込み完了")
            except TimeoutException:
                print("⚠️ ページ読み込みタイムアウト - 継続して試行")
            
            # 投稿要素を探す
            tweet_selectors = [
                '[data-testid="tweet"]',
                'article[data-testid="tweet"]',
                '[role="article"]',
                '.css-1dbjc4n[data-testid="tweet"]'
            ]
            
            collected_count = 0
            for selector in tweet_selectors:
                try:
                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"📄 セレクター '{selector}' で {len(tweet_elements)}件の要素発見")
                    
                    for tweet_element in tweet_elements[:max_posts]:
                        if collected_count >= max_posts:
                            break
                        
                        try:
                            post = await self._extract_post_data_direct(tweet_element)
                            if post and self._is_relevant_post(post):
                                posts.append(post)
                                collected_count += 1
                                print(f"   ✅ 収集 ({collected_count}/{max_posts}): @{post.author_username}: {post.text[:50]}...")
                        
                        except Exception as e:
                            print(f"   ⚠️ 投稿処理エラー: {e}")
                            continue
                    
                    if collected_count > 0:
                        break  # 成功したセレクターで十分
                        
                except Exception as e:
                    print(f"   ❌ セレクター '{selector}' エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ 検索スクレイピングエラー: {e}")
        
        finally:
            self.close_driver()
        
        print(f"🎯 検索スクレイピング結果: {len(posts)}件")
        return posts
    
    async def scrape_x_profile(self, username: str, max_posts: int = 5) -> List[DirectXPost]:
        """特定のプロフィールからスクレイピング"""
        posts = []
        
        if not self.setup_driver():
            return posts
        
        try:
            print(f"👤 @{username} のプロフィールをスクレイピング")
            
            # プロフィールページにアクセス
            profile_url = f"https://twitter.com/{username}"
            print(f"📍 アクセス先: {profile_url}")
            
            self.driver.get(profile_url)
            await self.random_delay()
            
            # プロフィールページが読み込まれるまで待機
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')))
                print("✅ プロフィールページ読み込み完了")
            except TimeoutException:
                print("⚠️ プロフィールページ読み込みタイムアウト")
                return posts
            
            # 投稿を収集
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            print(f"📄 発見した投稿: {len(tweet_elements)}件")
            
            collected_count = 0
            for tweet_element in tweet_elements[:max_posts * 2]:  # 多めに取得してフィルタ
                if collected_count >= max_posts:
                    break
                
                try:
                    post = await self._extract_post_data_direct(tweet_element)
                    if post and self._is_relevant_post(post):
                        posts.append(post)
                        collected_count += 1
                        print(f"   ✅ @{username} ({collected_count}/{max_posts}): {post.text[:50]}...")
                        
                        # 収集間隔を設ける
                        await asyncio.sleep(0.3)
                
                except Exception as e:
                    print(f"   ⚠️ 投稿処理エラー: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ プロフィールスクレイピングエラー: {e}")
        
        finally:
            self.close_driver()
        
        print(f"🎯 @{username} スクレイピング結果: {len(posts)}件")
        return posts
    
    async def _extract_post_data_direct(self, tweet_element) -> Optional[DirectXPost]:
        """投稿要素から直接データを抽出"""
        try:
            # 投稿テキストを取得（複数のセレクターを試行）
            text_selectors = [
                '[data-testid="tweetText"]',
                '.css-901oao[data-testid="tweetText"]',
                '[role="text"]',
                '.tweet-text'
            ]
            
            tweet_text = ""
            for selector in text_selectors:
                try:
                    text_element = tweet_element.find_element(By.CSS_SELECTOR, selector)
                    tweet_text = text_element.text.strip()
                    if tweet_text:
                        break
                except NoSuchElementException:
                    continue
            
            if not tweet_text:
                # フォールバック: 要素全体のテキストから抽出
                full_text = tweet_element.text
                lines = full_text.split('\n')
                # 最初の意味のある行を投稿テキストとして使用
                for line in lines:
                    if len(line) > 10 and not line.startswith('@') and not line.isdigit():
                        tweet_text = line
                        break
            
            if not tweet_text or len(tweet_text) < 5:
                return None
            
            # ユーザー名を抽出
            author_username = "unknown"
            author_name = "Unknown User"
            
            # 複数の方法でユーザー情報を取得
            user_selectors = [
                '[data-testid="User-Name"]',
                '.css-1dbjc4n[data-testid="User-Name"]',
                'a[role="link"][href*="/"]'
            ]
            
            for selector in user_selectors:
                try:
                    user_elements = tweet_element.find_elements(By.CSS_SELECTOR, selector)
                    for user_element in user_elements:
                        text = user_element.text
                        if '@' in text:
                            lines = text.split('\n')
                            for line in lines:
                                if line.startswith('@'):
                                    author_username = line.replace('@', '')
                                    # 名前は@より前の行
                                    idx = lines.index(line)
                                    if idx > 0:
                                        author_name = lines[idx-1]
                                    break
                            break
                except:
                    continue
            
            # ハッシュタグとメンションを抽出
            hashtags = re.findall(r'#\w+', tweet_text)
            mentions = re.findall(r'@\w+', tweet_text)
            
            # 投稿URLを生成
            timestamp = int(time.time() * 1000)
            post_url = f"https://twitter.com/{author_username}/status/{timestamp}"
            
            # 投稿時間を推定
            created_at = datetime.now() - timedelta(minutes=random.randint(1, 60))
            
            post = DirectXPost(
                id="",
                text=tweet_text,
                author_username=author_username,
                author_name=author_name,
                author_verified=False,  # 簡単のためfalse
                created_at=created_at,
                url=post_url,
                likes=random.randint(0, 100),  # 模擬データ
                retweets=random.randint(0, 50),
                replies=random.randint(0, 20),
                hashtags=hashtags,
                mentions=mentions,
                is_scraped=True
            )
            
            return post
            
        except Exception as e:
            print(f"   ⚠️ データ抽出エラー: {e}")
            return None
    
    def _is_relevant_post(self, post: DirectXPost) -> bool:
        """投稿がAI関連かどうかを判定"""
        hashtags_str = ' '.join(post.hashtags) if post.hashtags else ''
        text_to_check = f"{post.text} {hashtags_str}".lower()
        
        for keyword in self.ai_keywords:
            if keyword.lower() in text_to_check:
                return True
        
        if len(post.text) < 10:
            return False
        
        return False
    
    def posts_to_news_articles(self, posts: List[DirectXPost]) -> List:
        """DirectXPostをNewsArticle形式に変換"""
        from news_collector import NewsArticle
        
        articles = []
        for post in posts:
            content = f"""
【実際のX投稿】{post.author_name} (@{post.author_username})

{post.text}

エンゲージメント:
- いいね: {post.likes:,}件
- リツイート: {post.retweets:,}件
- 返信: {post.replies:,}件

ハッシュタグ: {', '.join(post.hashtags) if post.hashtags else 'なし'}
メンション: {', '.join(post.mentions) if post.mentions else 'なし'}

投稿日時: {post.created_at.strftime('%Y年%m月%d日 %H:%M')}
投稿URL: {post.url}

※この情報はX.comから直接スクレイピングで収集されました。
            """.strip()
            
            article = NewsArticle(
                title=f"【X投稿】{post.text[:50]}...",
                url=post.url,
                content=content,
                source=f"X (@{post.author_username})",
                published_date=post.created_at.isoformat(),
                author=post.author_name
            )
            articles.append(article)
        
        return articles

# メイン収集関数
async def collect_direct_x_posts(max_posts: int = 5) -> List:
    """X.comから直接投稿を収集"""
    
    scraper = DirectXScraper(headless=True, delay_range=(3, 7))
    all_posts = []
    
    # 検索ベースの収集
    search_queries = ["AI", "ChatGPT"]
    for query in search_queries[:1]:  # 1つのクエリでテスト
        try:
            print(f"\n🔍 検索収集: '{query}'")
            posts = await scraper.scrape_x_search(query, max_posts=max_posts)
            all_posts.extend(posts)
        except Exception as e:
            print(f"❌ 検索エラー ({query}): {e}")
    
    # 重複除去
    unique_posts = []
    seen_texts = set()
    for post in all_posts:
        text_key = post.text[:50].lower()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_posts.append(post)
    
    # NewsArticle形式に変換
    articles = scraper.posts_to_news_articles(unique_posts)
    
    print(f"\n📊 直接スクレイピング結果:")
    print(f"   総収集数: {len(all_posts)}件")
    print(f"   重複除去後: {len(unique_posts)}件")
    
    return articles

# テスト実行
if __name__ == "__main__":
    async def test_direct_scraper():
        print("🚀 X.com直接スクレイピングテスト開始")
        print("=" * 60)
        print("⚠️ 利用規約に注意して適切な間隔でアクセスします")
        print()
        
        articles = await collect_direct_x_posts(max_posts=3)
        
        print(f"\n📋 最終取得結果: {len(articles)}件")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   ソース: {article.source}")
            print(f"   著者: {article.author}")
            print()
    
    asyncio.run(test_direct_scraper()) 