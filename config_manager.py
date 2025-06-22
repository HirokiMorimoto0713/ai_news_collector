"""
設定管理の統一モジュール
環境変数とJSONファイルの両方に対応し、統一的な設定管理を提供
"""

import os
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

class ConfigManager:
    """設定管理を統一するクラス"""
    
    def __init__(self, env_file: str = ".env", json_file: str = None):
        """
        設定管理器の初期化
        
        Args:
            env_file: .envファイルのパス
            json_file: JSONファイルのパス（オプション、互換性のため）
        """
        self.env_file = env_file
        self.json_file = json_file
        self._config_cache = {}
        
        # .envファイルを読み込み
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ 環境変数ファイル読み込み: {env_file}")
        else:
            print(f"⚠️ 環境変数ファイルが見つかりません: {env_file}")
        
        # 互換性のためJSONファイルも読み込み（存在する場合）
        if json_file and os.path.exists(json_file):
            self._load_json_config(json_file)
            print(f"✅ JSONファイル読み込み（互換性モード）: {json_file}")
    
    def _load_json_config(self, json_file: str):
        """JSONファイルから設定を読み込み（互換性のため）"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
                self._config_cache.update(json_config)
        except Exception as e:
            print(f"JSONファイル読み込みエラー: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            
        Returns:
            設定値
        """
        # 1. 環境変数から取得を試行
        env_value = os.getenv(key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # 2. キャッシュされたJSON設定から取得を試行
        if key in self._config_cache:
            return self._config_cache[key]
        
        # 3. ドット記法での取得を試行（例: wp.url）
        if '.' in key:
            return self._get_nested_value(key, default)
        
        return default
    
    def _get_nested_value(self, key: str, default: Any = None) -> Any:
        """
        ドット記法での設定値取得（例: wp.url -> WP_URL）
        """
        # ドット記法を環境変数形式に変換
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # JSON形式での取得を試行
        keys = key.split('.')
        value = self._config_cache
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def _convert_value(self, value: str) -> Any:
        """
        文字列値を適切な型に変換
        """
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        elif value.lower() == 'none' or value.lower() == 'null':
            return None
        elif ',' in value:
            # カンマ区切りの場合はリストに変換
            return [item.strip() for item in value.split(',')]
        elif value.isdigit():
            return int(value)
        elif self._is_float(value):
            return float(value)
        else:
            return value
    
    def _is_float(self, value: str) -> bool:
        """文字列が浮動小数点数かチェック"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def get_wordpress_config(self) -> Dict[str, Any]:
        """
        WordPress設定を取得
        
        Returns:
            WordPress設定辞書
        """
        return {
            'wp_url': self.get('WP_URL', ''),
            'wp_user': self.get('WP_USER', ''),
            'wp_app_pass': self.get('WP_APP_PASS', ''),
            'post_settings': {
                'status': self.get('WP_POST_STATUS', 'publish'),
                'category_id': self.get('WP_CATEGORY_ID', 1),
                'tags': self.get('WP_DEFAULT_TAGS', []),
                'author_id': self.get('WP_AUTHOR_ID', 1),
                'featured_media': self.get('WP_FEATURED_MEDIA', None)
            },
            'slug_settings': {
                'auto_generate': self.get('WP_SLUG_AUTO_GENERATE', True),
                'prefix': self.get('WP_SLUG_PREFIX', ''),
                'max_length': self.get('WP_SLUG_MAX_LENGTH', 50)
            }
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """
        OpenAI設定を取得
        
        Returns:
            OpenAI設定辞書
        """
        return {
            'api_key': self.get('OPENAI_API_KEY', ''),
            'model': self.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'max_tokens': self.get('OPENAI_MAX_TOKENS', 2000),
            'temperature': self.get('OPENAI_TEMPERATURE', 0.7)
        }
    
    def get_news_config(self) -> Dict[str, Any]:
        """
        ニュース収集設定を取得
        
        Returns:
            ニュース収集設定辞書
        """
        return {
            'sources': self.get('NEWS_SOURCES', []),
            'collection_limit': self.get('NEWS_COLLECTION_LIMIT', 10),
            'processing_batch_size': self.get('NEWS_PROCESSING_BATCH_SIZE', 5)
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        システム設定を取得
        
        Returns:
            システム設定辞書
        """
        return {
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'log_file_path': self.get('LOG_FILE_PATH', 'system.log'),
            'backup_enabled': self.get('BACKUP_ENABLED', True)
        }
    
    def set_env_value(self, key: str, value: Any):
        """
        環境変数を設定（ランタイム用）
        
        Args:
            key: 設定キー
            value: 設定値
        """
        os.environ[key] = str(value)
    
    def validate_required_settings(self, required_keys: List[str]) -> List[str]:
        """
        必須設定の検証
        
        Args:
            required_keys: 必須キーのリスト
            
        Returns:
            不足しているキーのリスト
        """
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        return missing_keys
    
    def print_config_summary(self):
        """設定の概要を表示"""
        print("\n=== 設定概要 ===")
        
        wp_config = self.get_wordpress_config()
        print(f"WordPress URL: {wp_config['wp_url']}")
        print(f"WordPress User: {wp_config['wp_user']}")
        print(f"投稿ステータス: {wp_config['post_settings']['status']}")
        
        openai_config = self.get_openai_config()
        api_key = openai_config['api_key']
        print(f"OpenAI API Key: {'設定済み' if api_key else '未設定'}")
        
        system_config = self.get_system_config()
        print(f"ログレベル: {system_config['log_level']}")
        print(f"バックアップ: {'有効' if system_config['backup_enabled'] else '無効'}")
        print("================\n")

# グローバルインスタンス（互換性のため）
config_manager = ConfigManager(
    env_file=".env",
    json_file="wordpress_config.json"  # 既存のJSONファイルとの互換性
) 