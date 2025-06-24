"""
記事要約・感想生成モジュール
OpenAI APIを使用して記事の要約と感想を生成
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
import openai
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

from news_collector import NewsArticle

@dataclass
class ProcessedArticle:
    """処理済み記事のデータクラス"""
    original_article: NewsArticle
    summary: str
    user_value_comment: str
    processing_date: str
    translated_title: str = ""  # 翻訳されたタイトル
    content_preview: str = ""   # 本文プレビュー
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'title': self.original_article.title,
            'translated_title': self.translated_title,
            'url': self.original_article.url,
            'source': self.original_article.source,
            'original_content': self.original_article.content,
            'content_preview': self.content_preview,
            'summary': self.summary,
            'user_value_comment': self.user_value_comment,
            'processing_date': self.processing_date,
            'hash_id': self.original_article.hash_id
        }

class ArticleProcessor:
    """記事処理クラス"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定するか、引数で指定してください。")
        
        # OpenAI クライアントの初期化
        openai.api_key = self.openai_api_key
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # プロンプトテンプレート
        self.summary_prompt_template = """
以下のAI関連記事を250字程度で要約してください。

【文体の要件】
- 完全に「です・ます調」で統一する
- 親しみやすく読みやすい文体で書く
- 硬い表現を避け、わかりやすい言葉を使う
- 読者との距離感を縮める表現を心がける

【改行ルール（重要）】
- 2-3文ごとに改行する（適度な段落分け）
- 改行は「\n」を使用する
- 読みやすい自然な文章の流れを重視する

【内容の要件】
- 技術的な内容を分かりやすく説明
- 重要なポイントと実用的な価値を含める
- 読者が興味を持てるような書き方

記事タイトル: {title}
記事内容: {content}

要約（250字程度、です・ます調で1文ごと改行）:
"""
        
        self.user_value_prompt_template = """
以下のAI関連記事について、深い洞察と感情豊かな感想を書いてください。

【文体】ChatGPTのような親しみやすい会話調で、「これは嬉しいですね！」「正直言って」「個人的には」などの自然な表現を使用。

【内容】技術の本質的意味、社会への影響、人間的価値を多角的に考察し、表面的な「便利」を超えた深い気づきを提供。

【感情表現】嬉しさ、期待、心配など人間らしい感情の根本的理由を明確に表現。

【改行】1-2文ごとに改行（\n使用）し、自然な会話の流れを重視。

記事タイトル: {title}
記事要約: {summary}

感想（300-400文字程度で、深い洞察を込めた親しみやすい会話調で、必ず完全な文章で終わること）:
"""
        
        self.translation_prompt_template = """
以下の英語のタイトルを自然で読みやすい日本語に翻訳してください。

【翻訳の要件】
- 技術記事として自然な日本語表現
- 専門用語は適切な日本語に置き換える
- 読者にとって分かりやすい表現
- 原文の意味を正確に保持

英語タイトル: {title}

日本語翻訳:
"""
    
    def translate_english_title(self, title: str) -> str:
        """英語タイトルを日本語に翻訳"""
        # 英語かどうかを簡単にチェック
        if not re.search(r'[a-zA-Z]', title):
            return title  # 英語が含まれていない場合はそのまま返す
        
        try:
            prompt = self.translation_prompt_template.format(title=title)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは技術記事の翻訳を得意とする翻訳者です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            translated = response.choices[0].message.content
            if translated:
                return translated.strip()
            return title
            
        except Exception as e:
            print(f"翻訳エラー: {e}")
            return title  # エラーの場合は元のタイトルを返す
    
    def create_content_preview(self, content: str, max_length: int = 200) -> str:
        """記事本文のプレビューを作成"""
        if not content:
            return ""
        
        # HTMLタグを除去
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # 改行や余分な空白を整理
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        # 指定された長さでカット
        if len(clean_content) <= max_length:
            return clean_content
        
        # 文の境界で切る
        preview = clean_content[:max_length]
        last_period = preview.rfind('.')
        last_question = preview.rfind('?')
        last_exclamation = preview.rfind('!')
        
        # 最後の句読点を見つける
        last_sentence_end = max(last_period, last_question, last_exclamation)
        
        if last_sentence_end > max_length * 0.7:  # 70%以上の位置にある場合
            preview = preview[:last_sentence_end + 1]
        else:
            preview = preview + "..."
        
        return preview
    
    def extract_image_from_content(self, content: str) -> Optional[str]:
        """記事本文から画像URLを抽出"""
        # img タグのsrc属性を抽出
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, content, re.IGNORECASE)
        
        if matches:
            # 最初の画像URLを返す
            return matches[0]
        
        # Markdown形式の画像も検索
        md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
        md_matches = re.findall(md_img_pattern, content)
        
        if md_matches:
            return md_matches[0]
        
        return None
    
    def generate_summary(self, article: NewsArticle) -> str:
        """記事の要約を生成"""
        try:
            prompt = self.summary_prompt_template.format(
                title=article.title,
                content=article.content[:2000]  # 最初の2000文字まで
            )
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは技術記事の要約を得意とするライターです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            if summary:
                return summary.strip()
            return article.content[:300] + "..."
            
        except Exception as e:
            print(f"要約生成エラー: {e}")
            # フォールバック: 記事の最初の部分を使用
            return article.content[:300] + "..."
    
    def generate_user_value_comment(self, article: NewsArticle, summary: str) -> str:
        """ユーザー価値視点での感想を生成"""
        try:
            prompt = self.user_value_prompt_template.format(
                title=article.title,
                summary=summary
            )
            
            print(f"o3-miniで感想生成中（記事: {article.title[:30]}...）")
            
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {"role": "system", "content": "あなたはChatGPTのような親しみやすく感情豊かなAIアシスタントです。技術記事に対して、読者の気持ちに寄り添った自然で温かい感想を書いてください。嬉しさ、期待、ちょっとした心配など、人間らしい感情を込めて表現してください。深い洞察と思考を込めて、表面的ではない本質的な感想を提供してください。必ず完全な文章で終わるようにしてください。"},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000  # トークン数を増やす
            )
            
            # レスポンスの詳細確認
            comment = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            print(f"o3-miniレスポンス詳細: 文字数={len(comment) if comment else 0}, finish_reason={finish_reason}")
            
            if comment:
                comment = comment.strip()
                
                # 文章が途中で切れていないかチェック
                if finish_reason == "length":
                    print("⚠️ 警告: o3-miniの出力がトークン制限により途中で切れました")
                    # 最後の句点で切る
                    last_period = comment.rfind('。')
                    if last_period > len(comment) * 0.7:  # 70%以上の位置にある場合
                        comment = comment[:last_period + 1]
                    else:
                        comment += "..."  # 途中で切れた場合は省略記号を追加
                
                # 最低限の長さをチェック
                if len(comment) < 50:
                    print(f"⚠️ 警告: 感想が短すぎます（{len(comment)}文字）")
                
                return comment
            
            return "これは面白そうな技術ですね！\n私たちの生活がもっと便利になりそうで、ちょっとワクワクします。"
            
        except Exception as e:
            print(f"感想生成エラー: {e}")
            # フォールバック: 簡単なコメント
            return "これは面白そうな技術ですね！\n私たちの生活がもっと便利になりそうで、ちょっとワクワクします。"
    
    def process_article(self, article: NewsArticle) -> ProcessedArticle:
        """記事を処理（要約+感想生成+プレビュー）"""
        print(f"記事処理中: {article.title}")
        
        # 日本語記事のみを収集しているため、タイトル翻訳はスキップ
        translated_title = article.title  # 元のタイトルをそのまま使用
        
        # 本文プレビュー作成
        content_preview = self.create_content_preview(article.content)
        print(f"プレビュー作成完了: {len(content_preview)}文字")
        
        # 要約生成
        summary = self.generate_summary(article)
        print(f"要約生成完了: {len(summary)}文字")
        
        # 感想生成
        user_value_comment = self.generate_user_value_comment(article, summary)
        print(f"感想生成完了: {len(user_value_comment)}文字")
        
        processed_article = ProcessedArticle(
            original_article=article,
            summary=summary,
            user_value_comment=user_value_comment,
            processing_date=datetime.now().isoformat(),
            translated_title=translated_title,
            content_preview=content_preview
        )
        
        return processed_article
    
    def process_articles_batch(self, articles: List[NewsArticle]) -> List[ProcessedArticle]:
        """複数記事の一括処理"""
        processed_articles = []
        
        print(f"=== {len(articles)}件の記事処理開始 ===")
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] 処理中...")
            try:
                processed = self.process_article(article)
                processed_articles.append(processed)
                print("✅ 処理完了")
            except Exception as e:
                print(f"❌ 処理エラー: {e}")
                continue
        
        print(f"\n=== 処理完了: {len(processed_articles)}/{len(articles)}件成功 ===")
        return processed_articles
    
    def save_processed_articles(self, processed_articles: List[ProcessedArticle], filename: str = None) -> str:
        """処理済み記事を保存"""
        if not filename:
            filename = f"processed_articles_{datetime.now().strftime('%Y%m%d')}.json"
        
        articles_data = [article.to_dict() for article in processed_articles]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        print(f"処理済み記事を {filename} に保存しました")
        return filename

class BlogPostGenerator:
    """ブログ投稿用記事生成クラス"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI APIキーが設定されていません。")
        
        self.client = openai.OpenAI(api_key=self.openai_api_key)
    
    def generate_daily_blog_post(self, processed_articles: List[ProcessedArticle]) -> Dict[str, str]:
        """1日分の記事から統合ブログ投稿を生成"""
        
        # 記事情報をまとめる
        articles_summary = ""
        for i, article in enumerate(processed_articles, 1):
            articles_summary += f"""
{i}. {article.original_article.title}
ソース: {article.original_article.source}
URL: {article.original_article.url}
要約: {article.summary}
ユーザー価値: {article.user_value_comment}

"""
        
        blog_prompt = f"""
以下の{len(processed_articles)}件のAI関連記事から、ChatGPTのような親しみやすく感情豊かな統合ブログ投稿を作成してください。

記事情報:
{articles_summary}

【文体の要件】
- ChatGPTのような自然で親しみやすい会話調
- 「これは嬉しいですね！」「ちょっと驚きました」など感情表現を豊富に使う
- 「正直言って」「実際のところ」「個人的には」などの自然な口調
- 読者との距離を縮める表現（「皆さんも感じませんか？」「私も同じことを思いました」）

【感情表現の要件】
- 読者が何を嬉しく感じるかを明確に表現
- 期待感や驚き、ちょっとした心配も正直に
- 「わかる〜！」「そうそう！」と共感できる表現
- 読者の気持ちに寄り添った温かい表現

【改行ルール】
- 1-2文ごとに改行して読みやすく
- 改行は「\n」を使用する
- 段落の間は2回改行（\n\n）する

以下の形式でブログ投稿を作成してください：

1. タイトル: 親しみやすく興味を引くタイトル
2. 導入文: 今日のAI動向への感想（感情豊かで親しみやすい文体で、1-2文ごと改行）
3. 各記事の紹介: 記事ごとに感想を交えて紹介（感情豊かに、1-2文ごと改行）
4. まとめ: 読者への親しみやすいメッセージ（温かく感情豊かに、1-2文ごと改行）

読者が「わかる〜！」と共感し、親近感を持てる内容にしてください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはChatGPTのような親しみやすく感情豊かなAIアシスタントです。技術ブログを書く時も、読者の気持ちに寄り添った温かく自然な文体で、感情を込めて表現してください。"},
                    {"role": "user", "content": blog_prompt}
                ],
                max_tokens=1500,
                temperature=0.8
            )
            
            blog_content = response.choices[0].message.content.strip()
            
            # タイトルと本文を分離
            lines = blog_content.split('\n')
            title = lines[0].replace('タイトル:', '').replace('# ', '').strip()
            content = '\n'.join(lines[1:]).strip()
            
            return {
                'title': title,
                'content': content,
                'articles_count': len(processed_articles),
                'generation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"ブログ投稿生成エラー: {e}")
            # フォールバック
            return {
                'title': f"今日のAI動向まとめ ({len(processed_articles)}件)",
                'content': f"今日は{len(processed_articles)}件のワクワクするAI関連記事をお届けします！\n皆さんもきっと興味深く読んでいただけると思います。",
                'articles_count': len(processed_articles),
                'generation_date': datetime.now().isoformat()
            }

def main():
    """テスト実行"""
    # サンプル記事でテスト
    sample_articles = [
        NewsArticle(
            title="OpenAIが新機能を発表、X/Twitterで話題に",
            url="https://example.com/openai-news",
            content="OpenAIが最新のAI機能を発表し、X/Twitterで大きな反響を呼んでいます。この新機能により、ユーザーはより効率的にAIを活用できるようになります。新しいAPIエンドポイントが追加され、開発者はより柔軟にAI機能を統合できます。",
            source="Tech News"
        )
    ]
    
    # 環境変数チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("OPENAI_API_KEYが設定されていません。テスト用のダミーデータを使用します。")
        # ダミー処理結果
        processed = ProcessedArticle(
            original_article=sample_articles[0],
            summary="OpenAIが新しいAI機能を発表。ユーザーの効率性向上と開発者の統合柔軟性が向上。",
            user_value_comment="ユーザーはより簡単にAI機能を利用でき、日常業務の効率化が期待できます。",
            processing_date=datetime.now().isoformat()
        )
        
        print("=== ダミー処理結果 ===")
        print(f"タイトル: {processed.original_article.title}")
        print(f"要約: {processed.summary}")
        print(f"感想: {processed.user_value_comment}")
        
        return [processed]
    
    try:
        processor = ArticleProcessor()
        processed_articles = processor.process_articles_batch(sample_articles)
        processor.save_processed_articles(processed_articles)
        return processed_articles
    except Exception as e:
        print(f"処理エラー: {e}")
        return []

if __name__ == "__main__":
    main()

