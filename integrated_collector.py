"""
統合AI情報収集システム
各種ソースからAI関連情報を収集し、統合管理
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict
from news_collector import AINewsCollector, NewsArticle
from twitter_collector import collect_twitter_articles
from simple_scraper import SimpleScraper, SimpleArticle

class IntegratedAICollector:
    """統合AI情報収集クラス"""
    
    def __init__(self, config_file: str = "collector_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.news_collector = AINewsCollector()
        self.simple_scraper = SimpleScraper()
        self.all_articles = []
    
    def load_config(self) -> Dict:
        """設定を読み込み"""
        default_config = {
            "max_articles_per_day": 10,
            "sources": {
                "twitter": {
                    "enabled": False,
                    "use_api": False,
                    "max_articles": 0
                },
                "news_sites": {
                    "enabled": True,
                    "max_articles": 10
                },
                "tech_blogs": {
                    "enabled": True,
                    "max_articles": 5
                },
                "simple_scraper": {
                    "enabled": True,
                    "max_articles": 5
                }
            },
            "filters": {
                "min_content_length": 100,
                "exclude_keywords": ["広告", "PR", "スポンサー"],
                "required_keywords": ["AI", "人工知能", "機械学習", "ChatGPT", "LLM", "技術"]
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # デフォルト設定とマージ
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config

    def simple_article_to_news_article(self, simple_article: SimpleArticle) -> NewsArticle:
        """SimpleArticleをNewsArticleに変換"""
        published_date = simple_article.published_date
        if published_date is None:
            published_date = datetime.now().isoformat()
        
        return NewsArticle(
            title=simple_article.title,
            url=simple_article.url,
            content=simple_article.content,
            source=simple_article.source,
            published_date=published_date
        )
    
    def filter_article(self, article: NewsArticle) -> bool:
        """記事のフィルタリング"""
        filters = self.config["filters"]
        
        # 最小文字数チェック
        if len(article.content) < filters["min_content_length"]:
            return False
        
        # 除外キーワードチェック
        content_lower = article.content.lower()
        title_lower = article.title.lower()
        
        for exclude_word in filters["exclude_keywords"]:
            if exclude_word in content_lower or exclude_word in title_lower:
                return False
        
        # 必須キーワードチェック
        has_required_keyword = False
        for required_word in filters["required_keywords"]:
            if required_word.lower() in content_lower or required_word.lower() in title_lower:
                has_required_keyword = True
                break
        
        return has_required_keyword
    
    def filter_by_time(self, articles: List[NewsArticle], hours: int = 24) -> List[NewsArticle]:
        """指定時間以内の記事のみをフィルタリング"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        time_limit = now - timedelta(hours=hours)
        filtered_articles = []
        
        for article in articles:
            # published_dateが設定されている場合のみ時間フィルタを適用
            if article.published_date:
                try:
                    # ISO形式の日時をパース
                    published_time = datetime.fromisoformat(article.published_date.replace('Z', '+00:00'))
                    # タイムゾーンを除去して比較
                    published_time = published_time.replace(tzinfo=None)
                    
                    if published_time >= time_limit:
                        filtered_articles.append(article)
                    else:
                        print(f"古い記事をスキップ: {article.title} ({article.published_date})")
                except Exception as e:
                    print(f"日時解析エラー ({article.title}): {e}")
                    # 日時が解析できない場合は含める（安全側に倒す）
                    filtered_articles.append(article)
            else:
                # 公開日時が不明な場合は含める（安全側に倒す）
                filtered_articles.append(article)
        
        return filtered_articles
    
    async def collect_x_related_information(self, max_posts: int = 3) -> List[NewsArticle]:
        """X関連情報を収集（APIを使用しない方式）"""
        try:
            from simple_x_collector import collect_simple_x_posts
            
            print("📱 X関連情報収集開始...")
            articles = await collect_simple_x_posts(max_posts=max_posts)
            print(f"   ✅ X関連情報: {len(articles)}件取得")
            return articles
            
        except Exception as e:
            print(f"   ❌ X関連情報収集エラー: {e}")
            return []
    
    async def collect_all_articles(self) -> List[NewsArticle]:
        """全ソースから記事を収集"""
        all_articles = []
        
        print("🚀 統合記事収集開始")
        
        # 既存のニュース収集
        try:
            collector = AINewsCollector()
            regular_articles = collector.collect_daily_articles()
            all_articles.extend(regular_articles)
            print(f"📰 通常ニュース: {len(regular_articles)}件")
        except Exception as e:
            print(f"❌ 通常ニュース収集エラー: {e}")
        
        # X関連情報収集を追加
        try:
            x_articles = await self.collect_x_related_information(max_posts=3)
            all_articles.extend(x_articles)
            print(f"📱 X関連情報: {len(x_articles)}件")
        except Exception as e:
            print(f"❌ X関連情報収集エラー: {e}")
        
        print(f"📊 総合計: {len(all_articles)}件の記事を収集")
        return all_articles
    
    def remove_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """重複記事を除去"""
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            if article.hash_id not in seen_hashes:
                seen_hashes.add(article.hash_id)
                unique_articles.append(article)
        
        return unique_articles
    
    def save_collected_articles(self, filename: str = None):
        """収集した記事を保存"""
        if not filename:
            filename = f"daily_ai_news_{datetime.now().strftime('%Y%m%d')}.json"
        
        articles_data = []
        for article in self.all_articles:
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
    
    def get_collection_summary(self) -> Dict:
        """収集サマリーを取得"""
        source_counts = {}
        for article in self.all_articles:
            source = article.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'total_articles': len(self.all_articles),
            'source_breakdown': source_counts,
            'collection_time': datetime.now().isoformat(),
            'config_used': self.config
        }

async def main():
    """メイン実行関数"""
    collector = IntegratedAICollector()
    
    print("統合AI情報収集システム開始")
    articles = await collector.collect_all_articles()
    
    if articles:
        collector.save_collected_articles()
        summary = collector.get_collection_summary()
        
        print("\n=== 収集サマリー ===")
        print(f"総記事数: {summary['total_articles']}")
        print("ソース別内訳:")
        for source, count in summary['source_breakdown'].items():
            print(f"  {source}: {count}件")
        
        print("\n=== 収集記事一覧 ===")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   ソース: {article.source}")
            print(f"   URL: {article.url}")
            print()
    else:
        print("記事が収集されませんでした")

async def collect_all_ai_news():
    """すべてのソースからAIニュースを収集"""
    all_articles = []
    
    print("🚀 統合AIニュース収集開始")
    print("=" * 60)
    
    # 1. 通常のニュース収集
    try:
        print("\n📰 通常ニュース収集中...")
        from news_collector import collect_news
        news_articles = await collect_news()
        all_articles.extend(news_articles)
        print(f"✅ 通常ニュース: {len(news_articles)}件")
    except Exception as e:
        print(f"❌ 通常ニュース収集エラー: {e}")
    
    # 2. Simple X Collector（安定版）
    try:
        print("\n🐦 X関連情報収集中...")
        from simple_x_collector import collect_x_related_info
        x_articles = await collect_x_related_info()
        all_articles.extend(x_articles)
        print(f"✅ X関連情報: {len(x_articles)}件")
    except Exception as e:
        print(f"❌ X関連情報収集エラー: {e}")
    
    # X投稿収集機能は一旦保留
    # TODO: 実際のX投稿収集機能の実装を検討中
    # 現在の代替手段は要求に合わないため保留
    
    # # 3. 直接X投稿スクレイピング（実験版）- 保留中
    # try:
    #     print("\n🔍 直接X投稿スクレイピング中...")
    #     from direct_x_scraper import collect_direct_x_posts
    #     direct_x_articles = await collect_direct_x_posts(max_posts=3)
    #     if direct_x_articles:
    #         all_articles.extend(direct_x_articles)
    #         print(f"✅ 直接X投稿: {len(direct_x_articles)}件")
    #     else:
    #         print("⚠️ 直接X投稿: 0件 (フォールバック済み)")
    # except Exception as e:
    #     print(f"❌ 直接X投稿スクレイピングエラー: {e}")
    
    # # 4. Real X Scraper（代替手段）- 保留中
    # try:
    #     print("\n📱 代替X投稿収集中...")
    #     from real_x_scraper import collect_real_x_posts
    #     real_x_articles = await collect_real_x_posts(max_posts=3)
    #     all_articles.extend(real_x_articles)
    #     print(f"✅ 代替X投稿: {len(real_x_articles)}件")
    # except Exception as e:
    #     print(f"❌ 代替X投稿収集エラー: {e}")
    
    # 重複除去
    unique_articles = []
    seen_titles = set()
    for article in all_articles:
        title_key = article.title[:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    print(f"\n📊 統合収集結果:")
    print(f"   総収集数: {len(all_articles)}件")
    print(f"   重複除去後: {len(unique_articles)}件")
    print(f"   ※X投稿収集機能は現在保留中です")
    
    # ソース別統計
    source_stats = {}
    for article in unique_articles:
        source = article.source
        source_stats[source] = source_stats.get(source, 0) + 1
    
    print(f"\n📈 ソース別統計:")
    for source, count in source_stats.items():
        print(f"   {source}: {count}件")
    
    return unique_articles

if __name__ == "__main__":
    asyncio.run(main())

