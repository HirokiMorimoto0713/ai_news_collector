# AI情報自動収集・投稿システム

毎日AI関連の最新情報を自動収集し、要約・感想を付けてWordPressに自動投稿するシステムです。

## 🚀 主な機能

- **自動情報収集**: X/Twitter、ニュースサイト、技術ブログからAI関連情報を収集
- **AI要約・感想生成**: OpenAI APIを使用した300字要約と「ユーザー価値」視点での感想生成
- **WordPress自動投稿**: 既存のWordPressシステムと連携した自動投稿
- **SEOフレンドリーなスラッグ自動生成**: 日本語タイトルから英語スラッグを自動生成
- **重複除外**: 同一記事の重複投稿を防止
- **スケジュール実行**: 毎日9時収集、10時投稿の自動化

## 📋 システム要件

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **環境**: GCP Compute Engine (推奨)
- **必要なAPI**: OpenAI API、WordPress REST API

## 🛠️ クイックスタート

### 1. 自動セットアップ

```bash
# セットアップスクリプト実行
curl -sSL https://raw.githubusercontent.com/your-repo/ai-news-collector/main/setup.sh | bash
```

### 2. 設定ファイル編集

```bash
cd /home/ubuntu/ai_news_collector

# 環境変数設定
cp .env.template .env
nano .env  # APIキーとWordPress情報を設定

# WordPress設定
nano wordpress_config.json
```

### 3. システムファイル配置

以下のファイルをプロジェクトディレクトリにコピー:
- `news_collector.py`
- `twitter_collector.py`
- `integrated_collector.py`
- `article_processor.py`
- `wordpress_connector.py`
- `scheduler.py`
- `test_system.py`

### 4. 動作テスト

```bash
# システムテスト実行
python3 test_system.py

# 手動実行テスト
python3 scheduler.py workflow
```

### 5. cronジョブ設定

```bash
crontab -e

# 以下を追加
0 9 * * * cd /home/ubuntu/ai_news_collector && python3 scheduler.py collect
0 10 * * * cd /home/ubuntu/ai_news_collector && python3 scheduler.py workflow
0 2 * * * /home/ubuntu/ai_news_collector/backup.sh
```

## 📁 ファイル構成

```
ai_news_collector/
├── news_collector.py          # 基本情報収集モジュール
├── twitter_collector.py       # X/Twitter収集モジュール
├── integrated_collector.py    # 統合収集システム
├── article_processor.py       # 記事要約・感想生成
├── wordpress_connector.py     # WordPress連携
├── scheduler.py               # スケジュール実行
├── test_system.py            # システムテスト
├── setup.sh                  # 自動セットアップ
├── requirements.txt          # Python依存関係
├── .env                      # 環境変数（要設定）
├── wordpress_config.json     # WordPress設定
├── system_config.json        # システム設定
├── backup.sh                 # バックアップスクリプト
├── monitor.sh                # 監視スクリプト
├── maintenance.sh            # メンテナンススクリプト
└── DEPLOYMENT_GUIDE.md       # 詳細デプロイガイド
```

## ⚙️ 設定項目

### 環境変数 (.env)

```bash
OPENAI_API_KEY=your_openai_api_key_here
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_app_password
```

### WordPress設定 (wordpress_config.json)

```json
{
  "wp_url": "https://your-wordpress-site.com",
  "wp_user": "your_wp_username",
  "wp_app_pass": "your_wp_app_password",
  "post_settings": {
    "status": "publish",
    "category_id": 1,
    "tags": ["AI", "技術動向", "最新情報"],
    "author_id": 1,
    "featured_media": null
  },
  "slug_settings": {
    "auto_generate": true,
    "prefix": "ai-news-",
    "max_length": 50
  }
}
```

#### スラッグ設定の説明

- **auto_generate**: スラッグ自動生成の有効/無効
- **prefix**: スラッグの前に付けるプレフィックス（例: "ai-news-"）
- **max_length**: スラッグの最大長（デフォルト: 50文字）

## 🔤 スラッグ自動生成機能

### 概要

WordPress投稿時に、日本語タイトルから自動的にSEOフレンドリーな英語スラッグを生成します。

### 機能詳細

- **日本語→英語変換**: 100以上のAI・技術関連用語を自動変換
- **特殊文字処理**: 記号や括弧を適切にハイフンに変換
- **長さ制限**: 設定可能な最大長でスラッグを制限
- **プレフィックス対応**: カテゴリ別のプレフィックス設定可能

### 変換例

| 日本語タイトル | 生成されるスラッグ |
|---|---|
| 今日のAIニュース 2024年1月15日 | ai-news-today-ainews-2024-1-15 |
| OpenAIが新しいGPT-5を発表 | ai-news-openai-gpt-5-announcement |
| Google、AI検索機能をアップデート | ai-news-google-aisearch-feature-update |

### 設定方法

`wordpress_config.json`の`slug_settings`で設定:

```json
{
  "slug_settings": {
    "auto_generate": true,        // 自動生成を有効にする
    "prefix": "ai-news-",        // 全スラッグに付けるプレフィックス
    "max_length": 50             // スラッグの最大長
  }
}
```

## 🔧 使用方法

### 🎯 推奨: 新しい統合投稿システム

```bash
# テスト実行（投稿はしない）
python3 daily_publisher.py --test

# 実際の記事収集・処理・投稿
python3 daily_publisher.py
```

### 従来の手動実行

```bash
# 情報収集のみ
python3 scheduler.py collect

# 全ワークフロー（収集+処理+投稿）
python3 scheduler.py workflow

# スケジューラー起動
python3 scheduler.py schedule
```

### ログ確認

```bash
# システムログ
tail -f ai_news_system.log

# cronログ
tail -f cron.log
```

## 💰 運用費用

### GCP Compute Engine
- **e2-micro**: 月額 $6-8 (無料枠適用時 $0)
- **ディスク**: 10GB 約 $1.60/月

### API使用料
- **OpenAI API**: 月額 $1.50-3.00 (1日5記事想定)

**合計**: 月額 $8-13 (無料枠適用時 $3-5)

## 🛡️ セキュリティ

- 設定ファイルの権限制限 (600)
- ファイアウォール設定
- 定期的なセキュリティ更新
- APIキーの安全な管理

## 📊 監視・保守

### 自動監視
- ディスク使用量チェック
- メモリ使用量チェック
- エラーログ監視
- プロセス監視

### 定期メンテナンス
- システム更新 (月次)
- ログローテーション
- 古いデータ削除
- バックアップ実行

## 🔍 トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   - APIキー確認
   - 使用量制限確認
   - ダミー処理モードで一時運用

2. **WordPress接続エラー**
   - アプリケーションパスワード再生成
   - REST API有効化確認

3. **情報収集エラー**
   - ネットワーク接続確認
   - User-Agentヘッダー調整

## 📈 拡張・カスタマイズ

### 新しい情報源追加
`news_collector.py`の`collect_from_news_sites`メソッドを拡張

### 投稿フォーマット変更
`wordpress_connector.py`の`format_article_for_post`メソッドを修正

### 通知機能追加
Slack/Discord Webhook連携

## 📚 詳細ドキュメント

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 詳細なデプロイメントガイド
- [test_report.json](test_report.json) - システムテスト結果

## 📞 サポート

- **対応範囲**: インストール、設定、基本的なトラブルシューティング
- **除外事項**: カスタム開発、第三者API問題

## 📄 ライセンス

個人利用・商用利用ともに可能です。
第三者APIの利用規約に従ってご利用ください。

---

**注意事項**: 
- 各種APIの利用規約を遵守してください
- 情報収集時は対象サイトの負荷を考慮してください
- 定期的なバックアップを推奨します

