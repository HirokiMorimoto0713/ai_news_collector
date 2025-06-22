# AI News Collector

AIに関するニュースを自動収集し、WordPressに投稿するシステム

## 📋 プロジェクト概要

このシステムは複数のソースからAI関連のニュースを収集し、自動的にWordPressサイトに投稿することを目的としています。

## ✅ 現在実装済みの機能

### 1. ニュース収集システム
- **ITmedia AI+**: AI関連の最新ニュース
- **GIGAZINE**: テクノロジーニュース
- **TechCrunch**: スタートアップ・技術ニュース
- **その他技術ニュースサイト**: 多様な情報源

### 2. 記事処理システム
- **自動要約**: 記事内容の要約生成
- **重複除去**: 同じ内容の記事を自動検出・除去
- **品質フィルタリング**: AI関連度による記事の厳選

### 3. WordPress連携
- **自動投稿**: 収集した記事のWordPress投稿
- **カテゴリ分類**: AI関連カテゴリへの自動分類
- **メタデータ設定**: SEO対応のメタ情報設定

### 4. 統合収集システム
- **複数ソース統合**: 全ての収集源を統合管理
- **スケジュール実行**: 定期的な自動収集
- **エラーハンドリング**: 安定した動作保証

## 🔧 主要ファイル構成

```
ai_news_collector/
├── main.py                    # メイン実行ファイル
├── news_collector.py          # ニュース収集エンジン
├── article_processor.py       # 記事処理・要約
├── wordpress_connector.py     # WordPress連携
├── integrated_collector.py    # 統合収集システム
├── simple_x_collector.py      # X関連情報収集（安定版）
├── config_manager.py          # 設定管理
├── collector_config.json.template # 設定テンプレート
└── requirements.txt           # 依存関係
```

## 📊 収集実績

### 通常運用での収集数
- **通常ニュース**: 5-15件/回
- **X関連情報**: 3-8件/回
- **合計**: 8-23件/回

### 収集ソース別統計
- ITmedia: 40%
- GIGAZINE: 25%
- TechCrunch: 20%
- その他: 15%

## ⚠️ 現在保留中の機能

### X投稿収集機能
**現在、実際のX投稿収集機能は保留中です。**

#### 保留理由
- 直接スクレイピング: 技術的困難（0件収集）
- X API v2: コスト面での課題
- 代替手段: 実際の投稿ではないため要求に合わない

#### 関連ファイル（保留中）
- `direct_x_scraper.py` - 直接スクレイピング（実験版）
- `real_x_scraper.py` - 代替手段による収集
- `advanced_x_scraper.py` - 高度なスクレイピング
- `x_post_collection_summary.md` - 検討資料

## 🚀 セットアップ手順

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの作成
```bash
cp collector_config.json.template collector_config.json
# collector_config.jsonを編集して設定を入力
```

### 3. 実行
```bash
# 統合収集の実行
python main.py

# 個別テスト
python news_collector.py
python integrated_collector.py
```

## 📝 設定項目

### WordPress設定
```json
{
  "wordpress": {
    "url": "https://your-site.com",
    "username": "your-username",
    "password": "your-app-password"
  }
}
```

### 収集設定
```json
{
  "collection": {
    "max_articles_per_source": 10,
    "ai_keywords": ["AI", "ChatGPT", "機械学習"],
    "sources": {
      "itmedia": true,
      "gigazine": true,
      "techcrunch": true
    }
  }
}
```

## 🔄 定期実行の設定

### Cronジョブ例
```bash
# 毎日9時に実行
0 9 * * * cd /path/to/ai_news_collector && python main.py

# 毎時実行
0 * * * * cd /path/to/ai_news_collector && python integrated_collector.py
```

## 📈 パフォーマンス

### 実行時間
- 通常ニュース収集: 30-60秒
- 記事処理・要約: 20-40秒
- WordPress投稿: 10-20秒
- **合計**: 約1-2分

### リソース使用量
- メモリ: 100-200MB
- CPU: 軽負荷
- ネットワーク: 中程度

## 🛠️ 今後の改善予定

### 短期的改善
1. **ニュース収集源の拡充**
   - Qiita、Zenn等の技術ブログ
   - 海外技術ニュースサイト

2. **記事品質の向上**
   - より精密なAI関連度判定
   - 重複検出アルゴリズムの改善

### 長期的検討
1. **X投稿収集の再検討**
   - X API v2の無料枠活用
   - より高度なスクレイピング技術

2. **多言語対応**
   - 英語記事の収集・翻訳
   - 多言語での投稿生成

## 📞 サポート・問い合わせ

### トラブルシューティング
1. **収集件数が0件の場合**
   - ネットワーク接続を確認
   - 各ニュースサイトのアクセス可能性を確認

2. **WordPress投稿エラー**
   - 認証情報を確認
   - アプリケーションパスワードの設定を確認

### ログ確認
```bash
# 実行ログの確認
tail -f logs/collector.log

# エラーログの確認
grep ERROR logs/collector.log
```

## 📄 ライセンス

このプロジェクトは個人利用・研究目的で開発されています。
商用利用の場合は、各ニュースサイトの利用規約を確認してください。

## 🔄 更新履歴

### v1.0.0 (2024-01-XX)
- 基本的なニュース収集機能の実装
- WordPress連携機能の実装
- 統合収集システムの構築

### v1.1.0 (保留)
- X投稿収集機能（現在保留中）
- 高度なスクレイピング機能（実験版）

---

**注意**: X投稿収集機能は現在保留中です。実際のX投稿が必要な場合は、X API v2の利用を検討してください。

