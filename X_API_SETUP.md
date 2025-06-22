# X API v2 設定手順ガイド

## 🚀 概要
このガイドでは、X API v2 Free プランを使用して実際のX投稿を収集する設定手順を説明します。

## 📋 必要な手順

### Step 1: X Developer Account作成

1. **X Developer Portal にアクセス**
   - URL: https://developer.x.com/
   - 「Sign up」または「Apply」をクリック

2. **既存のXアカウントでログイン**
   - Xアカウントが必要です（なければ先に作成）

3. **開発者アカウント申請フォーム記入**
   ```
   使用目的: AI関連ニュース収集・分析
   プロジェクト名: AI News Collector
   説明: AIニュースの自動収集とWordPress投稿システム
   ```

### Step 2: プロジェクト・アプリ作成

1. **Developer Portal でプロジェクト作成**
   - 「Create Project」をクリック
   - プロジェクト名: `ai-news-collector`

2. **アプリ作成**
   - 「Create App」をクリック
   - アプリ名: `ai-news-app`

### Step 3: API認証情報取得

以下の5つの認証情報を取得してください：

1. **API Key** (Consumer Key)
2. **API Secret** (Consumer Secret)
3. **Bearer Token**
4. **Access Token**
5. **Access Token Secret**

### Step 4: 環境変数設定

取得した認証情報を以下の形式で `.env` ファイルに追加：

```bash
# X (Twitter) API設定
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_BEARER_TOKEN=your_bearer_token_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

## 💰 X API Free プラン制限

- **月間投稿取得上限**: 500投稿
- **料金**: 無料
- **機能**: 基本的な検索・投稿取得

## 🧪 テスト実行

認証情報設定後、以下でテスト可能：

```bash
python3 x_api_collector.py
```

## 🔧 統合テスト

X API を有効にして記事収集テスト：

```bash
python3 -c "
import asyncio
from twitter_collector import collect_twitter_articles

async def test():
    articles = await collect_twitter_articles(use_api=True, max_articles=3)
    print(f'収集: {len(articles)}件')
    
asyncio.run(test())
"
```

## ⚠️ 注意事項

1. **API制限**: 月500投稿まで（Free プラン）
2. **レート制限**: 15分間に最大180リクエスト
3. **データ品質**: 実際のX投稿データで高品質
4. **安定性**: 公式APIなので安定

## 🆘 トラブルシューティング

### 認証エラーの場合
- `.env` ファイルの認証情報を再確認
- API Key/Secret が正しいか確認

### 投稿が取得できない場合
- 検索キーワードを調整
- 時間範囲を拡大（24時間→48時間）

### 月間制限に達した場合
- Basic プラン（$200/月）への移行を検討
- 代替手段（ニュースサイト収集）を使用

## 📞 サポート

設定完了後、以下の情報をお知らせください：
- 認証情報設定完了の確認
- テスト実行結果
- エラーメッセージ（もしあれば） 