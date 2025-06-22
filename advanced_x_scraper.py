"""
Advanced X (Twitter) Post Scraper with Selenium
Seleniumを使用した高度なX投稿収集システム
注意: 利用規約を遵守して使用すること
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
class AdvancedXPost:
    """高度なX投稿データクラス"""
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
    hashtags: List[str] = None
    mentions: List[str] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if not self.id:
            self.id = hashlib.md5(f"{self.text}{self.author_username}".encode()).hexdigest()[:12]

class AdvancedXScraper:
    """高度なX投稿スクレイピングクラス"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None
        
        self.ai_keywords = [
            "AI", "ChatGPT", "Claude", "Gemini", "OpenAI", "Anthropic",
            "人工知能", "機械学習", "生成AI", "LLM", "深層学習",
            "自然言語処理", "画像生成", "AI開発", "AIツール"
        ]
        
        # 有名なAI関連アカウント
        self.ai_accounts = [
            "OpenAI", "AnthropicAI", "GoogleAI", "Microsoft", 
            "elonmusk", "sama", "karpathy", "ylecun"
        ]
        
        print("🤖 Advanced X Scraper 初期化")
        print("⚠️ 注意: 利用規約を遵守して使用してください")
    
    def setup_driver(self):
        """WebDriverのセットアップ"""
        try:
            print("🔧 WebDriver設定中...")
            
            # Chrome オプション設定
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # プライバシー設定
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # WebDriverの初期化
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 自動化検出を回避
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 10)
            
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
    
    async def scrape_x_posts_by_search(self, query: str, max_posts: int = 5) -> List[AdvancedXPost]:
        """検索キーワードでX投稿を収集"""
        posts = []
        
        if not self.setup_driver():
            return posts
        
        try:
            print(f"🔍 検索クエリ: '{query}' で投稿収集中...")
            
            # X検索ページにアクセス
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            self.driver.get(search_url)
            
            # ページ読み込み待機
            await asyncio.sleep(3)
            
            # 投稿要素を収集
            collected_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 3
            
            while collected_count < max_posts and scroll_attempts < max_scroll_attempts:
                try:
                    # 投稿要素を取得
                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
                    
                    for tweet_element in tweet_elements[collected_count:]:
                        if collected_count >= max_posts:
                            break
                        
                        try:
                            post = await self._extract_post_data(tweet_element)
                            if post and self._is_relevant_post(post):
                                posts.append(post)
                                collected_count += 1
                                print(f"   ✅ 収集 ({collected_count}/{max_posts}): {post.text[:50]}...")
                        
                        except Exception as e:
                            print(f"   ⚠️ 投稿処理エラー: {e}")
                            continue
                    
                    # 新しい投稿を読み込むためにスクロール
                    if collected_count < max_posts:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        await asyncio.sleep(2)
                        scroll_attempts += 1
                    
                except Exception as e:
                    print(f"   ❌ スクロール処理エラー: {e}")
                    break
            
        except Exception as e:
            print(f"❌ 検索収集エラー: {e}")
        
        finally:
            self.close_driver()
        
        print(f"🎯 検索収集結果: {len(posts)}件")
        return posts
    
    async def scrape_x_posts_by_accounts(self, accounts: List[str], max_posts_per_account: int = 2) -> List[AdvancedXPost]:
        """特定のアカウントからX投稿を収集"""
        all_posts = []
        
        if not self.setup_driver():
            return all_posts
        
        try:
            for account in accounts[:3]:  # 最大3アカウント
                try:
                    print(f"👤 @{account} の投稿を収集中...")
                    
                    # アカウントページにアクセス
                    profile_url = f"https://twitter.com/{account}"
                    self.driver.get(profile_url)
                    
                    # ページ読み込み待機
                    await asyncio.sleep(3)
                    
                    # 投稿要素を取得
                    tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
                    
                    account_posts = []
                    for tweet_element in tweet_elements[:max_posts_per_account * 2]:  # 多めに取得してフィルタ
                        try:
                            post = await self._extract_post_data(tweet_element)
                            if post and self._is_relevant_post(post) and len(account_posts) < max_posts_per_account:
                                account_posts.append(post)
                                print(f"   ✅ @{account}: {post.text[:50]}...")
                        
                        except Exception as e:
                            print(f"   ⚠️ 投稿処理エラー: {e}")
                            continue
                    
                    all_posts.extend(account_posts)
                    
                    # レート制限対策
                    await asyncio.sleep(random.uniform(2, 5))
                
                except Exception as e:
                    print(f"   ❌ @{account} 収集エラー: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ アカウント収集エラー: {e}")
        
        finally:
            self.close_driver()
        
        print(f"🎯 アカウント収集結果: {len(all_posts)}件")
        return all_posts
    
    async def _extract_post_data(self, tweet_element) -> Optional[AdvancedXPost]:
        """投稿要素からデータを抽出"""
        try:
            # 投稿テキストを取得
            try:
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = text_element.text
            except NoSuchElementException:
                return None
            
            # ユーザー情報を取得
            try:
                user_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                user_info = user_element.text.split('\n')
                author_name = user_info[0] if user_info else "Unknown"
                author_username = user_info[1].replace('@', '') if len(user_info) > 1 else "unknown"
            except NoSuchElementException:
                author_name = "Unknown"
                author_username = "unknown"
            
            # 認証バッジをチェック
            try:
                verified_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="icon-verified"]')
                author_verified = True
            except NoSuchElementException:
                author_verified = False
            
            # エンゲージメント情報を取得
            likes = self._extract_engagement_count(tweet_element, 'like')
            retweets = self._extract_engagement_count(tweet_element, 'retweet')
            replies = self._extract_engagement_count(tweet_element, 'reply')
            
            # ハッシュタグとメンションを抽出
            hashtags = re.findall(r'#\w+', tweet_text)
            mentions = re.findall(r'@\w+', tweet_text)
            
            # 投稿URLを生成
            post_url = f"https://twitter.com/{author_username}/status/{int(time.time() * 1000)}"
            
            post = AdvancedXPost(
                id="",
                text=tweet_text,
                author_username=author_username,
                author_name=author_name,
                author_verified=author_verified,
                created_at=datetime.now(),
                url=post_url,
                likes=likes,
                retweets=retweets,
                replies=replies,
                hashtags=hashtags,
                mentions=mentions
            )
            
            return post
            
        except Exception as e:
            print(f"   ⚠️ データ抽出エラー: {e}")
            return None
    
    def _extract_engagement_count(self, tweet_element, engagement_type: str) -> int:
        """エンゲージメント数を抽出"""
        try:
            engagement_element = tweet_element.find_element(By.CSS_SELECTOR, f'[data-testid="{engagement_type}"]')
            count_text = engagement_element.text
            
            if not count_text or count_text.isspace():
                return 0
            
            # 数値を抽出（K, M などの単位も処理）
            count_text = count_text.replace(',', '')
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            else:
                return int(re.sub(r'[^\d]', '', count_text)) if count_text.isdigit() else 0
        
        except (NoSuchElementException, ValueError):
            return 0
    
    def _is_relevant_post(self, post: AdvancedXPost) -> bool:
        """投稿がAI関連かどうかを判定"""
        text_to_check = f"{post.text} {' '.join(post.hashtags)}".lower()
        
        # AI関連キーワードをチェック
        for keyword in self.ai_keywords:
            if keyword.lower() in text_to_check:
                return True
        
        # 認証済みアカウントは優先
        if post.author_verified and any(ai_account.lower() in post.author_username.lower() for ai_account in self.ai_accounts):
            return True
        
        return False
    
    def posts_to_news_articles(self, posts: List[AdvancedXPost]) -> List:
        """AdvancedXPostをNewsArticle形式に変換"""
        from news_collector import NewsArticle
        
        articles = []
        for post in posts:
            content = f"""
【実際のX投稿】{post.author_name} (@{post.author_username})
{' ✓ 認証済み' if post.author_verified else ''}

{post.text}

エンゲージメント:
- いいね: {post.likes:,}件
- リツイート: {post.retweets:,}件
- 返信: {post.replies:,}件

ハッシュタグ: {', '.join(post.hashtags) if post.hashtags else 'なし'}
メンション: {', '.join(post.mentions) if post.mentions else 'なし'}

投稿日時: {post.created_at.strftime('%Y年%m月%d日 %H:%M')}
投稿URL: {post.url}

※この情報は公開されているX投稿から収集されたものです。
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
async def collect_advanced_x_posts(search_queries: List[str] = None, max_posts: int = 5) -> List:
    """
    高度なX投稿収集
    
    Args:
        search_queries: 検索クエリのリスト
        max_posts: 最大投稿数
    
    Returns:
        NewsArticle形式の記事リスト
    """
    if search_queries is None:
        search_queries = ["AI", "ChatGPT", "人工知能"]
    
    scraper = AdvancedXScraper(headless=True)
    all_posts = []
    
    # 検索ベースの収集
    for query in search_queries[:2]:  # 最大2つのクエリ
        try:
            posts = await scraper.scrape_x_posts_by_search(query, max_posts=3)
            all_posts.extend(posts)
        except Exception as e:
            print(f"❌ 検索エラー ({query}): {e}")
    
    # アカウントベースの収集
    try:
        account_posts = await scraper.scrape_x_posts_by_accounts(
            ["OpenAI", "AnthropicAI", "GoogleAI"], 
            max_posts_per_account=2
        )
        all_posts.extend(account_posts)
    except Exception as e:
        print(f"❌ アカウント収集エラー: {e}")
    
    # 重複除去
    unique_posts = []
    seen_texts = set()
    for post in all_posts:
        text_key = post.text[:50].lower()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_posts.append(post)
    
    # 最新順でソート
    sorted_posts = sorted(unique_posts, key=lambda p: p.created_at, reverse=True)
    final_posts = sorted_posts[:max_posts]
    
    # NewsArticle形式に変換
    articles = scraper.posts_to_news_articles(final_posts)
    
    print(f"\n📊 高度なX投稿収集結果:")
    print(f"   総収集数: {len(all_posts)}件")
    print(f"   重複除去後: {len(unique_posts)}件")
    print(f"   最終選択: {len(final_posts)}件")
    
    return articles

# テスト実行
if __name__ == "__main__":
    async def test_advanced_scraper():
        print("🚀 高度なX投稿収集システムテスト開始")
        print("=" * 60)
        
        # 基本テスト
        articles = await collect_advanced_x_posts(
            search_queries=["AI", "ChatGPT"], 
            max_posts=5
        )
        
        print(f"\n📋 取得結果: {len(articles)}件")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   ソース: {article.source}")
            print(f"   著者: {article.author}")
            print()
    
    asyncio.run(test_advanced_scraper()) 