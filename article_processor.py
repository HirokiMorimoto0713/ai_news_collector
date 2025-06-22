"""
記事要約・感想生成モジュール
OpenAI APIを使用して記事の要約と感想を生成
"""

import os
import json
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
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'title': self.original_article.title,
            'url': self.original_article.url,
            'source': self.original_article.source,
            'original_content': self.original_article.content,
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
ChatGPTのような親しみやすく、かつ正確な文体で、技術的な内容を分かりやすく説明してください。
重要なポイントと実用的な価値を含めて要約してください。

記事タイトル: {title}
記事内容: {content}

要約（250字程度）:
"""
        
        self.user_value_prompt_template = """
以下のAI関連記事について、「このニュースおよび技術によってユーザーは具体的にどんな影響を受けるか」という視点で感想・コメントを200字程度で書いてください。

具体的な影響の例：
- 日常生活での変化（作業効率、時間短縮、新しい体験など）
- ビジネスや仕事への影響（生産性、コスト削減、新しい機会など）
- 社会全体への波及効果（アクセシビリティ向上、教育、医療など）

ChatGPTのような親しみやすく、かつ専門的な文体で回答してください。

記事タイトル: {title}
記事要約: {summary}

具体的な影響分析（200字程度）:
"""
    
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
            
            summary = response.choices[0].message.content.strip()
            return summary
            
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
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはユーザー視点でのメリットを分析するのが得意なコンサルタントです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            comment = response.choices[0].message.content.strip()
            return comment
            
        except Exception as e:
            print(f"感想生成エラー: {e}")
            # フォールバック: 簡単なコメント
            return "この技術により、ユーザーはより便利で効率的なAI体験を得ることができそうです。"
    
    def process_article(self, article: NewsArticle) -> ProcessedArticle:
        """記事を処理（要約+感想生成）"""
        print(f"記事処理中: {article.title}")
        
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
            processing_date=datetime.now().isoformat()
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
以下の{len(processed_articles)}件のAI関連記事から、1つの統合ブログ投稿を作成してください。

記事情報:
{articles_summary}

以下の形式でブログ投稿を作成してください：

1. タイトル: 魅力的で検索されやすいタイトル
2. 導入文: 今日のAI動向の概要（100字程度）
3. 各記事の紹介: 記事ごとに要約と感想を含めて紹介
4. まとめ: 全体を通してのユーザーへのメッセージ（100字程度）

読者にとって価値のある、分かりやすい内容にしてください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは技術ブログの執筆を得意とするライターです。"},
                    {"role": "user", "content": blog_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
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
                'content': f"本日は{len(processed_articles)}件のAI関連記事をお届けします。",
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

