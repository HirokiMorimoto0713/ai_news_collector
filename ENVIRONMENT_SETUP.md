# 環境変数設定ガイド

## 必要な環境変数

このアプリケーションを実行するには、以下の環境変数を設定する必要があります：

### OpenAI API設定
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### WordPress設定
```bash
export WP_URL="https://your-wordpress-site.com"
export WP_USER="your_wp_username"
export WP_APP_PASS="your_wp_application_password"
```

## 設定方法

### 1. 一時的な設定（現在のセッションのみ）
```bash
export OPENAI_API_KEY="sk-..."
export WP_URL="https://ai-gene.jp"
export WP_USER="APIUSER"
export WP_APP_PASS="Ah3J norO VGMu wrnk Wb3p 4IDt"
```

### 2. 永続的な設定（推奨）
`.bashrc` または `.zshrc` ファイルに追加：
```bash
echo 'export OPENAI_API_KEY="your_key_here"' >> ~/.bashrc
echo 'export WP_URL="https://your-site.com"' >> ~/.bashrc
echo 'export WP_USER="your_username"' >> ~/.bashrc
echo 'export WP_APP_PASS="your_app_password"' >> ~/.bashrc
source ~/.bashrc
```

### 3. .envファイルを使用（開発環境）
プロジェクトルートに `.env` ファイルを作成：
```
OPENAI_API_KEY=your_openai_api_key_here
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_application_password
```

## 設定の確認
```bash
echo $OPENAI_API_KEY
echo $WP_URL
echo $WP_USER
echo $WP_APP_PASS
```

## セキュリティ注意事項
- APIキーや認証情報は絶対にGitリポジトリにコミットしないでください
- `.env` ファイルは `.gitignore` に追加してください
- 本番環境では適切な権限管理を行ってください 