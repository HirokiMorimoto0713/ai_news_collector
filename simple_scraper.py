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
        
        # 情報源の設定（大幅に拡張 - 30以上のサイト）
        self.sources = {
            # 日本語サイト（大幅拡張）
            'itmedia': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/news/subtop/aiplus/',
                'article_selector': 'h2.title a',
                'content_selector': '.inner p',
                'max_articles': 3
            },
            'gigazine': {
                'base_url': 'https://gigazine.net',
                'search_url': 'https://gigazine.net/news/tags/AI/',
                'article_selector': 'h2 a',
                'content_selector': '.preface, .article p',
                'max_articles': 3
            },
            'impress_watch': {
                'base_url': 'https://pc.watch.impress.co.jp',
                'search_url': 'https://pc.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 2
            },
            'ascii': {
                'base_url': 'https://ascii.jp',
                'search_url': 'https://ascii.jp/tech/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'mynavi': {
                'base_url': 'https://news.mynavi.jp',
                'search_url': 'https://news.mynavi.jp/techplus/technology/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'nikkei_xtech': {
                'base_url': 'https://xtech.nikkei.com',
                'search_url': 'https://xtech.nikkei.com/atcl/nxt/news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            
            # 追加日本語サイト
            'cnet_japan': {
                'base_url': 'https://japan.cnet.com',
                'search_url': 'https://japan.cnet.com/tag/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'internet_watch': {
                'base_url': 'https://internet.watch.impress.co.jp',
                'search_url': 'https://internet.watch.impress.co.jp/docs/news/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.body p',
                'max_articles': 2
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
                'max_articles': 1
            },
            'itmedia_mobile': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/mobile/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 1
            },
            'itmedia_enterprise': {
                'base_url': 'https://www.itmedia.co.jp',
                'search_url': 'https://www.itmedia.co.jp/enterprise/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 1
            },
            'robotstart': {
                'base_url': 'https://robotstart.info',
                'search_url': 'https://robotstart.info/category/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'ledge_ai': {
                'base_url': 'https://ledge.ai',
                'search_url': 'https://ledge.ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'ainow': {
                'base_url': 'https://ainow.ai',
                'search_url': 'https://ainow.ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'aismiley': {
                'base_url': 'https://aismiley.co.jp',
                'search_url': 'https://aismiley.co.jp/ai_news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'codezine': {
                'base_url': 'https://codezine.jp',
                'search_url': 'https://codezine.jp/tag/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'publickey': {
                'base_url': 'https://www.publickey1.jp',
                'search_url': 'https://www.publickey1.jp/blog/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'gihyo': {
                'base_url': 'https://gihyo.jp',
                'search_url': 'https://gihyo.jp/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'atmarkit': {
                'base_url': 'https://atmarkit.itmedia.co.jp',
                'search_url': 'https://atmarkit.itmedia.co.jp/ait/subtop/features/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.inner p',
                'max_articles': 1
            },
            'techplus': {
                'base_url': 'https://news.mynavi.jp',
                'search_url': 'https://news.mynavi.jp/techplus/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            
            # 海外メジャーサイト
            'techcrunch': {
                'base_url': 'https://techcrunch.com',
                'search_url': 'https://techcrunch.com/category/artificial-intelligence/',
                'article_selector': 'h2 a',
                'content_selector': '.article-content p',
                'max_articles': 3
            },
            'venturebeat': {
                'base_url': 'https://venturebeat.com',
                'search_url': 'https://venturebeat.com/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-content p',
                'max_articles': 3
            },
            'arstechnica': {
                'base_url': 'https://arstechnica.com',
                'search_url': 'https://arstechnica.com/tag/artificial-intelligence/',
                'article_selector': 'h2 a',
                'content_selector': '.post-content p',
                'max_articles': 3
            },
            'theverge': {
                'base_url': 'https://www.theverge.com',
                'search_url': 'https://www.theverge.com/ai-artificial-intelligence',
                'article_selector': 'h2 a',
                'content_selector': '.duet--article--article-body p',
                'max_articles': 2
            },
            'wired': {
                'base_url': 'https://www.wired.com',
                'search_url': 'https://www.wired.com/tag/artificial-intelligence/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.post-content p',
                'max_articles': 2
            },
            'zdnet': {
                'base_url': 'https://www.zdnet.com',
                'search_url': 'https://www.zdnet.com/topic/artificial-intelligence/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'engadget': {
                'base_url': 'https://www.engadget.com',
                'search_url': 'https://www.engadget.com/tag/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.post-content p',
                'max_articles': 2
            },
            
            # AI専門サイト
            'ainews': {
                'base_url': 'https://www.artificialintelligence-news.com',
                'search_url': 'https://www.artificialintelligence-news.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'towards_data_science': {
                'base_url': 'https://towardsdatascience.com',
                'search_url': 'https://towardsdatascience.com/tagged/artificial-intelligence',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.section-content p',
                'max_articles': 2
            },
            'machine_learning_mastery': {
                'base_url': 'https://machinelearningmastery.com',
                'search_url': 'https://machinelearningmastery.com/blog/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            
            # ビジネス・ニュースサイト
            'reuters': {
                'base_url': 'https://www.reuters.com',
                'search_url': 'https://www.reuters.com/technology/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'bloomberg': {
                'base_url': 'https://www.bloomberg.com',
                'search_url': 'https://www.bloomberg.com/technology',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'cnbc': {
                'base_url': 'https://www.cnbc.com',
                'search_url': 'https://www.cnbc.com/technology/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.ArticleBody-articleBody p',
                'max_articles': 2
            },
            'cnn_business': {
                'base_url': 'https://www.cnn.com',
                'search_url': 'https://www.cnn.com/business/tech',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            
            # 学術・研究系
            'mit_tech_review': {
                'base_url': 'https://www.technologyreview.com',
                'search_url': 'https://www.technologyreview.com/topic/artificial-intelligence/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'nature': {
                'base_url': 'https://www.nature.com',
                'search_url': 'https://www.nature.com/subjects/machine-learning',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.article-body p',
                'max_articles': 1
            },
            'science_daily': {
                'base_url': 'https://www.sciencedaily.com',
                'search_url': 'https://www.sciencedaily.com/news/computers_math/artificial_intelligence/',
                'article_selector': 'h3 a, h2 a',
                'content_selector': '.article-text p',
                'max_articles': 2
            },
            
            # 開発者向け
            'dev_to': {
                'base_url': 'https://dev.to',
                'search_url': 'https://dev.to/t/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-body p',
                'max_articles': 2
            },
            'hackernews': {
                'base_url': 'https://news.ycombinator.com',
                'search_url': 'https://hn.algolia.com/?query=AI&type=story',
                'article_selector': 'a.storylink',
                'content_selector': '.comment p',
                'max_articles': 1
            },
            'medium': {
                'base_url': 'https://medium.com',
                'search_url': 'https://medium.com/tag/artificial-intelligence',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.section-content p',
                'max_articles': 2
            },
            
            # 企業ブログ
            'openai_blog': {
                'base_url': 'https://openai.com',
                'search_url': 'https://openai.com/blog/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-content p',
                'max_articles': 1
            },
            'google_ai': {
                'base_url': 'https://ai.googleblog.com',
                'search_url': 'https://ai.googleblog.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.post-body p',
                'max_articles': 1
            },
            'microsoft_ai': {
                'base_url': 'https://blogs.microsoft.com',
                'search_url': 'https://blogs.microsoft.com/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'anthropic_blog': {
                'base_url': 'https://www.anthropic.com',
                'search_url': 'https://www.anthropic.com/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.article-content p',
                'max_articles': 1
            },
            
                         # 追加の海外サイト
             'nextbigfuture': {
                'base_url': 'https://www.nextbigfuture.com',
                'search_url': 'https://www.nextbigfuture.com/category/artificial-intelligence',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'singularityhub': {
                'base_url': 'https://singularityhub.com',
                'search_url': 'https://singularityhub.com/topic/artificial-intelligence/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            
            # 専門分野別サイト
            'ai_research': {
                'base_url': 'https://www.ai-research.com',
                'search_url': 'https://www.ai-research.com/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'deeplearning_ai': {
                'base_url': 'https://www.deeplearning.ai',
                'search_url': 'https://www.deeplearning.ai/blog/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'ai_news_com': {
                'base_url': 'https://www.ai-news.com',
                'search_url': 'https://www.ai-news.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'ml_news': {
                'base_url': 'https://www.ml-news.com',
                'search_url': 'https://www.ml-news.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'robotics_business': {
                'base_url': 'https://www.roboticsbusinessreview.com',
                'search_url': 'https://www.roboticsbusinessreview.com/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'healthcare_ai': {
                'base_url': 'https://www.healthcareaimagazine.com',
                'search_url': 'https://www.healthcareaimagazine.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'fintech_ai': {
                'base_url': 'https://www.fintechmagazine.com',
                'search_url': 'https://www.fintechmagazine.com/ai',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            
            # 地域別サイト（アジア太平洋）
            'asia_tech': {
                'base_url': 'https://www.techinasia.com',
                'search_url': 'https://www.techinasia.com/topic/artificial-intelligence',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'kr_aitimes': {
                'base_url': 'https://www.aitimes.kr',
                'search_url': 'https://www.aitimes.kr/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'china_ai': {
                'base_url': 'https://www.chinaai.com',
                'search_url': 'https://www.chinaai.com/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'singapore_tech': {
                'base_url': 'https://www.sgtechreview.com',
                'search_url': 'https://www.sgtechreview.com/ai/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            
            # 地域別サイト（ヨーロッパ）
            'eu_ai_watch': {
                'base_url': 'https://www.ai-watch.eu',
                'search_url': 'https://www.ai-watch.eu/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            'uk_ai_news': {
                'base_url': 'https://www.ukainews.com',
                'search_url': 'https://www.ukainews.com/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'german_ai': {
                'base_url': 'https://www.ki-news.de',
                'search_url': 'https://www.ki-news.de/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 1
            },
            
            # スタートアップ・ベンチャー系
            'startup_ai': {
                'base_url': 'https://www.startupai.com',
                'search_url': 'https://www.startupai.com/news',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
                'max_articles': 2
            },
            'vc_ai': {
                'base_url': 'https://www.vcai.news',
                'search_url': 'https://www.vcai.news/',
                'article_selector': 'h2 a, h3 a',
                'content_selector': '.entry-content p',
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