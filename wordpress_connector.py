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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import openai
from io import BytesIO

# 環境変数を読み込み
load_dotenv()

from article_processor import ProcessedArticle

class WordPressConnector:
    """WordPress連携クラス"""
    
    def __init__(self, config_file: str = "wordpress_config.json"):
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.setup_authentication()
        
        # OpenAI設定
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # リトライ設定
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
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
    
    def generate_featured_image_prompt(self, title: str, content: str = "") -> str:
        """
        記事タイトルと内容からアイキャッチ画像生成プロンプトを作成
        """
        try:
            resp = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "あなたは画像プロンプト作成のエキスパートです。"
                            "AIニュース記事のアイキャッチ画像に適した、極端にシンプルで"
                            "パステルカラーのアイコンベース画像を生成するための英語プロンプトを1文で答えてください。\n\n"
                            "要件：\n"
                            "- extremely simple, minimalist, icon-based design\n"
                            "- soft pastel colors (light pink, mint green, lavender, peach, sky blue)\n"
                            "- AI関連のシンプルなアイコン（脳、回路、ロボット顔など）\n"
                            "- 白い背景\n"
                            "- 文字やテキストは含めない\n"
                            "- flat design, vector-style\n"
                            "- 例: 'Extremely simple minimalist AI brain icon in soft pastel colors, flat design, white background, vector-style illustration'"
                        )
                    },
                    {"role": "user", "content": f"タイトル: {title}\n内容の概要: {content[:200]}"}
                ],
                temperature=0.7,
                max_tokens=200
            )
            content = resp.choices[0].message.content
            return content.strip() if content else "Extremely simple minimalist AI brain icon in soft pastel colors, flat design, white background, vector-style illustration"
        except Exception as e:
            print(f"画像プロンプト生成エラー: {e}")
            # フォールバック用のデフォルトプロンプト
            return "Extremely simple minimalist AI brain icon in soft pastel colors, flat design, white background, vector-style illustration"

    def generate_featured_image_url(self, image_prompt: str) -> Optional[str]:
        """
        DALL·E 3でアイキャッチ画像を生成
        """
        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1792x1024",  # アイキャッチに適したサイズ
                n=1
            )
            return response.data[0].url
        except Exception as e:
            print(f"画像生成エラー: {e}")
            return None

    def upload_image_to_wp(self, image_url: str, filename: str = None) -> tuple[Optional[int], Optional[str]]:
        """
        画像をWordPressにアップロード
        """
        if not image_url:
            return None, None
            
        print(f"アイキャッチ画像アップロード開始: {image_url}")
        
        try:
            # 画像を取得
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            original_data = img_response.content
            print(f"画像サイズ: {len(original_data)} bytes")
            
            # 画像サイズが大きい場合はリサイズ
            if len(original_data) > 500 * 1024:  # 500KB以上の場合
                try:
                    from PIL import Image
                    import io
                    
                    # 画像を開く
                    img = Image.open(io.BytesIO(original_data))
                    print(f"元画像サイズ: {img.size}")
                    
                    # アスペクト比を保持してリサイズ（最大1200x800）
                    img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                    print(f"リサイズ後: {img.size}")
                    
                    # JPEG形式で圧縮
                    img_buffer = io.BytesIO()
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(img_buffer, format='JPEG', quality=85, optimize=True)
                    img_data = img_buffer.getvalue()
                    print(f"圧縮後サイズ: {len(img_data)} bytes")
                    
                    filename = filename or "ai_news_featured_image.jpg"
                    content_type = "image/jpeg"
                    
                except ImportError:
                    print("Pillowがインストールされていません。元画像を使用します。")
                    img_data = original_data
                    filename = filename or "ai_news_featured_image.jpg"
                    content_type = "image/jpeg"
            else:
                img_data = original_data
                filename = filename or "ai_news_featured_image.jpg"
                content_type = "image/jpeg"
            
            # WordPressにアップロード
            api_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/media')
            
            # ファイル名をASCII文字のみに変換
            safe_filename = "".join(c for c in filename if ord(c) < 128) or "featured_image.jpg"
            
            # 認証情報を取得
            wp_user = self.config['wp_user']
            wp_app_pass = self.config['wp_app_pass']
            
            resp = requests.post(
                api_url,
                auth=(wp_user, wp_app_pass),
                headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
                files={"file": (safe_filename, img_data, content_type)},
                timeout=60
            )
            
            if resp.status_code == 201:
                media_data = resp.json()
                print(f"アイキャッチ画像アップロード成功: {filename} (ID: {media_data['id']})")
                return media_data["id"], media_data["source_url"]
            else:
                print(f"画像アップロードエラー: {resp.status_code} - {resp.text}")
                return None, None
                
        except Exception as e:
            print(f"画像アップロード例外: {e}")
            return None, None

    def create_post(self, title: str, content: str, excerpt: str = "", tags: Optional[List[str]] = None, custom_slug: Optional[str] = None) -> Optional[Dict]:
        """WordPress記事を作成（アイキャッチ画像生成機能付き）"""
        try:
            api_url = urljoin(self.config['wp_url'], '/wp-json/wp/v2/posts')
            
            # タグの処理 - 文字列タグをタグIDに変換
            tag_ids = []
            if tags is None:
                tags = self.config['post_settings']['tags']
            
            if tags:
                tag_ids = self.get_or_create_tag_ids(tags)
            
            # アイキャッチ画像の生成（設定で制御）
            featured_media_id = None
            generate_featured_image = self.config['post_settings'].get('generate_featured_image', True)
            
            if generate_featured_image:
                try:
                    print("🎨 アイキャッチ画像生成開始...")
                    image_prompt = self.generate_featured_image_prompt(title, content)
                    print(f"画像プロンプト: {image_prompt}")
                    
                    image_url = self.generate_featured_image_url(image_prompt)
                    if image_url:
                        media_id, media_url = self.upload_image_to_wp(image_url, f"featured_{title[:20]}.jpg")
                        if media_id:
                            featured_media_id = media_id
                            print(f"✅ アイキャッチ画像設定完了 (ID: {media_id})")
                        else:
                            print("⚠️ アイキャッチ画像アップロードに失敗")
                    else:
                        print("⚠️ アイキャッチ画像生成に失敗")
                except Exception as e:
                    print(f"⚠️ アイキャッチ画像処理エラー: {e}")
                    print("📝 アイキャッチ画像なしで記事作成を続行します")
            else:
                print("📝 アイキャッチ画像生成は無効です")
            
            post_data = {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'status': self.config['post_settings']['status'],
                'categories': [self.config['post_settings']['category_id']],
                'tags': tag_ids,  # タグIDの配列を使用
                'author': self.config['post_settings']['author_id']
            }
            
            # アイキャッチ画像を設定
            if featured_media_id:
                post_data['featured_media'] = featured_media_id
            
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
            
            response = self.session.post(api_url, json=post_data, timeout=30)
            
            if response.status_code == 201:
                post_info = response.json()
                print(f"WordPress投稿成功: {post_info['link']}")
                if featured_media_id:
                    print(f"🖼️ アイキャッチ画像付きで投稿完了")
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
    
    def format_article_for_post(self, processed_article: ProcessedArticle, article_number: int) -> str:
        """記事を投稿用にフォーマット（HTMLタグ使用）"""
        article = processed_article.original_article
        
        # ソース名を整形
        source_name = getattr(article, 'source', 'Unknown').title()
        if source_name == 'Unknown':
            # URLからソース名を推定
            if 'venturebeat' in article.url.lower():
                source_name = 'Venturebeat'
            elif 'cnet' in article.url.lower():
                source_name = 'Cnet_Japan'
            elif 'nikkei' in article.url.lower():
                source_name = 'Nikkei'
            elif 'ascii' in article.url.lower():
                source_name = 'ASCII'
            elif 'itmedia' in article.url.lower():
                source_name = 'ITmedia'
            else:
                source_name = 'Tech News'
        
        # 日本語記事のため元のタイトルをそのまま使用
        display_title = article.title
        
        # 要約と感想の改行を適切に処理（HTML化）
        summary_html = processed_article.summary.replace('\n', '<br>\n')
        comment_html = processed_article.user_value_comment.replace('\n', '<br>\n')
        
        formatted_content = f"""<h2>📰 {article_number}. {display_title}</h2>

<blockquote>
<strong>ソース:</strong> {source_name}<br>
<strong>元タイトル:</strong> {article.title}<br>
<br>
<a href="{article.url}" target="_blank">📖 元記事を読む →</a>
</blockquote>

<p>ソース: {source_name}</p>

<h4>🔍 記事プレビュー</h4>

<p>{getattr(processed_article, 'content_preview', '') or article.content[:200] + '...'}</p>

<h3>📝 記事の要約</h3>

<p>{summary_html}</p>

<h3>💡 私たちへの影響と今後の展望</h3>

<p>{comment_html}</p>

<hr>

"""
        return formatted_content
    
    def generate_daily_post_content(self, processed_articles: List[ProcessedArticle]) -> Dict:
        """1日分の投稿コンテンツを生成（HTMLタグ使用）"""
        today = datetime.now()
        
        # タイトル生成（正しい形式）
        title = f"今日のAIニュース {len(processed_articles)}選 – {today.strftime('%Y年%m月%d日')}"
        
        # 導入文
        intro = f"""<p>こんにちは！今日も最新のAI情報をお届けします！</p>

<p>本日は{len(processed_articles)}件の注目すべきAIニュースをピックアップしました。それぞれのニュースについて、要約と私たちへの影響を分析してお伝えします。</p>

"""
        
        # 目次生成
        toc = "<h2>目次</h2>\n\n"
        for i, processed_article in enumerate(processed_articles, 1):
            # 日本語記事のため元のタイトルをそのまま使用
            article_title = processed_article.original_article.title
            # タイトルを短縮
            if len(article_title) > 50:
                short_title = article_title[:50] + "..."
            else:
                short_title = article_title
            toc += f"<p><strong>{i}. {short_title}</strong></p>\n\n"
        
        toc += "\n"
        
        # 各記事のコンテンツ
        articles_content = ""
        for i, processed_article in enumerate(processed_articles, 1):
            articles_content += self.format_article_for_post(processed_article, i)
        
        # まとめ
        conclusion = f"""<h2>🎯 今日のまとめ</h2>

<p>いかがでしたでしょうか？今日も様々なAI技術の進歩が見られましたね！</p>

<p>これらの技術動向は、私たちの日常生活や仕事に大きな変化をもたらす可能性があります。ぜひこの情報を参考に、AI技術を積極的に活用していってください。</p>

<p>他にも気になるAI情報がありましたら、ぜひコメントで教えてくださいね！明日もお楽しみに！</p>
"""
        
        # 全体のコンテンツ
        full_content = intro + toc + articles_content + conclusion
        
        # 抜粋（excerpt）
        excerpt = f"今日のAI情報まとめです！{len(processed_articles)}件の注目記事を、わかりやすい要約と私たちの生活への影響という視点でご紹介しています。"
        
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
            tags=["AI", "AIニュース", "まとめ", "技術動向", "最新情報"]
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

