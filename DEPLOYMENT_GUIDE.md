# AI情報自動収集・投稿システム デプロイメントガイド

## 概要

このシステムは、毎日AI関連の最新情報を自動収集し、要約・感想を付けてWordPressに自動投稿するシステムです。GCP Compute Engineでの運用を想定して設計されています。

## システム構成

### 主要コンポーネント

1. **情報収集モジュール** (`integrated_collector.py`)
   - X/Twitter、ニュースサイト、技術ブログからAI関連情報を収集
   - 重複除外機能付き

2. **記事処理モジュール** (`article_processor.py`)
   - OpenAI APIを使用した300字要約生成
   - ユーザー価値視点での感想生成

3. **WordPress連携モジュール** (`wordpress_connector.py`)
   - WordPress REST APIを使用した自動投稿
   - 既存システムとの互換性

4. **スケジューラー** (`scheduler.py`)
   - 毎日9時に情報収集、10時に投稿
   - cronジョブとしての実行

### 技術スタック

- **言語**: Python 3.11+
- **主要ライブラリ**: 
  - requests (HTTP通信)
  - beautifulsoup4 (Webスクレイピング)
  - openai (AI処理)
  - schedule (スケジュール実行)
- **デプロイ環境**: GCP Compute Engine
- **連携システム**: WordPress (REST API)

## 前提条件

### 必要なAPIキー・認証情報

1. **OpenAI APIキー**
   - ChatGPT APIアクセス用
   - 月額使用量の目安: $10-30

2. **WordPress認証情報**
   - WordPressサイトURL
   - ユーザー名
   - アプリケーションパスワード

3. **X/Twitter認証情報** (オプション)
   - API使用する場合のみ必要
   - 代替手段も実装済み

### GCP環境要件

- **インスタンスタイプ**: e2-micro (無料枠対応)
- **OS**: Ubuntu 22.04 LTS
- **ディスク**: 10GB (標準永続ディスク)
- **ネットワーク**: HTTP/HTTPS通信許可



## GCP Compute Engine セットアップ手順

### 1. インスタンス作成

```bash
# gcloudコマンドでインスタンス作成
gcloud compute instances create ai-news-collector \
    --zone=asia-northeast1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,https-server
```

### 2. ファイアウォール設定

```bash
# HTTP/HTTPS通信を許可
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server
```

### 3. インスタンスへの接続

```bash
# SSH接続
gcloud compute ssh ai-news-collector --zone=asia-northeast1-a
```

## システムインストール手順

### 1. 基本環境セットアップ

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# Python環境確認
python3 --version
pip3 --version

# 必要なシステムパッケージインストール
sudo apt install -y git curl wget unzip
```

### 2. プロジェクトファイルの配置

```bash
# プロジェクトディレクトリ作成
mkdir -p /home/ubuntu/ai_news_collector
cd /home/ubuntu/ai_news_collector

# ファイルをアップロード（以下のいずれかの方法）
# 方法1: scpでファイル転送
# 方法2: GitHubリポジトリからクローン
# 方法3: 手動でファイル作成
```

### 3. Python依存関係インストール

```bash
# 依存関係インストール
pip3 install -r requirements.txt

# インストール確認
pip3 list | grep -E "(requests|beautifulsoup4|openai|schedule)"
```

## 設定ファイル構成

### 1. 環境変数設定

```bash
# .envファイル作成
cat > .env << EOF
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# WordPress設定
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_app_password

# その他設定
TIMEZONE=Asia/Tokyo
LOG_LEVEL=INFO
EOF

# 権限設定
chmod 600 .env
```

### 2. WordPress設定ファイル

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
  }
}
```

### 3. システム設定ファイル

```json
{
  "schedule": {
    "collection_time": "09:00",
    "posting_time": "10:00",
    "timezone": "Asia/Tokyo"
  },
  "duplicate_prevention": {
    "enabled": true,
    "history_days": 30,
    "similarity_threshold": 0.8
  },
  "error_handling": {
    "max_retries": 3,
    "retry_delay_minutes": 5,
    "notification_email": null
  },
  "logging": {
    "level": "INFO",
    "file": "ai_news_system.log",
    "max_size_mb": 10
  }
}
```


## cronジョブ設定

### 1. cronジョブの設定

```bash
# crontabを編集
crontab -e

# 以下の行を追加
# 毎日9時に情報収集
0 9 * * * cd /home/ubuntu/ai_news_collector && /usr/bin/python3 scheduler.py collect >> /home/ubuntu/ai_news_collector/cron.log 2>&1

# 毎日10時に全ワークフロー実行（収集+処理+投稿）
0 10 * * * cd /home/ubuntu/ai_news_collector && /usr/bin/python3 scheduler.py workflow >> /home/ubuntu/ai_news_collector/cron.log 2>&1
```

### 2. cronジョブの確認

```bash
# 設定確認
crontab -l

# ログ確認
tail -f /home/ubuntu/ai_news_collector/cron.log
```

### 3. 手動実行テスト

```bash
# 情報収集のみテスト
python3 scheduler.py collect

# 全ワークフローテスト
python3 scheduler.py workflow

# スケジューラー起動テスト（Ctrl+Cで停止）
python3 scheduler.py schedule
```

## 運用・監視

### 1. ログ監視

```bash
# システムログ確認
tail -f ai_news_system.log

# cronログ確認
tail -f cron.log

# エラーログ検索
grep -i error ai_news_system.log
```

### 2. 動作確認

```bash
# 収集された記事確認
ls -la daily_ai_news_*.json

# 処理済み記事確認
ls -la processed_articles_*.json

# WordPress投稿ログ確認
ls -la wordpress_post_log_*.json
```

### 3. システム状態確認

```bash
# プロセス確認
ps aux | grep python3

# ディスク使用量確認
df -h

# メモリ使用量確認
free -h
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. OpenAI API エラー

**症状**: 記事処理でエラーが発生
```
OpenAI API エラー: Rate limit exceeded
```

**解決方法**:
- APIキーの使用量制限を確認
- リクエスト間隔を調整
- ダミー処理モードで一時的に運用

#### 2. WordPress接続エラー

**症状**: WordPress投稿に失敗
```
WordPress接続エラー: 401 Unauthorized
```

**解決方法**:
- アプリケーションパスワードの再生成
- WordPressサイトのREST API有効化確認
- ファイアウォール設定確認

#### 3. 情報収集エラー

**症状**: 記事が収集されない
```
収集された記事がありません
```

**解決方法**:
- ネットワーク接続確認
- 対象サイトのアクセス制限確認
- User-Agentヘッダーの調整

#### 4. cronジョブが動作しない

**症状**: スケジュール実行されない

**解決方法**:
```bash
# cronサービス状態確認
sudo systemctl status cron

# cronサービス再起動
sudo systemctl restart cron

# 絶対パスで指定
which python3  # パス確認
```

### ログレベル調整

```bash
# デバッグモードで実行
export LOG_LEVEL=DEBUG
python3 scheduler.py workflow
```

## セキュリティ設定

### 1. ファイル権限設定

```bash
# 設定ファイルの権限制限
chmod 600 .env
chmod 600 wordpress_config.json
chmod 600 twitter_credentials.json

# 実行ファイルの権限設定
chmod 755 *.py
```

### 2. ファイアウォール設定

```bash
# 不要なポートを閉じる
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 3. 定期的なセキュリティ更新

```bash
# 自動更新設定
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```


## 費用見積もり

### GCP Compute Engine 費用

**e2-microインスタンス（推奨）**
- 月額: 約 $6-8 (無料枠適用時は $0)
- vCPU: 0.25-1.0
- メモリ: 1GB
- ディスク: 10GB ($1.60/月)

**合計月額**: 約 $7-10 (無料枠適用時は約 $2)

### API使用料

**OpenAI API (GPT-3.5-turbo)**
- 1日5記事 × 30日 = 150記事/月
- 1記事あたり約 $0.01-0.02
- 月額: 約 $1.50-3.00

**合計運用費用**: 月額 $8-13 (無料枠適用時は $3-5)

## バックアップ・復旧

### 1. データバックアップ

```bash
# 日次バックアップスクリプト
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/ubuntu/backups/$DATE"

mkdir -p $BACKUP_DIR

# 設定ファイルバックアップ
cp *.json $BACKUP_DIR/
cp .env $BACKUP_DIR/

# ログファイルバックアップ
cp *.log $BACKUP_DIR/

# 収集データバックアップ
cp daily_ai_news_*.json $BACKUP_DIR/ 2>/dev/null || true
cp processed_articles_*.json $BACKUP_DIR/ 2>/dev/null || true

# 古いバックアップ削除（30日以上）
find /home/ubuntu/backups -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh

# cronに追加
echo "0 2 * * * /home/ubuntu/ai_news_collector/backup.sh" | crontab -
```

### 2. システム復旧手順

```bash
# 1. 最新バックアップから復旧
LATEST_BACKUP=$(ls -1 /home/ubuntu/backups | tail -1)
cp /home/ubuntu/backups/$LATEST_BACKUP/* /home/ubuntu/ai_news_collector/

# 2. 権限復旧
chmod 600 .env *.json
chmod 755 *.py

# 3. 依存関係再インストール
pip3 install -r requirements.txt

# 4. 動作確認
python3 test_system.py
```

## 拡張・カスタマイズ

### 1. 新しい情報源の追加

`news_collector.py`の`collect_from_news_sites`メソッドを拡張:

```python
def collect_from_new_source(self) -> List[NewsArticle]:
    """新しい情報源からの収集"""
    articles = []
    
    try:
        # 新しいサイトのスクレイピング処理
        url = "https://new-ai-news-site.com"
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 記事抽出ロジック
        # ...
        
    except Exception as e:
        print(f"新しい情報源収集エラー: {e}")
    
    return articles
```

### 2. 投稿フォーマットのカスタマイズ

`wordpress_connector.py`の`format_article_for_post`メソッドを修正:

```python
def format_article_for_post(self, processed_article: ProcessedArticle) -> str:
    """カスタム投稿フォーマット"""
    # 独自のHTMLテンプレート
    template = """
    <div class="ai-news-article">
        <h3 class="article-title">{title}</h3>
        <div class="article-meta">
            <span class="source">{source}</span>
            <span class="date">{date}</span>
        </div>
        <div class="article-summary">{summary}</div>
        <div class="user-value">{user_value}</div>
        <a href="{url}" class="read-more">続きを読む</a>
    </div>
    """
    
    return template.format(
        title=processed_article.original_article.title,
        source=processed_article.original_article.source,
        date=datetime.now().strftime('%Y年%m月%d日'),
        summary=processed_article.summary,
        user_value=processed_article.user_value_comment,
        url=processed_article.original_article.url
    )
```

### 3. 通知機能の追加

```python
def send_notification(self, message: str):
    """Slack/Discord通知"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if webhook_url:
        payload = {'text': message}
        requests.post(webhook_url, json=payload)
```

## 保守・更新

### 1. 定期メンテナンス

```bash
# 月次メンテナンススクリプト
cat > maintenance.sh << 'EOF'
#!/bin/bash

echo "=== 月次メンテナンス開始 ==="

# システム更新
sudo apt update && sudo apt upgrade -y

# Python依存関係更新
pip3 install --upgrade -r requirements.txt

# ログローテーション
find . -name "*.log" -size +10M -exec gzip {} \;

# 古いデータファイル削除
find . -name "daily_ai_news_*.json" -mtime +90 -delete
find . -name "processed_articles_*.json" -mtime +90 -delete

# ディスク使用量チェック
df -h

echo "=== 月次メンテナンス完了 ==="
EOF

chmod +x maintenance.sh

# 月初実行
echo "0 3 1 * * /home/ubuntu/ai_news_collector/maintenance.sh" | crontab -
```

### 2. システム監視

```bash
# 監視スクリプト
cat > monitor.sh << 'EOF'
#!/bin/bash

# ディスク使用量チェック
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "警告: ディスク使用量が80%を超えています ($DISK_USAGE%)"
fi

# メモリ使用量チェック
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "警告: メモリ使用量が90%を超えています ($MEMORY_USAGE%)"
fi

# プロセス確認
if ! pgrep -f "scheduler.py" > /dev/null; then
    echo "警告: スケジューラープロセスが動作していません"
fi

# 最新ログ確認
if [ -f "ai_news_system.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR" ai_news_system.log | tail -100)
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "警告: 最近のログに多数のエラーがあります ($ERROR_COUNT件)"
    fi
fi
EOF

chmod +x monitor.sh

# 1時間ごとに監視
echo "0 * * * * /home/ubuntu/ai_news_collector/monitor.sh" | crontab -
```

## サポート・連絡先

### 技術サポート

- **システム設計**: AI情報収集・投稿システム
- **対応範囲**: インストール、設定、基本的なトラブルシューティング
- **除外事項**: カスタム開発、第三者API問題

### 更新履歴

- **v1.0.0** (2025-06-14): 初回リリース
  - 基本的な情報収集・投稿機能
  - WordPress連携
  - スケジュール実行

### ライセンス

このシステムは個人利用・商用利用ともに可能です。
第三者APIの利用規約に従ってご利用ください。

---

**注意事項**: 
- 各種APIの利用規約を遵守してください
- 情報収集時は対象サイトの負荷を考慮してください
- 定期的なバックアップを推奨します

