#!/usr/bin/env python3
"""
AI情報収集・投稿メインスクリプト
1日1記事で複数の高品質なAI記事をまとめて投稿
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List
from integrated_collector import IntegratedAICollector
from article_processor import ArticleProcessor
from wordpress_connector import WordPressConnector, DailyPostGenerator

class AINewsSystem:
    """AI情報収集・投稿システム"""
    
    def __init__(self):
        self.collector = IntegratedAICollector()
        self.processor = ArticleProcessor()
        self.wp_connector = WordPressConnector()
        self.post_generator = DailyPostGenerator(self.wp_connector)
        self.articles_per_post = 8  # 1記事に含めるニュース数
        self.max_posts_per_day = 1  # 1日1記事
        
    def load_today_posts_count(self) -> int:
        """今日の投稿数を取得"""
        today = datetime.now().strftime('%Y-%m-%d')
        count_file = f"daily_posts_{today}.json"
        
        if os.path.exists(count_file):
            with open(count_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('count', 0)
        return 0
    
    def save_today_posts_count(self, count: int):
        """今日の投稿数を保存"""
        today = datetime.now().strftime('%Y-%m-%d')
        count_file = f"daily_posts_{today}.json"
        
        data = {
            'date': today,
            'count': count,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(count_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def select_best_articles(self, articles: List, max_count: int = 8) -> List:
        """最高品質の記事を選択"""
        if len(articles) <= max_count:
            return articles
            
        # 記事の品質スコアを計算
        scored_articles = []
        
        for article in articles:
            score = 0
            
            # タイトルの品質（長さと内容）
            title_len = len(article.title)
            if 20 <= title_len <= 80:
                score += 2
            elif title_len > 80:
                score += 1
            
            # 本文の品質（長さ）
            content_len = len(article.content)
            if content_len > 500:
                score += 3
            elif content_len > 300:
                score += 2
            elif content_len > 150:
                score += 1
            
            # 重要キーワードの存在
            important_keywords = [
                'ChatGPT', 'OpenAI', 'Google', 'Meta', 'Apple', 
                'Claude', 'Anthropic', 'Gemini', '生成AI', 'LLM',
                '機械学習', 'ディープラーニング', '人工知能'
            ]
            
            title_content = (article.title + ' ' + article.content[:200]).lower()
            keyword_count = sum(1 for keyword in important_keywords 
                              if keyword.lower() in title_content)
            score += keyword_count
            
            # ソースの信頼性
            trusted_sources = ['itmedia', 'gigazine', 'techcrunch', 'wired', 'theverge', 'arstechnica', 'venturebeat']
            if hasattr(article, 'source') and article.source.lower() in trusted_sources:
                score += 2
            
            scored_articles.append((score, article))
        
        # スコア順にソートして上位を選択
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles[:max_count]]

    async def run_daily_collection(self):
        """1日の記事収集・投稿を実行"""
        print("=== AI情報収集・投稿システム開始 ===")
        
        # 今日の投稿数をチェック
        today_count = self.load_today_posts_count()
        
        if today_count >= self.max_posts_per_day:
            print(f"今日の投稿はすでに完了しています（{today_count}/{self.max_posts_per_day}件）。")
            return
        
        print(f"今日の投稿数: {today_count}/{self.max_posts_per_day}")
        print(f"今日のまとめ記事を作成します（目標: {self.articles_per_post}件のニュース）")
        
        try:
            # 記事を収集
            print("\n🚀 高度統合記事収集開始")
            articles = await self.collector.collect_all_articles()
            
            if not articles:
                print("収集できた記事がありません。")
                return
            
            print(f"✅ {len(articles)}件の記事を収集しました")
            
            # 最高品質の記事を選択
            best_articles = self.select_best_articles(articles, self.articles_per_post)
            print(f"=== {len(best_articles)}件の記事処理開始 ===")
            
            if len(best_articles) < 3:
                print("十分な記事数が確保できませんでした。最低3件必要です。")
                return
            
            # 各記事を処理（要約・感想生成）
            processed_articles = []
            
            for i, article in enumerate(best_articles, 1):
                try:
                    print(f"\n[{i}/{len(best_articles)}] 処理中...")
                    print(f"記事処理中: {article.title}")
                    
                    # 記事を処理（要約・感想生成）
                    processed = self.processor.process_article(article)
                    
                    if processed:
                        processed_articles.append(processed)
                        print("✅ 処理完了")
                    else:
                        print("❌ 処理失敗")
                        
                except Exception as e:
                    print(f"❌ 記事処理エラー: {e}")
                    continue
            
            print(f"\n=== 処理完了: {len(processed_articles)}/{len(best_articles)}件成功 ===")
            
            if len(processed_articles) < 3:
                print("処理済み記事が不足しています。最低3件必要です。")
                return
            
            print(f"✅ {len(processed_articles)}件の記事を処理しました")
            
            # WordPress投稿
            print("\n--- WordPress投稿開始 ---")
            post_info = self.post_generator.publish_daily_post(processed_articles)
            
            if post_info:
                print("✅ WordPressに投稿完了")
                print(f"   投稿ID: {post_info['id']}")
                print(f"   投稿URL: {post_info['link']}")
                
                # 投稿数を更新
                self.save_today_posts_count(today_count + 1)
                print("=== システム実行完了 ===")
            else:
                print("❌ WordPress投稿に失敗しました")
                
        except Exception as e:
            print(f"❌ システムエラー: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """メイン関数"""
    system = AINewsSystem()
    await system.run_daily_collection()

if __name__ == "__main__":
    asyncio.run(main()) 