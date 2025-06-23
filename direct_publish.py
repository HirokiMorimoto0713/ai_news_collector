#!/usr/bin/env python3
"""
直接投稿スクリプト
収集した記事を処理してWordPressに投稿
"""

import json
import os
from datetime import datetime
from typing import List

from news_collector import NewsArticle
from article_processor import ArticleProcessor
from wordpress_connector import WordPressConnector, DailyPostGenerator

def create_sample_articles() -> List[NewsArticle]:
    """サンプル記事を作成（収集した記事の代替）"""
    articles = [
        NewsArticle(
            title="生成AIで業務改善を実現する方法と効果的な活用ポイント",
            url="https://ascii.jp/elem/000/004/281/4281502/",
            content="生成AIを活用した業務改善は、多くの企業にとって重要な課題となっています。適切な活用方法を理解することで、効率的な業務改善を実現できます。本記事では、生成AIを用いた具体的な業務改善手法について詳しく解説します。",
            source="ascii"
        ),
        NewsArticle(
            title="IT技術者の生成AI「実装経験」はまだ少数／日本人の70％が感じる「国の衰退」",
            url="https://ascii.jp/elem/000/004/293/4293667/",
            content="最新の調査によると、IT技術者の生成AI実装経験はまだ限定的であることが判明しました。一方で、日本人の約70%が国の技術的衰退を感じているという興味深い結果も明らかになっています。",
            source="ascii"
        ),
        NewsArticle(
            title="教皇レオ14世、グーグルやMetaなどIT大手に「倫理的AIの枠組み」求める",
            url="https://japan.cnet.com/article/35234605/",
            content="教皇レオ14世は、GoogleやMetaなどの主要IT企業に対して、AI技術の倫理的な使用に関する明確なガイドラインの策定を求めました。この発言は、AI技術の社会的影響に対する宗教界の懸念を反映しています。",
            source="cnet_japan"
        ),
        NewsArticle(
            title="AI検索のPerplexityにBBCが「法的措置」警告、コンテンツの「逐語的」複製で",
            url="https://japan.cnet.com/article/35234591/",
            content="BBCは、AI検索エンジンのPerplexityに対して、BBCのコンテンツを逐語的に複製していることを理由に法的措置を警告しました。この問題は、AI技術と著作権保護の間の複雑な関係を浮き彫りにしています。",
            source="cnet_japan"
        ),
        NewsArticle(
            title="なぜ、あなたはChatGPTに「ハマってしまう」のか--気持ちよくなる仕組みを専門家が解明",
            url="https://japan.cnet.com/article/35234528/",
            content="専門家の研究により、ChatGPTが人々を魅了する心理的メカニズムが明らかになりました。対話型AIの持つ特殊な性質が、ユーザーに快感を与える仕組みについて詳しく解説されています。",
            source="cnet_japan"
        )
    ]
    return articles

def main():
    """メイン処理"""
    print("=== 直接投稿システム開始 ===")
    
    # WordPress接続の確認
    wp_connector = WordPressConnector()
    if not wp_connector.test_connection():
        print("WordPress接続に失敗しました")
        return
    
    # 記事を作成
    articles = create_sample_articles()
    print(f"処理対象記事: {len(articles)}件")
    
    # 記事処理
    processor = ArticleProcessor()
    processed_articles = []
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] 処理中: {article.title[:50]}...")
        try:
            processed = processor.process_article(article)
            processed_articles.append(processed)
            print("✅ 処理完了")
        except Exception as e:
            print(f"❌ 処理失敗: {e}")
    
    print(f"\n=== 処理完了: {len(processed_articles)}/{len(articles)}件成功 ===")
    
    if not processed_articles:
        print("投稿する記事がありません")
        return
    
    # WordPress投稿
    post_generator = DailyPostGenerator(wp_connector)
    post_info = post_generator.publish_daily_post(processed_articles)
    
    if post_info:
        print(f"\n🎉 投稿成功!")
        print(f"📝 投稿URL: {post_info['link']}")
        print(f"📊 記事数: {len(processed_articles)}件")
    else:
        print("\n❌ 投稿失敗")

if __name__ == "__main__":
    main() 