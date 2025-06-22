#!/usr/bin/env python3
"""
日次AI記事投稿システム
実際の記事を収集・処理・投稿する本番用スクリプト
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional
from integrated_collector import IntegratedAICollector
from article_processor import ArticleProcessor
from wordpress_connector import WordPressConnector, DailyPostGenerator

class DailyAIPublisher:
    """日次AI記事投稿システム"""
    
    def __init__(self):
        self.collector = IntegratedAICollector()
        self.processor = ArticleProcessor()
        self.wp_connector = WordPressConnector()
        self.post_generator = DailyPostGenerator(self.wp_connector)
    
    async def run_daily_publication(self, min_articles: int = 3, max_articles: int = 8) -> Optional[dict]:
        """日次投稿の完全実行"""
        
        print("=" * 60)
        print("🤖 AI記事日次投稿システム開始")
        print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Step 1: WordPress接続テスト
            print("\n🔗 Step 1: WordPress接続テスト")
            if not self.wp_connector.test_connection():
                print("❌ WordPress接続に失敗しました")
                return None
            print("✅ WordPress接続成功")
            
            # Step 2: 記事収集（24時間以内）
            print(f"\n📰 Step 2: AI記事収集（24時間以内）")
            articles = await self.collector.collect_all_sources()
            
            if len(articles) < min_articles:
                print(f"❌ 収集記事数が不足しています（{len(articles)}件 < {min_articles}件）")
                return None
            
            # 最大記事数まで制限
            if len(articles) > max_articles:
                articles = articles[:max_articles]
                print(f"📊 記事数を{max_articles}件に制限しました")
            
            print(f"✅ {len(articles)}件の記事を収集しました")
            
            # Step 3: 記事処理（要約・感想生成）
            print(f"\n🔄 Step 3: 記事処理（要約・感想生成）")
            processed_articles = self.processor.process_articles_batch(articles)
            
            if not processed_articles:
                print("❌ 記事処理に失敗しました")
                return None
            
            print(f"✅ {len(processed_articles)}件の記事処理完了")
            
            # Step 4: 投稿コンテンツ生成
            print(f"\n📝 Step 4: 投稿コンテンツ生成")
            post_content = self.post_generator.generate_daily_post_content(processed_articles)
            
            print(f"✅ 投稿コンテンツ生成完了")
            print(f"   タイトル: {post_content['title']}")
            print(f"   記事数: {post_content['articles_count']}件")
            
            # Step 5: WordPress投稿
            print(f"\n🚀 Step 5: WordPress投稿")
            
            # 最終確認を表示
            print("\n📋 投稿内容プレビュー:")
            print(f"   タイトル: {post_content['title']}")
            print(f"   抜粋: {post_content['excerpt']}")
            print(f"   記事数: {len(processed_articles)}件")
            print("   含まれる記事:")
            for i, pa in enumerate(processed_articles, 1):
                print(f"     {i}. {pa.original_article.title[:50]}...")
            
            # WordPress投稿実行
            post_info = self.wp_connector.create_post(
                title=post_content['title'],
                content=post_content['content'],
                excerpt=post_content['excerpt'],
                tags=["AI", "技術動向", "まとめ", "最新情報", "日次更新"]
            )
            
            if post_info:
                print(f"✅ WordPress投稿成功!")
                print(f"   投稿URL: {post_info['link']}")
                print(f"   投稿ID: {post_info['id']}")
                
                # 詳細ログを保存
                result = self.save_publication_log(post_info, processed_articles, post_content)
                
                print("\n🎉 日次投稿が正常に完了しました!")
                return result
            else:
                print("❌ WordPress投稿に失敗しました")
                return None
                
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_publication_log(self, post_info: dict, processed_articles: List, post_content: dict) -> dict:
        """投稿ログを詳細に保存"""
        timestamp = datetime.now()
        
        log_data = {
            'publication_date': timestamp.isoformat(),
            'wordpress_post': {
                'id': post_info['id'],
                'url': post_info['link'],
                'title': post_content['title'],
                'status': post_info.get('status', 'unknown')
            },
            'articles_summary': {
                'total_count': len(processed_articles),
                'sources': {}
            },
            'collected_articles': []
        }
        
        # ソース別集計
        for pa in processed_articles:
            source = pa.original_article.source
            if source not in log_data['articles_summary']['sources']:
                log_data['articles_summary']['sources'][source] = 0
            log_data['articles_summary']['sources'][source] += 1
            
            # 個別記事情報
            log_data['collected_articles'].append({
                'title': pa.original_article.title,
                'url': pa.original_article.url,
                'source': pa.original_article.source,
                'published_date': pa.original_article.published_date,
                'summary_length': len(pa.summary),
                'comment_length': len(pa.user_value_comment)
            })
        
        # ログファイル保存
        log_filename = f"daily_publication_log_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 詳細ログを {log_filename} に保存しました")
        return log_data
    
    async def test_run(self) -> bool:
        """テスト実行（投稿はしない）"""
        print("🧪 テストモード: 投稿は行いません")
        
        try:
            # 記事収集テスト
            articles = await self.collector.collect_all_sources()
            print(f"✅ 記事収集テスト: {len(articles)}件")
            
            if articles:
                # 記事処理テスト（1件のみ）
                processed = self.processor.process_articles_batch(articles[:1])
                print(f"✅ 記事処理テスト: {len(processed)}件")
                
                if processed:
                    # 投稿コンテンツ生成テスト
                    content = self.post_generator.generate_daily_post_content(processed)
                    print(f"✅ コンテンツ生成テスト: {content['title']}")
                    
                    print("\n📋 テスト結果:")
                    print(f"   タイトル: {content['title']}")
                    print(f"   抜粋: {content['excerpt']}")
                    print(f"   コンテンツ長: {len(content['content'])}文字")
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ テスト中にエラー: {e}")
            return False

async def main():
    """メイン実行"""
    import sys
    
    publisher = DailyAIPublisher()
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # テストモード
        success = await publisher.test_run()
        if success:
            print("\n✅ テスト完了: システムは正常に動作しています")
        else:
            print("\n❌ テスト失敗: システムに問題があります")
    else:
        # 本番実行
        result = await publisher.run_daily_publication()
        if result:
            print(f"\n✅ 日次投稿完了: {result['wordpress_post']['url']}")
        else:
            print("\n❌ 日次投稿失敗")

if __name__ == "__main__":
    asyncio.run(main()) 