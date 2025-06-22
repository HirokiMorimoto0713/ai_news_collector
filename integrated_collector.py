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

class IntegratedAICollector:
    """統合AI情報収集クラス"""
    
    def __init__(self, config_file: str = "collector_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.news_collector = AINewsCollector()
        self.all_articles = []
    
    def load_config(self) -> Dict:
        """設定を読み込み"""
        default_config = {
            "max_articles_per_day": 5,
            "sources": {
                "twitter": {
                    "enabled": True,
                    "use_api": False,  # デフォルトはAPI使用しない（リスク回避）
                    "max_articles": 2
                },
                "news_sites": {
                    "enabled": True,
                    "max_articles": 2
                },
                "tech_blogs": {
                    "enabled": True,
                    "max_articles": 1
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
    
    async def collect_all_sources(self) -> List[NewsArticle]:
        """全ソースから情報を収集"""
        all_articles = []
        
        print("=== AI情報収集開始 ===")
        
        # X/Twitter収集
        if self.config["sources"]["twitter"]["enabled"]:
            try:
                min_likes = self.config["sources"]["twitter"].get("min_likes", 30)
                max_articles = self.config["sources"]["twitter"].get("max_articles", 10)
                twitter_articles = await collect_twitter_articles(
                    use_api=self.config["sources"]["twitter"]["use_api"],
                    min_likes=min_likes,
                    max_articles=max_articles
                )
                # フィルタリングを緩和（テスト用）
                filtered_twitter = twitter_articles  # フィルタリングを一時的に無効化
                all_articles.extend(filtered_twitter)
                print(f"X/Twitter: {len(filtered_twitter)} 件収集")
            except Exception as e:
                print(f"X/Twitter収集エラー: {e}")
        
        # ニュースサイト収集
        if self.config["sources"]["news_sites"]["enabled"]:
            try:
                news_articles = self.news_collector.collect_from_news_sites()
                filtered_news = [a for a in news_articles if self.filter_article(a)]
                max_news = self.config["sources"]["news_sites"]["max_articles"]
                all_articles.extend(filtered_news[:max_news])
                print(f"ニュースサイト: {len(filtered_news[:max_news])} 件収集")
            except Exception as e:
                print(f"ニュースサイト収集エラー: {e}")
        
        # 技術ブログ収集
        if self.config["sources"]["tech_blogs"]["enabled"]:
            try:
                blog_articles = self.news_collector.collect_from_tech_blogs()
                filtered_blogs = [a for a in blog_articles if self.filter_article(a)]
                max_blogs = self.config["sources"]["tech_blogs"]["max_articles"]
                all_articles.extend(filtered_blogs[:max_blogs])
                print(f"技術ブログ: {len(filtered_blogs[:max_blogs])} 件収集")
            except Exception as e:
                print(f"技術ブログ収集エラー: {e}")
        
        # 重複除去
        unique_articles = self.remove_duplicates(all_articles)
        
        # 最大件数まで制限
        max_total = self.config["max_articles_per_day"]
        final_articles = unique_articles[:max_total]
        
        self.all_articles = final_articles
        print(f"=== 収集完了: 合計 {len(final_articles)} 件 ===")
        
        return final_articles
    
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
        
        print(f"収集記事を {filename} に保存しました")
        return filename
    
    def get_collection_summary(self) -> Dict:
        """収集結果のサマリーを取得"""
        if not self.all_articles:
            return {"total": 0, "by_source": {}}
        
        summary = {
            "total": len(self.all_articles),
            "by_source": {},
            "collection_time": datetime.now().isoformat()
        }
        
        for article in self.all_articles:
            source = article.source
            if source not in summary["by_source"]:
                summary["by_source"][source] = 0
            summary["by_source"][source] += 1
        
        return summary

async def main():
    """メイン実行関数"""
    collector = IntegratedAICollector()
    
    # 情報収集実行
    articles = await collector.collect_all_sources()
    
    # 結果保存
    filename = collector.save_collected_articles()
    
    # サマリー表示
    summary = collector.get_collection_summary()
    print("\n=== 収集サマリー ===")
    print(f"総記事数: {summary['total']}")
    print("ソース別:")
    for source, count in summary["by_source"].items():
        print(f"  {source}: {count}件")
    
    # 記事一覧表示
    print("\n=== 収集記事一覧 ===")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   ソース: {article.source}")
        print(f"   URL: {article.url}")
        print(f"   内容: {article.content[:100]}...")
        print()
    
    return articles, filename

if __name__ == "__main__":
    asyncio.run(main())

