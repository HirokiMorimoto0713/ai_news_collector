# AI News Collector - Refactored Version

リファクタリングされたAI情報収集・投稿システム

## 🔄 リファクタリングの改善点

### 1. **モジュール構造の整理**
```
src/
├── core/                 # コアモジュール
│   ├── models.py        # データモデル
│   ├── config.py        # 設定管理
│   ├── logger.py        # ログシステム
│   └── exceptions.py    # カスタム例外
├── collectors/          # 収集モジュール
├── processors/          # 処理モジュール
├── connectors/          # 連携モジュール
└── utils/               # ユーティリティ
    ├── http_client.py   # HTTP通信
    ├── text_utils.py    # テキスト処理
    ├── file_utils.py    # ファイル操作
    └── date_utils.py    # 日付処理
```

### 2. **統一された設定管理**
- 環境変数とJSONファイルの両方に対応
- ドット記法での設定アクセス（`wordpress.url`）
- デフォルト設定ファイルの自動生成
- 設定の検証機能

### 3. **改良されたログシステム**
- カラー出力対応
- モジュール別ログ管理
- ファイル・コンソール出力の選択
- 構造化されたログ出力

### 4. **エラーハンドリングの改善**
- カスタム例外クラス
- 詳細なエラー情報
- グレースフルな処理継続

### 5. **型ヒントの追加**
- 全関数・メソッドに型ヒント
- データクラスの活用
- 型安全性の向上

## 🚀 使用方法

### 1. 環境設定

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依存関係のインストール
pip install -r requirements_refactored.txt
```

### 2. 設定ファイルの作成

```bash
# リファクタリング版の実行（初回は設定ファイルを自動生成）
python main_refactored.py
```

設定ファイルが `config/` ディレクトリに自動生成されます：

- `config/wordpress.json` - WordPress設定
- `config/openai.json` - OpenAI設定
- `config/collection.json` - 収集設定
- `config/system.json` - システム設定

### 3. 設定の編集

#### WordPress設定 (`config/wordpress.json`)
```json
{
  "url": "https://your-wordpress-site.com",
  "user": "your-username",
  "app_pass": "your-app-password",
  "post": {
    "status": "publish",
    "category_id": 1,
    "default_tags": ["AI", "技術動向"],
    "author_id": 1
  }
}
```

#### OpenAI設定 (`config/openai.json`)
```json
{
  "api_key": "your-openai-api-key",
  "model": "gpt-3.5-turbo",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### 4. 実行

```bash
# リファクタリング版の実行
python main_refactored.py

# 従来版との並行実行も可能
python main.py
```

## 🔧 新機能

### 1. **統一設定管理**
```python
from src.core.config import ConfigManager

config = ConfigManager()
wp_url = config.get('wordpress.url')
api_key = config.get('openai.api_key')
```

### 2. **構造化ログ**
```python
from src.core.logger import get_logger

logger = get_logger("my_module")
logger.info("Processing started")
logger.error("Error occurred", extra={'context': 'processing'})
```

### 3. **型安全なデータモデル**
```python
from src.core.models import NewsArticle, ProcessedArticle

article = NewsArticle(
    title="AI News",
    url="https://example.com",
    content="Content here",
    source="Example Site"
)
```

### 4. **統一HTTPクライアント**
```python
from src.utils.http_client import HTTPClient

async with HTTPClient() as client:
    response = await client.async_get("https://example.com")
```

## 📊 パフォーマンス改善

### 1. **非同期処理の最適化**
- 並列HTTP リクエスト
- 効率的なリソース管理
- レート制限対応

### 2. **メモリ使用量の削減**
- ストリーミング処理
- 適切なキャッシュ管理
- リソースの自動解放

### 3. **エラー回復力の向上**
- リトライ機能
- フォールバック処理
- グレースフルな劣化

## 🔍 デバッグ・監視

### 1. **詳細なログ出力**
```bash
# ログレベルの変更
export SYSTEM_LOG_LEVEL=DEBUG
python main_refactored.py
```

### 2. **統計情報の取得**
- 収集記事数
- 処理成功/失敗数
- 実行時間の測定

### 3. **設定の検証**
```bash
# 設定の妥当性チェック
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
config.print_config_summary()
"
```

## 🔄 移行ガイド

### 従来版からの移行

1. **設定の移行**
   ```bash
   # 既存の設定を新形式に変換
   python migrate_config.py
   ```

2. **段階的移行**
   - リファクタリング版と従来版を並行実行
   - 動作確認後に完全移行

3. **データの互換性**
   - 既存のデータファイルはそのまま使用可能
   - 新しいディレクトリ構造に自動対応

## 🧪 テスト

```bash
# テストの実行
pytest tests/

# カバレッジレポート
pytest --cov=src tests/

# 型チェック
mypy src/
```

## 📈 今後の拡張計画

### 1. **新しいコレクター**
- RSS フィード対応
- API 連携の追加
- カスタムソースの対応

### 2. **高度な処理機能**
- 画像解析
- 動画コンテンツ対応
- 多言語処理

### 3. **モニタリング**
- Prometheus メトリクス
- ヘルスチェック機能
- アラート機能

## ⚠️ 注意事項

### 1. **互換性**
- 既存の機能は完全に保持
- データ形式の互換性を維持
- 段階的な移行が可能

### 2. **パフォーマンス**
- 初回実行時は設定ファイル生成のため時間がかかる場合があります
- MeCab が利用できない環境では簡易テキスト処理を使用

### 3. **設定**
- 必須設定が不足している場合は実行前にエラーで停止
- 設定ファイルの形式が変更された場合は自動マイグレーション

## 📞 サポート

### トラブルシューティング

1. **設定エラー**
   ```bash
   # 設定の検証
   python -c "
   from src.core.config import ConfigManager
   config = ConfigManager()
   missing = config.validate_required_settings(['wordpress.url', 'openai.api_key'])
   print('Missing:', missing)
   "
   ```

2. **ログの確認**
   ```bash
   # ログファイルの確認
   tail -f logs/ai_news_collector.log
   ```

3. **デバッグモード**
   ```bash
   # デバッグレベルで実行
   export SYSTEM_LOG_LEVEL=DEBUG
   python main_refactored.py
   ```

---

## 📄 ライセンス

このプロジェクトは個人利用・研究目的で開発されています。
商用利用の場合は、各ニュースサイトの利用規約を確認してください。 