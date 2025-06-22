# twitterapi.io 設定ガイド

## 概要

twitterapi.ioは、X（Twitter）APIの代替サービスで、レート制限が緩く、安定したX投稿収集を提供します。

## 特徴

- ✅ **レート制限が緩い**: 公式X APIよりも制限が少ない
- ✅ **安定性**: 高い稼働率と信頼性
- ✅ **シンプル**: 簡単な認証とAPI構造
- ✅ **コスト効率**: 無料プランでも十分な機能

## セットアップ手順

### 1. アカウント作成

1. [twitterapi.io](https://twitterapi.io/) にアクセス
2. 「Sign Up」をクリックしてアカウント作成
3. メールアドレスとパスワードを入力
4. メール認証を完了

### 2. APIキー取得

1. ダッシュボードにログイン
2. 「API Keys」セクションに移動
3. 「Create New API Key」をクリック
4. APIキーをコピーして保存

### 3. プラン選択

#### 無料プラン (Free Tier)
- 月間 10,000 リクエスト
- 基本的な検索機能
- 24時間サポート

#### 有料プラン (Pro/Enterprise)
- より多くのリクエスト
- 高度な検索オプション
- 優先サポート

### 4. 環境変数設定

`.env` ファイルに以下を追加：

```bash
# twitterapi.io 設定
TWITTERAPI_IO_KEY=your_twitterapi_io_api_key_here
```

### 5. 動作確認

```bash
python3 twitterapi_io_collector.py
```

## API仕様

### エンドポイント

- **ベースURL**: `https://api.twitterapi.io/v1`
- **検索**: `/tweets/search/recent`
- **認証**: Bearer Token

### リクエスト例

```python
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

params = {
    'query': 'AI -is:retweet -is:reply lang:ja',
    'max_results': 10,
    'since': '2024-01-01',
    'tweet.fields': 'created_at,public_metrics,author_id',
    'user.fields': 'username,name,verified',
    'expansions': 'author_id'
}
```

### レスポンス形式

```json
{
  "data": [
    {
      "id": "1234567890",
      "text": "AI技術の最新動向について...",
      "created_at": "2024-01-01T12:00:00.000Z",
      "author_id": "987654321",
      "public_metrics": {
        "like_count": 42,
        "retweet_count": 15,
        "reply_count": 8
      }
    }
  ],
  "includes": {
    "users": [
      {
        "id": "987654321",
        "username": "ai_expert",
        "name": "AI Expert"
      }
    ]
  }
}
```

## トラブルシューティング

### よくある問題

#### 1. 認証エラー
```
Error: 401 Unauthorized
```
**解決方法**: APIキーが正しく設定されているか確認

#### 2. レート制限
```
Error: 429 Too Many Requests
```
**解決方法**: しばらく待ってから再試行、またはプランをアップグレード

#### 3. 検索結果なし
```
Warning: No tweets found
```
**解決方法**: 検索クエリを調整、時間範囲を拡大

### デバッグ方法

1. **APIキー確認**:
   ```bash
   echo $TWITTERAPI_IO_KEY
   ```

2. **手動テスト**:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        "https://api.twitterapi.io/v1/tweets/search/recent?query=AI"
   ```

3. **ログ確認**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## 統合システムでの使用

### 設定ファイル

`collector_config.json`:
```json
{
  "sources": {
    "twitter": {
      "enabled": true,
      "use_api": true,
      "api_provider": "twitterapi_io",
      "max_articles": 5,
      "min_likes": 5
    }
  }
}
```

### 優先順序

1. **twitterapi.io** (最優先)
2. **X API v2** (フォールバック)
3. **代替手段** (API無効時のみ)

## コスト管理

### 使用量監視

- ダッシュボードで月間使用量を確認
- アラート設定で上限に近づいたら通知
- ログでリクエスト数を追跡

### 最適化のヒント

- 検索クエリを絞り込む
- 不要なフィールドを除外
- キャッシュを活用
- バッチ処理で効率化

## サポート

- **公式ドキュメント**: https://docs.twitterapi.io/
- **サポートチケット**: ダッシュボードから作成
- **コミュニティ**: Discord/Slack チャンネル 