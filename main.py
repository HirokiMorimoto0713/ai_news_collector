#!/usr/bin/env python3
"""
AI情報収集・投稿メインスクリプト
1日1記事で5つの高品質なAI記事をまとめて投稿
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List
from integrated_collector import IntegratedAICollector
from article_processor import ArticleProcessor, BlogPostGenerator
from wordpress_connector import WordPressConnector

class AINewsSystem:
    """AI情報収集・投稿システム（1日1記事まとめ版）"""
    
    def __init__(self):
        self.collector = IntegratedAICollector()
        self.processor = ArticleProcessor()
        self.blog_generator = BlogPostGenerator()
        self.wp_connector = WordPressConnector()
        self.articles_per_post = 5  # 1記事に含めるニュース数
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
    
    def select_best_articles(self, articles: List, max_count: int = 5) -> List:
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
    
    def extract_image_from_article(self, article) -> str:
        """記事から画像を抽出、またはニュースサイトのロゴを返す"""
        import re
        
        print(f"画像抽出開始: {article.title[:50]}...")
        
        # 1. 記事本文から画像を検索
        img_patterns = [
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+src=([^\s>]+)[^>]*>',
            r'https://[^\s"\'<>]+\.(jpg|jpeg|png|gif|webp)',
        ]
        
        for i, pattern in enumerate(img_patterns, 1):
            matches = re.findall(pattern, article.content, re.IGNORECASE)
            if matches:
                img_url = matches[0] if isinstance(matches[0], str) else matches[0][0]
                # 相対URLの場合は絶対URLに変換
                if img_url.startswith('/'):
                    from urllib.parse import urljoin, urlparse
                    base_url = f"{urlparse(article.url).scheme}://{urlparse(article.url).netloc}"
                    img_url = urljoin(base_url, img_url)
                print(f"  記事内画像発見 (パターン{i}): {img_url}")
                return img_url
        
        print("  記事内に画像が見つかりませんでした")
        
        # 2. ニュースサイトのロゴを使用
        source = getattr(article, 'source', '').lower()
        
        # URLからサイト名を推定する関数
        def get_site_from_url(url):
            if not url:
                return ''
            url = url.lower()
            
            # 日本語サイト
            if 'itmedia' in url:
                return 'itmedia'
            elif 'gigazine' in url:
                return 'gigazine'
            elif 'pc.watch.impress' in url or 'impress' in url:
                return 'impress_watch'
            elif 'ascii.jp' in url:
                return 'ascii'
            elif 'mynavi' in url:
                return 'mynavi'
            elif 'xtech.nikkei' in url:
                return 'nikkei_xtech'
            
            # 海外メジャーサイト
            elif 'techcrunch' in url:
                return 'techcrunch'
            elif 'venturebeat' in url:
                return 'venturebeat'
            elif 'arstechnica' in url:
                return 'arstechnica'
            elif 'theverge' in url:
                return 'theverge'
            elif 'wired' in url:
                return 'wired'
            elif 'zdnet' in url:
                return 'zdnet'
            elif 'engadget' in url:
                return 'engadget'
            
            # AI専門サイト
            elif 'artificialintelligence-news' in url:
                return 'ainews'
            elif 'towardsdatascience' in url:
                return 'towards_data_science'
            elif 'machinelearningmastery' in url:
                return 'machine_learning_mastery'
            
            # ビジネス・ニュースサイト
            elif 'reuters' in url:
                return 'reuters'
            elif 'bloomberg' in url:
                return 'bloomberg'
            elif 'cnbc' in url:
                return 'cnbc'
            elif 'cnn' in url:
                return 'cnn_business'
            
            # 学術・研究系
            elif 'technologyreview' in url:
                return 'mit_tech_review'
            elif 'nature.com' in url:
                return 'nature'
            elif 'sciencedaily' in url:
                return 'science_daily'
            
            # 開発者向け
            elif 'dev.to' in url:
                return 'dev_to'
            elif 'news.ycombinator' in url:
                return 'hackernews'
            elif 'medium.com' in url:
                return 'medium'
            
            # 企業ブログ
            elif 'openai.com' in url:
                return 'openai_blog'
            elif 'ai.googleblog' in url:
                return 'google_ai'
            elif 'blogs.microsoft' in url:
                return 'microsoft_ai'
            elif 'anthropic.com' in url:
                return 'anthropic_blog'
            
            # 追加の海外サイト
            elif 'nextbigfuture' in url:
                return 'nextbigfuture'
            elif 'singularityhub' in url:
                return 'singularityhub'
            
            # その他
            elif 'nikkei' in url:
                return 'nikkei'
            elif 'yahoo' in url:
                return 'yahoo'
            elif 'google' in url:
                return 'google'
            elif 'bbc' in url:
                return 'bbc'
            
            return ''
        
        # sourceが空の場合はURLから推定
        if not source:
            source = get_site_from_url(getattr(article, 'url', ''))
        
        site_logos = {
            # 日本語サイト
            'itmedia': 'https://image.itmedia.co.jp/images/common/logo_itmedia.gif',
            'gigazine': 'https://gigazine.net/giga.png',
            'impress_watch': 'https://pc.watch.impress.co.jp/img/pcw/head/logo.png',
            'ascii': 'https://ascii.jp/img/2017/logo.svg',
            'mynavi': 'https://news.mynavi.jp/image/logo_mynavi_news.png',
            'nikkei_xtech': 'https://xtech.nikkei.com/favicon.ico',
            
            # 海外メジャーサイト
            'techcrunch': 'https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png',
            'venturebeat': 'https://venturebeat.com/wp-content/themes/vb-news/img/logos/VB_Logo_Dark.svg',
            'arstechnica': 'https://cdn.arstechnica.net/wp-content/uploads/2016/10/cropped-ars-logo-512_480-32x32.png',
            'theverge': 'https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395359/android-chrome-192x192.0.png',
            'wired': 'https://www.wired.com/verso/static/wired/assets/logo-wired.svg',
            'zdnet': 'https://www.zdnet.com/a/img/resize/logo-zdnet.png',
            'engadget': 'https://s.blogcdn.com/www.engadget.com/media/2013/07/favicon-192.png',
            
            # AI専門サイト
            'ainews': 'https://www.artificialintelligence-news.com/favicon.ico',
            'towards_data_science': 'https://miro.medium.com/v2/resize:fill:152:152/1*sHhtYhaCe2Uc3IU0IgKwIQ.png',
            'machine_learning_mastery': 'https://machinelearningmastery.com/favicon.ico',
            
            # ビジネス・ニュースサイト
            'reuters': 'https://www.reuters.com/pf/resources/images/reuters/reuters-logo.svg',
            'bloomberg': 'https://assets.bwbx.io/s3/javelin/public/javelin/images/favicon-black-63fe5249d3.png',
            'cnbc': 'https://www.cnbc.com/a/img/redesign/cnbc_logo.svg',
            'cnn_business': 'https://cdn.cnn.com/cnn/.e/img/3.0/global/misc/cnn-logo.png',
            
            # 学術・研究系
            'mit_tech_review': 'https://www.technologyreview.com/favicon.ico',
            'nature': 'https://www.nature.com/static/images/favicons/nature/apple-touch-icon.png',
            'science_daily': 'https://www.sciencedaily.com/favicon.ico',
            
            # 開発者向け
            'dev_to': 'https://dev.to/favicon.ico',
            'hackernews': 'https://news.ycombinator.com/favicon.ico',
            'medium': 'https://miro.medium.com/v2/resize:fill:152:152/1*sHhtYhaCe2Uc3IU0IgKwIQ.png',
            
            # 企業ブログ
            'openai_blog': 'https://openai.com/favicon.ico',
            'google_ai': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
            'microsoft_ai': 'https://c.s-microsoft.com/favicon.ico',
            'anthropic_blog': 'https://www.anthropic.com/favicon.ico',
            
            # 追加の海外サイト
            'nextbigfuture': 'https://www.nextbigfuture.com/favicon.ico',
            'singularityhub': 'https://singularityhub.com/favicon.ico',
            
            # その他
            'nikkei': 'https://www.nikkei.com/favicon.ico',
            'yahoo': 'https://s.yimg.com/rz/p/yahoo_frontpage_en-US_s_f_p_205x58_frontpage.png',
            'google': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
            'bbc': 'https://static.files.bbci.co.uk/ws/simorgh-assets/public/news/images/metadata/poster-1024x576.png'
        }
        
        if source in site_logos:
            selected_logo = site_logos[source]
            print(f"  ニュースサイトロゴ選択: {selected_logo}")
            print(f"  ソース: {source}")
            return selected_logo
        
        # 3. フォールバック：汎用的なニュースアイコン
        fallback_images = [
            'https://dummyimage.com/400x200/007CBA/FFFFFF&text=NEWS',
            'https://dummyimage.com/400x200/28A745/FFFFFF&text=TECH+NEWS',
            'https://dummyimage.com/400x200/DC3545/FFFFFF&text=AI+NEWS',
        ]
        
        import hashlib
        hash_value = int(hashlib.md5(article.title.encode()).hexdigest(), 16)
        selected_image = fallback_images[hash_value % len(fallback_images)]
        
        print(f"  フォールバック画像選択: {selected_image}")
        print(f"  ソース: {source}")
        
        return selected_image
    
    def create_consolidated_blog_post(self, processed_articles: List) -> dict:
        """統合ブログ投稿を作成（改良版：プレビュー・翻訳対応）"""
        today = datetime.now()
        
        # タイトル生成
        title = f"今日のAIニュース {len(processed_articles)}選 - {today.strftime('%Y年%m月%d日')}"
        
        # 導入文
        intro = f"""こんにちは！今日も最新のAI情報をお届けします！

本日は{len(processed_articles)}件の注目すべきAIニュースをピックアップしました。それぞれのニュースについて、要約と私たちへの影響を分析してお伝えします。

"""
        
        # 各記事セクションを作成
        content_sections = []
        for i, processed in enumerate(processed_articles, 1):
            article = processed.original_article
            
            # 翻訳されたタイトルがある場合は使用
            display_title = getattr(processed, 'translated_title', '') or article.title
            
            # プレビューテキスト
            preview_text = getattr(processed, 'content_preview', '') or article.content[:200] + "..."
            
            # 画像URL取得（改良版）
            img_url = self.extract_image_from_article(article)
            print(f"記事{i}の画像URL: {img_url}")
            
            # 画像HTMLを改良（ニュースサイトロゴ対応）
            source_name = getattr(article, 'source', 'Unknown').title()
            image_html = f'''<div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e0e0e0;">
<img src="{img_url}" alt="{source_name}ロゴ" style="max-height: 120px; width: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
     onerror="
     if (this.src !== 'https://dummyimage.com/400x200/007CBA/FFFFFF&text=NEWS') {{
         this.src='https://dummyimage.com/400x200/007CBA/FFFFFF&text=NEWS';
     }} else {{
         this.style.display='none';
         this.nextElementSibling.innerHTML='ロゴを読み込めませんでした';
     }}
     ">
<p style="font-size: 12px; color: #666; margin-top: 8px; font-style: italic;">ソース: {source_name}</p>
</div>'''
            
            section = f"""<h2>📰 {i}. {display_title}</h2>

<blockquote style="background-color: #f8f9fa; border-left: 4px solid #007cba; padding: 15px; margin: 20px 0; border-radius: 5px;">
<p><strong>ソース:</strong> {getattr(article, 'source', 'Unknown')}</p>
<p><strong>元タイトル:</strong> {article.title if display_title != article.title else '（上記と同じ）'}</p>
<p><a href="{article.url}" target="_blank" rel="noopener" style="color: #007cba; text-decoration: none; font-weight: bold;">📖 元記事を読む →</a></p>
</blockquote>

{image_html}

<div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h4>🔍 記事プレビュー</h4>
<p style="font-style: italic; color: #555; line-height: 1.6;">{preview_text}</p>
</div>

<h3>📝 記事の要約</h3>
<p>{processed.summary}</p>

<h3>💡 私たちへの影響と今後の展望</h3>
<p>{processed.user_value_comment}</p>

<hr style="margin: 30px 0; border: none; border-top: 2px solid #e0e0e0;">

"""
            content_sections.append(section)
        
        # まとめ文
        outro = f"""<h2>🎯 今日のまとめ</h2>

<p>いかがでしたでしょうか？今日も様々なAI技術の進歩が見られましたね！</p>

<p>これらの技術動向は、私たちの日常生活や仕事に大きな変化をもたらす可能性があります。ぜひこの情報を参考に、AI技術を積極的に活用していってください。</p>

<p>他にも気になるAI情報がありましたら、ぜひコメントで教えてくださいね！明日もお楽しみに！</p>
"""
        
        # 全体を結合
        full_content = intro + ''.join(content_sections) + outro
        
        return {
            'title': title,
            'content': full_content,
            'articles_count': len(processed_articles)
        }
    
    async def run_daily_collection(self):
        """1日の記事収集・投稿を実行"""
        print("=== AI記事収集・投稿システム開始（1日1記事まとめ版） ===")
        
        # 今日の投稿数をチェック
        today_count = self.load_today_posts_count()
        
        if today_count >= self.max_posts_per_day:
            print(f"今日の投稿はすでに完了しています（{today_count}/{self.max_posts_per_day}件）。")
            return
        
        print(f"今日の投稿数: {today_count}/{self.max_posts_per_day}")
        print(f"今日のまとめ記事を作成します（目標: {self.articles_per_post}件のニュース）")
        
        try:
            # 記事を収集
            print("\n--- 記事収集開始 ---")
            articles = await self.collector.collect_all_sources()
            
            if not articles:
                print("収集できた記事がありません。")
                return
            
            print(f"合計 {len(articles)} 件の記事を収集")
            
            # 最高品質の記事を選択（5件）
            best_articles = self.select_best_articles(articles, self.articles_per_post)
            print(f"まとめ記事用に {len(best_articles)} 件の記事を選択")
            
            if len(best_articles) < 3:
                print("十分な記事数が確保できませんでした。最低3件必要です。")
                return
            
            # 各記事を処理（要約・感想生成）
            print(f"\n--- {len(best_articles)}件の記事処理開始 ---")
            processed_articles = []
            
            for i, article in enumerate(best_articles, 1):
                try:
                    print(f"\n[{i}/{len(best_articles)}] 処理中...")
                    print(f"タイトル: {article.title}")
                    print(f"ソース: {getattr(article, 'source', 'Unknown')}")
                    
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
            
            if not processed_articles:
                print("処理できた記事がありません。")
                return
            
            print(f"\n=== 記事処理完了: {len(processed_articles)}件成功 ===")
            
            # 統合ブログ投稿を作成
            print("\n--- 統合ブログ投稿作成中 ---")
            blog_post = self.create_consolidated_blog_post(processed_articles)
            
            print(f"統合記事作成完了:")
            print(f"  タイトル: {blog_post['title']}")
            print(f"  含まれるニュース: {blog_post['articles_count']}件")
            print(f"  本文文字数: {len(blog_post['content'])}文字")
            
            # WordPressに投稿
            print("\n--- WordPress投稿中 ---")
            post_result = self.wp_connector.create_post(
                title=blog_post['title'],
                content=blog_post['content'],
                excerpt=f"本日の注目AIニュース{blog_post['articles_count']}選をお届けします。各ニュースの要約と影響分析をご覧ください。"
            )
            
            if post_result:
                # 投稿数を更新
                self.save_today_posts_count(1)
                
                print(f"✅ 投稿成功!")
                print(f"   投稿ID: {post_result['id']}")
                print(f"   投稿URL: {post_result.get('link', 'N/A')}")
                print(f"   含まれるニュース: {blog_post['articles_count']}件")
                
                print(f"\n=== 処理完了 ===")
                print(f"今日のまとめ記事投稿が完了しました！")
                
            else:
                print("❌ WordPress投稿に失敗しました")
            
        except Exception as e:
            print(f"システムエラー: {e}")
            raise

async def collect_all_news_sources():
    """全ニュースソースから記事を収集（高度版）"""
    all_articles = []
    
    print("🚀 高度統合記事収集開始")
    
    # 1. 高度スクレイピング（並列処理）
    try:
        from advanced_scraper import AdvancedScraper
        advanced_scraper = AdvancedScraper(max_concurrent=15)
        
        # 古いキャッシュを削除
        advanced_scraper.clear_cache(max_age_days=1)
        
        # 高度スクレイピング実行
        advanced_articles = await advanced_scraper.collect_all_articles(max_total_articles=20)
        
        # AdvancedArticleをNewsArticleに変換
        converted_articles = []
        for adv_article in advanced_articles:
            from news_collector import NewsArticle
            article = NewsArticle(
                title=adv_article.title,
                url=adv_article.url,
                content=adv_article.content,
                source=adv_article.source,
                published_date=adv_article.published_date
            )
            converted_articles.append(article)
        
        all_articles.extend(converted_articles)
        print(f"⚡ 高度スクレイピング: {len(converted_articles)}件")
        
    except Exception as e:
        print(f"❌ 高度スクレイピングエラー: {e}")
        
        # フォールバック: 通常のスクレイピング
        try:
            collector = AINewsCollector()
            regular_articles = collector.collect_daily_articles()
            all_articles.extend(regular_articles)
            print(f"📰 フォールバック収集: {len(regular_articles)}件")
        except Exception as e2:
            print(f"❌ フォールバック収集エラー: {e2}")
    
    # 2. X関連情報収集 - 完全無効化
    # ユーザー要求により、X風の情報も含めて全て無効化
    print(f"⚠️ X関連情報収集は無効化されています（ユーザー要求）")
    
    # try:
    #     from simple_x_collector import collect_simple_x_posts
    #     x_posts = await collect_simple_x_posts(max_posts=3)
    #     
    #     # XPostをNewsArticleに変換
    #     x_articles = []
    #     for x_post in x_posts:
    #         from news_collector import NewsArticle
    #         article = NewsArticle(
    #             title=x_post.title,
    #             url=x_post.url,
    #             content=x_post.content,
    #             source=x_post.source,
    #             published_date=x_post.published_date,
    #             author=x_post.author
    #         )
    #         x_articles.append(article)
    #     
    #     all_articles.extend(x_articles)
    #     print(f"📱 X関連情報: {len(x_articles)}件")
    #     
    # except Exception as e:
    #     print(f"❌ X関連情報収集エラー: {e}")
    
    # 3. 重複除去と品質フィルタリング
    try:
        filtered_articles = remove_duplicates_and_filter(all_articles)
        print(f"🔍 フィルタリング後: {len(filtered_articles)}件")
        
        print(f"📊 総合計: {len(filtered_articles)}件の高品質記事を収集")
        return filtered_articles
        
    except Exception as e:
        print(f"❌ フィルタリングエラー: {e}")
        return all_articles

def remove_duplicates_and_filter(articles):
    """重複除去と品質フィルタリング"""
    seen_urls = set()
    seen_titles = set()
    filtered_articles = []
    
    for article in articles:
        # URL重複チェック
        if article.url in seen_urls:
            continue
        
        # タイトル重複チェック（類似度）
        title_key = article.title.lower().strip()
        if title_key in seen_titles:
            continue
        
        # 品質チェック
        if len(article.content) < 100:  # 最小文字数
            continue
        
        if len(article.title) < 10:  # 最小タイトル長
            continue
        
        seen_urls.add(article.url)
        seen_titles.add(title_key)
        filtered_articles.append(article)
    
    # 最新順にソート
    filtered_articles.sort(key=lambda x: x.published_date or "", reverse=True)
    
    return filtered_articles

async def main():
    """メイン実行関数"""
    try:
        print("=== AI情報収集・投稿システム開始 ===")
        
        # 統合記事収集
        articles = await collect_all_news_sources()
        
        if not articles:
            print("❌ 記事が収集されませんでした")
            return
        
        print(f"✅ {len(articles)}件の記事を収集しました")
        
        # 記事処理
        processor = ArticleProcessor()
        processed_articles = processor.process_articles_batch(articles)
        
        if not processed_articles:
            print("❌ 記事の処理に失敗しました")
            return
        
        print(f"✅ {len(processed_articles)}件の記事を処理しました")
        
        # ブログ投稿生成
        blog_generator = BlogPostGenerator()
        blog_post = blog_generator.generate_daily_blog_post(processed_articles)
        
        # WordPress投稿
        wp_connector = WordPressConnector()
        if wp_connector.post_article(
            title=blog_post['title'],
            content=blog_post['content'],
            tags=blog_post['tags']
        ):
            print("✅ WordPressに投稿完了")
        else:
            print("❌ WordPress投稿に失敗")
        
        print("=== システム実行完了 ===")
        
    except Exception as e:
        print(f"❌ システムエラー: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 