"""
シンプルなWebスクレイピングによる記事収集
ITmedia、GIGAZINE以外の追加情報源を含む
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import random

@dataclass
class SimpleArticle:
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[str] = None

class SimpleScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 情報源の設定（日本語サイト中心に大幅拡張）
        self.sources = {
            # 主要日本語ITニュースサイト
            'itmedia': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/news/subtop/aiplus/',
                'article_selector': 'h2.title a',
                'content_selector': '.inner p',
                'max_articles': 4
            },
            'gigazine': {
                'base_url': 'https://gigazine.net',
                'search_url': 'https://gigazine.net/news/tags/AI/',
                'article_selector': 'h2 a',
                'content_selector': '.preface, .article p',
                'max_articles': 4
            },
            'impress_watch': {
                'base_url': 'https://pc.watch.impress.co.jp',
                'search_url': 'https://pc.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 3
            },
            'ascii': {
                'base_url': 'https://ascii.jp',
                'search_url': 'https://ascii.jp/tech/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            'mynavi': {
                'base_url': 'https://news.mynavi.jp',
                'search_url': 'https://news.mynavi.jp/techplus/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            'nikkei_xtech': {
                'base_url': 'https://xtech.nikkei.com',
                'search_url': 'https://xtech.nikkei.com/atcl/nxt/news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            
            # 日本語AI専門サイト・技術サイト
            'cnet_japan': {
                'base_url': 'https://japan.cnet.com',
                'search_url': 'https://japan.cnet.com/tag/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            'internet_watch': {
                'base_url': 'https://internet.watch.impress.co.jp',
                'search_url': 'https://internet.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 3
            },
            'forest_watch': {
                'base_url': 'https://forest.watch.impress.co.jp',
                'search_url': 'https://forest.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 2
            },
            'akiba_pc_watch': {
                'base_url': 'https://akiba-pc.watch.impress.co.jp',
                'search_url': 'https://akiba-pc.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 2
            },
            'itmedia_mobile': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/mobile/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'itmedia_enterprise': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/enterprise/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'robotstart': {
                'base_url': 'https://robotstart.info',
                'search_url': 'https://robotstart.info/category/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 3
            },
            'ledge_ai': {
                'base_url': 'https://ledge.ai',
                'search_url': 'https://ledge.ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 3
            },
            'ainow': {
                'base_url': 'https://ainow.ai',
                'search_url': 'https://ainow.ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 3
            },
            'aismiley': {
                'base_url': 'https://aismiley.co.jp',
                'search_url': 'https://aismiley.co.jp/ai_news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 3
            },
            'codezine': {
                'base_url': 'https://codezine.jp',
                'search_url': 'https://codezine.jp/tag/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            'publickey': {
                'base_url': 'https://www.publickey1.jp',
                'search_url': 'https://www.publickey1.jp/blog/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 3
            },
            'gihyo': {
                'base_url': 'https://gihyo.jp',
                'search_url': 'https://gihyo.jp/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'atmarkit': {
                'base_url': 'https://atmarkit.itmedia.co.jp',
                'search_url': 'https://atmarkit.itmedia.co.jp/ait/subtop/features/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'techplus': {
                'base_url': 'https://news.mynavi.jp',
                'search_url': 'https://news.mynavi.jp/techplus/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 3
            },
            
            # 追加日本語サイト（大幅拡張）
            'watch_impress': {
                'base_url': 'https://www.watch.impress.co.jp',
                'search_url': 'https://www.watch.impress.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.body p',
                'max_articles': 2
            },
            'itmedia_business': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/business/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'nikkei_tech': {
                'base_url': 'https://www.nikkei.com',
                'search_url': 'https://www.nikkei.com/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'diamond_online': {
                'base_url': 'https://diamond.jp',
                'search_url': 'https://diamond.jp/category/technology',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'toyokeizai': {
                'base_url': 'https://toyokeizai.net',
                'search_url': 'https://toyokeizai.net/category/technology',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'business_insider_japan': {
                'base_url': 'https://www.businessinsider.jp',
                'search_url': 'https://www.businessinsider.jp/category/tech',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'yahoo_news_tech': {
                'base_url': 'https://news.yahoo.co.jp',
                'search_url': 'https://news.yahoo.co.jp/categories/it',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'zaikei': {
                'base_url': 'https://www.zaikei.co.jp',
                'search_url': 'https://www.zaikei.co.jp/category/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'jiji_tech': {
                'base_url': 'https://www.jiji.com',
                'search_url': 'https://www.jiji.com/jc/list?g=eco',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'kyodo_tech': {
                'base_url': 'https://this.kiji.is',
                'search_url': 'https://this.kiji.is/technology',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'sankei_tech': {
                'base_url': 'https://www.sankei.com',
                'search_url': 'https://www.sankei.com/economy/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'mainichi_tech': {
                'base_url': 'https://mainichi.jp',
                'search_url': 'https://mainichi.jp/tech/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'asahi_tech': {
                'base_url': 'https://www.asahi.com',
                'search_url': 'https://www.asahi.com/tech/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'yomiuri_tech': {
                'base_url': 'https://www.yomiuri.co.jp',
                'search_url': 'https://www.yomiuri.co.jp/science/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'nhk_tech': {
                'base_url': 'https://www3.nhk.or.jp',
                'search_url': 'https://www3.nhk.or.jp/news/tech/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'newswitch': {
                'base_url': 'https://newswitch.jp',
                'search_url': 'https://newswitch.jp/category/technology',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'fabcross': {
                'base_url': 'https://fabcross.jp',
                'search_url': 'https://fabcross.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'monoist': {
                'base_url': 'https://monoist.itmedia.co.jp',
                'search_url': 'https://monoist.itmedia.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'eetimes_japan': {
                'base_url': 'https://eetimes.itmedia.co.jp',
                'search_url': 'https://eetimes.itmedia.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'ednjapan': {
                'base_url': 'https://ednjapan.com',
                'search_url': 'https://ednjapan.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'techfactory': {
                'base_url': 'https://techfactory.itmedia.co.jp',
                'search_url': 'https://techfactory.itmedia.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'techtarget': {
                'base_url': 'https://techtarget.itmedia.co.jp',
                'search_url': 'https://techtarget.itmedia.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 2
            },
            'keyman': {
                'base_url': 'https://keyman.or.jp',
                'search_url': 'https://keyman.or.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'cloud_watch': {
                'base_url': 'https://cloud.watch.impress.co.jp',
                'search_url': 'https://cloud.watch.impress.co.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.body p',
                'max_articles': 2
            },
            'security_next': {
                'base_url': 'https://www.security-next.com',
                'search_url': 'https://www.security-next.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 1
            },
            'scan_netsecurity': {
                'base_url': 'https://scan.netsecurity.ne.jp',
                'search_url': 'https://scan.netsecurity.ne.jp/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 1
            },
            'dime': {
                'base_url': 'https://dime.jp',
                'search_url': 'https://dime.jp/genre/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'getnavijp': {
                'base_url': 'https://getnavi.jp',
                'search_url': 'https://getnavi.jp/digital/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'bcnretail': {
                'base_url': 'https://www.bcnretail.com',
                'search_url': 'https://www.bcnretail.com/news/detail/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'ipa_go_jp': {
                'base_url': 'https://www.ipa.go.jp',
                'search_url': 'https://www.ipa.go.jp/about/press/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 1
            },
            'nisc_go_jp': {
                'base_url': 'https://www.nisc.go.jp',
                'search_url': 'https://www.nisc.go.jp/news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 1
            }
        }
    
    def get_page_content(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """ページの内容を取得"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"ページ取得エラー ({url}): {e}")
            return None
    
    def extract_article_content(self, url: str, content_selector: str) -> str:
        """記事の本文を抽出"""
        soup = self.get_page_content(url)
        if not soup:
            return ""
        
        try:
            # 複数のセレクターを試行
            selectors = content_selector.split(', ')
            content_parts = []
            
            for selector in selectors:
                elements = soup.select(selector.strip())
                for element in elements[:10]:  # 最初の10個まで
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:  # 意味のあるテキストのみ
                        content_parts.append(text)
            
            # 一般的なセレクターも試行
            if not content_parts:
                generic_selectors = [
                    'article p',
                    '.content p',
                    '.post p',
                    '.entry-content p',
                    'main p',
                    'p'
                ]
                
                for selector in generic_selectors:
                    elements = soup.select(selector)
                    for element in elements[:15]:
                        text = element.get_text(strip=True)
                        if text and len(text) > 30:
                            content_parts.append(text)
                    if content_parts:
                        break
            
            return ' '.join(content_parts[:8])  # 最初の8段落まで
            
        except Exception as e:
            print(f"本文抽出エラー ({url}): {e}")
            return ""
    
    def collect_from_source(self, source_name: str, source_config: dict) -> List[SimpleArticle]:
        """特定の情報源から記事を収集"""
        articles = []
        
        try:
            print(f"{source_name}から記事を収集中...")
            
            # 検索ページを取得
            soup = self.get_page_content(source_config['search_url'])
            if not soup:
                print(f"{source_name}: 検索ページの取得に失敗")
                return articles
            
            # 記事リンクを取得
            article_links = soup.select(source_config['article_selector'])
            
            processed_count = 0
            max_articles = source_config.get('max_articles', 3)
            
            for link in article_links:
                if processed_count >= max_articles:
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
                    ai_keywords = ['AI', 'ai', 'Ai', '人工知能', 'ChatGPT', 'GPT', 'LLM', 
                                  '機械学習', 'ディープラーニング', 'OpenAI', 'Google', 'Meta',
                                  'Claude', 'Gemini', 'Anthropic', '生成AI', 'Copilot']
                    
                    if not any(keyword in title for keyword in ai_keywords):
                        continue
                    
                    print(f"  記事処理中: {title[:50]}...")
                    
                    # 本文を取得
                    content = self.extract_article_content(article_url, source_config['content_selector'])
                    
                    if content and len(content) > 100:
                        article = SimpleArticle(
                            title=title,
                            url=article_url,
                            content=content,
                            source=source_name,
                            published_date=datetime.now().isoformat()
                        )
                        articles.append(article)
                        processed_count += 1
                        print(f"  ✓ 記事を収集: {title[:50]}...")
                    
                    # レート制限
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"  記事処理エラー: {e}")
                    continue
            
            print(f"{source_name}: {len(articles)} 件の記事を収集")
            
        except Exception as e:
            print(f"{source_name}収集エラー: {e}")
        
        return articles
    
    def collect_all_articles(self) -> List[SimpleArticle]:
        """全ての情報源から記事を収集"""
        all_articles = []
        
        print("=== 拡張スクレイピング開始 ===")
        
        for source_name, source_config in self.sources.items():
            try:
                articles = self.collect_from_source(source_name, source_config)
                all_articles.extend(articles)
                
                # ソース間の間隔
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"{source_name}でエラー: {e}")
                continue
        
        print(f"=== 収集完了: 合計 {len(all_articles)} 件 ===")
        return all_articles

# テスト実行
if __name__ == "__main__":
    scraper = SimpleScraper()
    articles = scraper.collect_all_articles()
    
    print(f"\n=== 収集結果 ===")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   ソース: {article.source}")
        print(f"   URL: {article.url}")
        print(f"   本文: {article.content[:100]}...")
        print() 