"""
WordPress投稿連携モジュール
既存のWordPressシステムと連携して記事を投稿
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime
import base64
from urllib.parse import urljoin
from dotenv import load_dotenv
import re
import unicodedata

# 環境変数を読み込み
load_dotenv()

from article_processor import ProcessedArticle

class WordPressConnector:
    """WordPress連携クラス"""
    
    def __init__(self, config_file: str = "wordpress_config.json"):
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.setup_authentication()
    
    def generate_slug(self, title: str) -> str:
        """タイトルからWordPressスラッグを生成"""
        # 日本語から英語への変換マップ（長い単語から先に処理するため順序重要）
        jp_to_en_map = {
            # 複合語・長い単語を先に処理
            'スマートフォン': 'smartphone',
            'プラットフォーム': 'platform',
            'インターネット': 'internet',
            'コンピュータ': 'computer',
            'ソフトウェア': 'software',
            'ハードウェア': 'hardware',
            'セキュリティ': 'security',
            'プライバシー': 'privacy',
            'アップデート': 'update',
            'リリース': 'release',
            'サービス': 'service',
            'ビジネス': 'business',
            'デメリット': 'demerit',
            'メリット': 'merit',
            'システム': 'system',
            'ユーザー': 'user',
            'デバイス': 'device',
            'オンライン': 'online',
            'クラウド': 'cloud',
            'データ': 'data',
            'ツール': 'tool',
            'アプリ': 'app',
            'テスト': 'test',
            'ウェブ': 'web',
            
            # AI関連用語
            'AI': 'ai',
            'ChatGPT': 'chatgpt',
            'GPT': 'gpt',
            'OpenAI': 'openai',
            'Google': 'google',
            'Microsoft': 'microsoft',
            'Amazon': 'amazon',
            'Apple': 'apple',
            'Meta': 'meta',
            'Tesla': 'tesla',
            'NVIDIA': 'nvidia',
            'DeepMind': 'deepmind',
            'Claude': 'claude',
            'Alexa': 'alexa',
            'Siri': 'siri',
            'Azure': 'azure',
            'Python': 'python',
            
            # 基本単語
            'ニュース': 'news',
            '技術': 'tech',
            '動向': 'trends',
            '最新': 'latest',
            '情報': 'info',
            'まとめ': 'summary',
            '今日': 'today',
            '本日': 'today',
            '発表': 'announcement',
            '開発': 'development',
            '機能': 'feature',
            '新機能': 'new-feature',
            '企業': 'company',
            '市場': 'market',
            '業界': 'industry',
            '分析': 'analysis',
            '予測': 'prediction',
            '研究': 'research',
            '実験': 'experiment',
            '導入': 'introduction',
            '採用': 'adoption',
            '活用': 'utilization',
            '効果': 'effect',
            '影響': 'impact',
            '変化': 'change',
            '進歩': 'progress',
            '革新': 'innovation',
            '改善': 'improvement',
            '向上': 'enhancement',
            '課題': 'challenge',
            '問題': 'issue',
            '解決': 'solution',
            '対策': 'measure',
            '方法': 'method',
            '手法': 'approach',
            '技法': 'technique',
            '戦略': 'strategy',
            '計画': 'plan',
            '目標': 'goal',
            '成果': 'result',
            '結果': 'outcome',
            '報告': 'report',
            '発見': 'discovery',
            '特徴': 'feature',
            '利点': 'advantage',
            '欠点': 'disadvantage',
            '価格': 'price',
            '費用': 'cost',
            '無料': 'free',
            '有料': 'paid',
            '年': 'year',
            '月': 'month',
            '日': 'day',
            '時間': 'time',
            '分': 'minute',
            '秒': 'second',
            '版': 'version',
            '比較': 'comparison',
            '検証': 'verification',
            '速報': 'breaking',
            '必見': 'must-see',
            '未来': 'future',
            '体験': 'experience',
            '医療': 'medical',
            '分野': 'field',
            '自動': 'auto',
            '運転': 'driving',
            '検索': 'search',
            '拡張': 'expansion',
            '統合': 'integration',
            '公開': 'release',
            '性能': 'performance',
            '大幅': 'significant',
            '自然': 'natural',
            '対話': 'conversation',
            '可能': 'possible',
            '革新的': 'innovative',
            '搭載': 'equipped'
        }
        
        # 日付パターンを処理（例：2024年1月15日 → 2024-01-15）
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        title = re.sub(date_pattern, r'\1-\2-\3', title)
        
        # 数字と単位の処理（例：10個 → 10-items）
        number_unit_pattern = r'(\d+)(個|件|台|人|社|回|時間|分|秒|年|月|日)'
        title = re.sub(number_unit_pattern, r'\1-\2', title)
        
        # 日本語キーワードを英語に変換（大小文字を区別しない）
        for jp, en in jp_to_en_map.items():
            title = title.replace(jp, en)
        
        # Unicode正規化
        title = unicodedata.normalize('NFKC', title)
        
        # 小文字に変換
        title = title.lower()
        
        # 日本語文字を削除し、英数字、ハイフン、アンダースコアのみ残す
        # 日本語文字（ひらがな、カタカナ、漢字）を削除
        title = re.sub(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBF]', '-', title)
        
        # その他の特殊文字もハイフンに置換
        title = re.sub(r'[^\w\-_]', '-', title)
        
        # 連続するハイフンを1つに統合
        title = re.sub(r'-+', '-', title)
        
        # 先頭と末尾のハイフンを削除
        title = title.strip('-')
        
        # 空の場合はデフォルトスラッグ
        if not title:
            title = f"post-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # プレフィックスを追加
        slug_config = self.config.get('slug_settings', {})
        prefix = slug_config.get('prefix', '')
        max_length = slug_config.get('max_length', 50)
        
        if prefix:
            title = f"{prefix}{title}"
        
        # 長すぎる場合は切り詰め
        if len(title) > max_length:
            title = title[:max_length]
        
        return title
    
    def load_config(self, config_file: str) -> Dict:
        """WordPress設定を読み込み"""
        default_config = {
            "wp_url": "https://your-wordpress-site.com",
            "wp_user": "your_wp_username",
            "wp_app_pass": "your_wp_app_password",
            "post_settings": {
                "status": "publish",  # publish, draft, private
                "category_id": 1,
                "tags": ["AI", "技術動向", "最新情報"],
                "author_id": 1,
                "featured_media": None
            },
            "slug_settings": {
                "auto_generate": True,  # 自動スラッグ生成を有効にするか
                "prefix": "",  # スラッグの前に付けるプレフィックス（例：ai-news-）
                "max_length": 50  # スラッグの最大長
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # デフォルト設定とマージ
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"WordPress設定ファイル {config_file} を作成しました。実際の設定に置き換えてください。")
            return default_config
    
    def setup_authentication(self):
        """WordPress認証設定"""
        # Basic認証用のヘッダーを設定
        credentials = f"{self.config['wp_user']}:{self.config['wp_app_pass']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI News Collector Bot 1.0'
        })
    
    def test_connection(self) -> bool:
        """WordPress接続テスト"""
        try:
            api_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/users/me')
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"WordPress接続成功: {user_data.get('name', 'Unknown User')}")
                return True
            else:
                print(f"WordPress接続失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"WordPress接続エラー: {e}")
            return False
    
    def get_or_create_tag_ids(self, tag_names: List[str]) -> List[int]:
        """タグ名からタグIDを取得、存在しない場合は作成"""
        tag_ids = []
        
        for tag_name in tag_names:
            try:
                # 既存のタグを検索
                search_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/tags')
                search_response = self.session.get(search_url, params={'search': tag_name}, timeout=10)
                
                if search_response.status_code == 200:
                    existing_tags = search_response.json()
                    
                    # 完全一致するタグを探す
                    tag_found = False
                    for tag in existing_tags:
                        if tag['name'].lower() == tag_name.lower():
                            tag_ids.append(tag['id'])
                            tag_found = True
                            break
                    
                    # タグが見つからない場合は新規作成
                    if not tag_found:
                        create_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/tags')
                        create_data = {'name': tag_name}
                        create_response = self.session.post(create_url, json=create_data, timeout=10)
                        
                        if create_response.status_code == 201:
                            new_tag = create_response.json()
                            tag_ids.append(new_tag['id'])
                        else:
                            print(f"タグ作成失敗: {tag_name} - {create_response.text}")
                
            except Exception as e:
                print(f"タグ処理エラー: {tag_name} - {e}")
        
        return tag_ids
    
    def create_post(self, title: str, content: str, excerpt: str = "", tags: Optional[List[str]] = None, custom_slug: Optional[str] = None) -> Optional[Dict]:
        """WordPress記事を作成"""
        try:
            api_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/posts')
            
            # タグの処理 - 文字列タグをタグIDに変換
            tag_ids = []
            if tags is None:
                tags = self.config['post_settings']['tags']
            
            if tags:
                tag_ids = self.get_or_create_tag_ids(tags)
            
            post_data = {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'status': self.config['post_settings']['status'],
                'categories': [self.config['post_settings']['category_id']],
                'tags': tag_ids,  # タグIDの配列を使用
                'author': self.config['post_settings']['author_id']
            }
            
            # スラッグの設定
            slug_config = self.config.get('slug_settings', {})
            auto_generate = slug_config.get('auto_generate', True)
            
            if custom_slug is not None and custom_slug.strip():
                # カスタムスラッグが指定されている場合
                slug = custom_slug.strip()
                post_data['slug'] = slug
                print(f"カスタムスラッグを使用: {slug}")
            elif auto_generate:
                # 自動生成が有効な場合
                slug = self.generate_slug(title)
                post_data['slug'] = slug
                print(f"自動生成されたスラッグ: {slug}")
            else:
                # スラッグ生成を無効にしている場合（WordPressのデフォルトを使用）
                print("スラッグ自動生成は無効です。WordPressのデフォルトスラッグを使用します。")
            
            # アイキャッチ画像があれば設定
            if self.config['post_settings']['featured_media']:
                post_data['featured_media'] = self.config['post_settings']['featured_media']
            
            response = self.session.post(api_url, json=post_data, timeout=30)
            
            if response.status_code == 201:
                post_info = response.json()
                print(f"WordPress投稿成功: {post_info['link']}")
                return post_info
            else:
                print(f"WordPress投稿失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"WordPress投稿エラー: {e}")
            return None

class DailyPostGenerator:
    """日次投稿生成クラス"""
    
    def __init__(self, wp_connector: WordPressConnector):
        self.wp_connector = wp_connector
    
    def format_article_for_post(self, processed_article: ProcessedArticle) -> str:
        """記事を投稿用にフォーマット"""
        article = processed_article.original_article
        
        # 記事タイトルから簡潔な見出しを生成
        title_words = article.title.split('、')[0].split('が')[0].split('の')[0]
        if len(title_words) > 20:
            title_words = title_words[:20] + "..."
        
        formatted_content = f"""
<blockquote>
<p>{article.content}</p>
<footer>— <cite><a href="{article.url}" target="_blank">元のポストを見る</a></cite></footer>
</blockquote>

<h4>📝 要約</h4>
<p>{processed_article.summary}</p>

<h4>💡 ユーザーへの具体的な影響</h4>
<p>{processed_article.user_value_comment}</p>

<hr>
"""
        return formatted_content
    
    def generate_daily_post_content(self, processed_articles: List[ProcessedArticle]) -> Dict[str, str]:
        """1日分の投稿コンテンツを生成"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        # タイトル生成
        title = f"今日のAIニュース {today}"
        
        # 導入文
        intro = f"""
<p>本日のAI関連技術動向をお届けします。{len(processed_articles)}件の注目記事をピックアップし、要約と「ユーザーへの具体的な影響」の視点でご紹介いたします。</p>
"""
        
        # 各記事のコンテンツ
        articles_content = ""
        for i, processed_article in enumerate(processed_articles, 1):
            # 記事タイトルから簡潔な見出しを生成
            article_title = processed_article.original_article.title
            # タイトルを短縮して見出しに適した形にする
            if '、' in article_title:
                heading = article_title.split('、')[0]
            elif 'が' in article_title:
                heading = article_title.split('が')[0] + 'の動向'
            elif 'を' in article_title:
                heading = article_title.split('を')[0] + 'について'
            else:
                heading = article_title[:30] + ('...' if len(article_title) > 30 else '')
            
            articles_content += f"<h2>📰 {heading}</h2>\n"
            articles_content += self.format_article_for_post(processed_article)
        
        # まとめ
        conclusion = f"""
<h2>🎯 まとめ</h2>
<p>本日は{len(processed_articles)}件のAI関連記事をご紹介しました。これらの技術動向は、私たちの日常生活やビジネスにおいて、より便利で効率的な体験をもたらす可能性を秘めています。</p>
<p>AI技術の進歩により、ユーザーはより直感的で使いやすいツールを手に入れ、創造性や生産性の向上が期待できます。</p>
<p>明日も最新のAI動向をお届けしますので、ぜひお楽しみに！</p>
"""
        
        # 全体のコンテンツ
        full_content = intro + articles_content + conclusion
        
        # 抜粋（excerpt）
        excerpt = f"本日のAI技術動向まとめ。{len(processed_articles)}件の注目記事を要約し、ユーザー価値の視点で解説します。"
        
        return {
            'title': title,
            'content': full_content,
            'excerpt': excerpt,
            'articles_count': len(processed_articles)
        }
    
    def publish_daily_post(self, processed_articles: List[ProcessedArticle]) -> Optional[Dict]:
        """日次投稿を公開"""
        if not processed_articles:
            print("投稿する記事がありません")
            return None
        
        print(f"=== {len(processed_articles)}件の記事でWordPress投稿を作成中 ===")
        
        # 投稿コンテンツ生成
        post_content = self.generate_daily_post_content(processed_articles)
        
        # WordPress投稿
        post_info = self.wp_connector.create_post(
            title=post_content['title'],
            content=post_content['content'],
            excerpt=post_content['excerpt'],
            tags=["AI", "技術動向", "まとめ", "最新情報"]
        )
        
        if post_info:
            print(f"✅ 投稿成功: {post_info['link']}")
            
            # 投稿ログを保存
            log_data = {
                'post_id': post_info['id'],
                'post_url': post_info['link'],
                'title': post_content['title'],
                'articles_count': post_content['articles_count'],
                'published_date': datetime.now().isoformat(),
                'articles': [
                    {
                        'title': pa.original_article.title,
                        'url': pa.original_article.url,
                        'source': pa.original_article.source
                    }
                    for pa in processed_articles
                ]
            }
            
            log_filename = f"wordpress_post_log_{datetime.now().strftime('%Y%m%d')}.json"
            with open(log_filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            print(f"投稿ログを {log_filename} に保存しました")
            return post_info
        else:
            print("❌ 投稿失敗")
            return None

def main():
    """テスト実行"""
    # WordPress接続テスト
    wp_connector = WordPressConnector()
    
    print("=== WordPress接続テスト ===")
    if not wp_connector.test_connection():
        print("WordPress設定を確認してください")
        return
    
    # サンプル処理済み記事でテスト
    from news_collector import NewsArticle
    from article_processor import ProcessedArticle
    
    sample_processed = [
        ProcessedArticle(
            original_article=NewsArticle(
                title="OpenAIが新機能を発表、X/Twitterで話題に",
                url="https://example.com/openai-news",
                content="OpenAIが最新のAI機能を発表...",
                source="Tech News"
            ),
            summary="OpenAIが新しいAI機能を発表。ユーザーの効率性向上と開発者の統合柔軟性が向上。",
            user_value_comment="ユーザーはより簡単にAI機能を利用でき、日常業務の効率化が期待できます。",
            processing_date=datetime.now().isoformat()
        )
    ]
    
    # 投稿テスト
    post_generator = DailyPostGenerator(wp_connector)
    post_info = post_generator.publish_daily_post(sample_processed)
    
    if post_info:
        print(f"テスト投稿完了: {post_info['link']}")
    else:
        print("テスト投稿失敗")

if __name__ == "__main__":
    main()

