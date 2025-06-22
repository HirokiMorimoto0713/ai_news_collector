#!/bin/bash

# AI情報収集システム 自動セットアップスクリプト
# GCP Compute Engine Ubuntu 22.04 LTS用

set -e

echo "=== AI情報収集システム セットアップ開始 ==="

# 1. システム更新
echo "1. システム更新中..."
sudo apt update && sudo apt upgrade -y

# 2. 必要なパッケージインストール
echo "2. 必要なパッケージをインストール中..."
sudo apt install -y python3-pip git curl wget unzip

# 3. Python依存関係インストール
echo "3. Python依存関係をインストール中..."
pip3 install --user requests beautifulsoup4 openai schedule python-dotenv

# 4. プロジェクトディレクトリ作成
echo "4. プロジェクトディレクトリを作成中..."
mkdir -p /home/ubuntu/ai_news_collector
cd /home/ubuntu/ai_news_collector

# 5. 設定ファイルテンプレート作成
echo "5. 設定ファイルテンプレートを作成中..."

# .envテンプレート
cat > .env.template << 'EOF'
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

# WordPress設定テンプレート
cat > wordpress_config.json << 'EOF'
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
EOF

# システム設定
cat > system_config.json << 'EOF'
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
EOF

# 6. バックアップスクリプト作成
echo "6. バックアップスクリプトを作成中..."
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/ubuntu/backups/$DATE"

mkdir -p $BACKUP_DIR

# 設定ファイルバックアップ
cp *.json $BACKUP_DIR/ 2>/dev/null || true
cp .env $BACKUP_DIR/ 2>/dev/null || true

# ログファイルバックアップ
cp *.log $BACKUP_DIR/ 2>/dev/null || true

# 収集データバックアップ
cp daily_ai_news_*.json $BACKUP_DIR/ 2>/dev/null || true
cp processed_articles_*.json $BACKUP_DIR/ 2>/dev/null || true

# 古いバックアップ削除（30日以上）
find /home/ubuntu/backups -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh

# 7. 監視スクリプト作成
echo "7. 監視スクリプトを作成中..."
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

# 最新ログ確認
if [ -f "ai_news_system.log" ]; then
    ERROR_COUNT=$(tail -100 ai_news_system.log | grep -c "ERROR" || echo "0")
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "警告: 最近のログに多数のエラーがあります ($ERROR_COUNT件)"
    fi
fi
EOF

chmod +x monitor.sh

# 8. メンテナンススクリプト作成
echo "8. メンテナンススクリプトを作成中..."
cat > maintenance.sh << 'EOF'
#!/bin/bash

echo "=== 月次メンテナンス開始 ==="

# システム更新
sudo apt update && sudo apt upgrade -y

# Python依存関係更新
pip3 install --user --upgrade requests beautifulsoup4 openai schedule python-dotenv

# ログローテーション
find . -name "*.log" -size +10M -exec gzip {} \; 2>/dev/null || true

# 古いデータファイル削除
find . -name "daily_ai_news_*.json" -mtime +90 -delete 2>/dev/null || true
find . -name "processed_articles_*.json" -mtime +90 -delete 2>/dev/null || true

# ディスク使用量チェック
df -h

echo "=== 月次メンテナンス完了 ==="
EOF

chmod +x maintenance.sh

# 9. 権限設定
echo "9. ファイル権限を設定中..."
chmod 600 .env.template *.json
chmod 755 *.sh

# 10. ファイアウォール設定（オプション）
echo "10. ファイアウォール設定中..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw --force enable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
    echo "ファイアウォール設定完了"
else
    echo "ufw が見つかりません。手動でファイアウォールを設定してください。"
fi

# 11. 完了メッセージ
echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次の手順を実行してください:"
echo ""
echo "1. 設定ファイルの編集:"
echo "   cp .env.template .env"
echo "   nano .env  # APIキーとWordPress情報を設定"
echo "   nano wordpress_config.json  # WordPress詳細設定"
echo ""
echo "2. システムファイルの配置:"
echo "   # 提供されたPythonファイルをこのディレクトリにコピー"
echo "   # - news_collector.py"
echo "   # - twitter_collector.py"
echo "   # - integrated_collector.py"
echo "   # - article_processor.py"
echo "   # - wordpress_connector.py"
echo "   # - scheduler.py"
echo ""
echo "3. 動作テスト:"
echo "   python3 test_system.py"
echo ""
echo "4. cronジョブ設定:"
echo "   crontab -e"
echo "   # 以下を追加:"
echo "   # 0 9 * * * cd /home/ubuntu/ai_news_collector && python3 scheduler.py collect"
echo "   # 0 10 * * * cd /home/ubuntu/ai_news_collector && python3 scheduler.py workflow"
echo "   # 0 2 * * * /home/ubuntu/ai_news_collector/backup.sh"
echo "   # 0 * * * * /home/ubuntu/ai_news_collector/monitor.sh"
echo "   # 0 3 1 * * /home/ubuntu/ai_news_collector/maintenance.sh"
echo ""
echo "セットアップディレクトリ: $(pwd)"
echo ""

