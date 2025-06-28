# AI News Collector

AIに関するニュースを自動収集し、WordPressに投稿するシステム

## 🔗 GitHubリポジトリ

**メインリポジトリ**: [https://github.com/HirokiMorimoto0713/ai_news_collector](https://github.com/HirokiMorimoto0713/ai_news_collector)

## 📋 プロジェクト概要

このシステムは複数のソースからAI関連のニュースを収集し、自動的にWordPressサイトに投稿することを目的としています。

## 🔄 リファクタリング版について

**NEW**: リファクタリング版が利用可能です！

### リファクタリング版の特徴
- **モジュール化された構造**: `src/core/`, `src/utils/` ディレクトリ
- **統一設定管理**: JSON形式の設定ファイル (`config/`)
- **カラー対応ログ**: 詳細な実行ログとエラー追跡
- **型安全性**: 完全な型ヒント対応
- **強化されたエラーハンドリング**: カスタム例外とグレースフル処理

### 使用方法
```bash
# リファクタリング版の実行
python main_refactored.py

# 従来版（互換性維持）
python main.py
```

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
- **アイキャッチ画像生成**: DALL·E 3によるアイキャッチ画像の自動生成
- **カテゴリ分類**: AI関連カテゴリへの自動分類
- **メタデータ設定**: SEO対応のメタ情報設定

### 4. 統合収集システム
- **複数ソース統合**: 全ての収集源を統合管理
- **スケジュール実行**: 定期的な自動収集
- **エラーハンドリング**: 安定した動作保証

## 🔧 主要ファイル構成

```
ai_news_collector/
├── main.py                    # メイン実行ファイル（従来版）
├── main_refactored.py         # メイン実行ファイル（リファクタリング版）
├── news_collector.py          # ニュース収集エンジン
├── article_processor.py       # 記事処理・要約
├── wordpress_connector.py     # WordPress連携
├── integrated_collector.py    # 統合収集システム
├── src/                       # リファクタリング版モジュール
│   ├── core/                  # コアモジュール
│   │   ├── config.py         # 設定管理
│   │   ├── logger.py         # ログシステム
│   │   ├── models.py         # データモデル
│   │   └── exceptions.py     # カスタム例外
│   └── utils/                 # ユーティリティ
│       ├── http_client.py    # HTTP通信
│       ├── text_utils.py     # テキスト処理
│       ├── file_utils.py     # ファイル操作
│       └── date_utils.py     # 日付処理
├── config/                    # 設定ファイル（自動生成）
│   ├── openai.json           # OpenAI API設定
│   ├── wordpress.json        # WordPress設定
│   ├── collection.json       # 収集設定
│   └── system.json           # システム設定
├── requirements.txt           # 依存関係（従来版）
├── requirements_refactored.txt # 依存関係（リファクタリング版）
└── README_REFACTORED.md       # リファクタリング版詳細説明
```

## 🚀 セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/HirokiMorimoto0713/ai_news_collector.git
cd ai_news_collector
```

### 2. 依存関係のインストール

#### 従来版
```bash
pip install -r requirements.txt
```

#### リファクタリング版（推奨）
```bash
pip install -r requirements_refactored.txt
```

### 3. 設定ファイルの作成

#### 従来版
```bash
cp collector_config.json.template collector_config.json
# collector_config.jsonを編集して設定を入力
```

#### リファクタリング版
```bash
# 初回実行で設定ファイルが自動生成されます
python main_refactored.py
# config/ ディレクトリ内の設定ファイルを編集
```

### 4. 実行

#### 従来版
```bash
# 統合収集の実行
python main.py

# 個別テスト
python news_collector.py
python integrated_collector.py
```

#### リファクタリング版
```bash
# リファクタリング版の実行
python main_refactored.py
```

## 📝 設定項目

### WordPress設定
```json
{
  "wp_url": "https://your-site.com",
  "wp_user": "your-username",
  "wp_app_pass": "your-app-password",
  "post_settings": {
    "status": "publish",
    "category_id": 1,
    "tags": ["AI", "技術動向", "最新情報"],
    "author_id": 1,
    "generate_featured_image": true
  }
}
```

### OpenAI設定（アイキャッチ画像生成用）
環境変数または設定ファイルで設定：
```bash
OPENAI_API_KEY=your_openai_api_key
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
# 従来版: 毎日9時に実行
0 9 * * * cd /path/to/ai_news_collector && python main.py

# リファクタリング版: 毎日12時に実行
0 12 * * * cd /path/to/ai_news_collector && python main_refactored.py
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
# 従来版: 実行ログの確認
tail -f logs/collector.log

# リファクタリング版: カラー対応ログの確認
tail -f logs/ai_news_collector.log

# エラーログの確認
grep ERROR logs/*.log
```

## 📄 ライセンス

このプロジェクトは個人利用・研究目的で開発されています。
商用利用の場合は、各ニュースサイトの利用規約を確認してください。

## 🔄 更新履歴

### v2.0.0 (2024-06-XX) - リファクタリング版
- モジュール化されたアーキテクチャ
- 統一設定管理システム
- カラー対応ログシステム
- 型安全性の向上
- 強化されたエラーハンドリング

### v1.0.0 (2024-01-XX)
- 基本的なニュース収集機能の実装
- WordPress連携機能の実装
- 統合収集システムの構築

### v1.1.0 (保留)
- X投稿収集機能（現在保留中）
- 高度なスクレイピング機能（実験版）

---

**注意**: X関連情報収集機能は完全に無効化されています。システムはニュースサイトからの情報収集のみに特化しています。

