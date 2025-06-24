"""
Configuration management for AI News Collector
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from pathlib import Path

from .exceptions import ConfigError
from .logger import get_logger


class ConfigManager:
    """統一設定管理クラス"""
    
    def __init__(
        self,
        env_file: str = ".env",
        config_dir: str = "config",
        logger_name: str = "config"
    ):
        """
        設定管理器の初期化
        
        Args:
            env_file: .envファイルのパス
            config_dir: 設定ファイルディレクトリ
            logger_name: ロガー名
        """
        self.env_file = env_file
        self.config_dir = Path(config_dir)
        self.logger = get_logger(logger_name)
        self._config_cache = {}
        
        # 設定ディレクトリを作成
        self.config_dir.mkdir(exist_ok=True)
        
        # .envファイルを読み込み
        self._load_env_file()
        
        # 設定ファイルを読み込み
        self._load_config_files()
    
    def _load_env_file(self):
        """環境変数ファイルを読み込み"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            self.logger.info(f"Environment file loaded: {self.env_file}")
        else:
            self.logger.warning(f"Environment file not found: {self.env_file}")
    
    def _load_config_files(self):
        """設定ファイルを読み込み"""
        config_files = [
            "wordpress.json",
            "openai.json", 
            "collection.json",
            "system.json"
        ]
        
        for config_file in config_files:
            config_path = self.config_dir / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        config_name = config_file.replace('.json', '')
                        self._config_cache[config_name] = config_data
                        self.logger.info(f"Config file loaded: {config_file}")
                except Exception as e:
                    self.logger.error(f"Failed to load config file {config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応: section.key）
            default: デフォルト値
            
        Returns:
            設定値
        """
        # 1. 環境変数から取得を試行
        env_value = self._get_from_env(key)
        if env_value is not None:
            return env_value
        
        # 2. 設定ファイルから取得を試行
        config_value = self._get_from_config(key)
        if config_value is not None:
            return config_value
        
        return default
    
    def _get_from_env(self, key: str) -> Any:
        """環境変数から設定値を取得"""
        # ドット記法を環境変数形式に変換 (section.key -> SECTION_KEY)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return self._convert_value(env_value)
        
        return None
    
    def _get_from_config(self, key: str) -> Any:
        """設定ファイルから設定値を取得"""
        if '.' not in key:
            return self._config_cache.get(key)
        
        # ドット記法での取得
        keys = key.split('.')
        section = keys[0]
        
        if section not in self._config_cache:
            return None
        
        value = self._config_cache[section]
        for k in keys[1:]:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _convert_value(self, value: str) -> Any:
        """文字列値を適切な型に変換"""
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        elif value.lower() in ('none', 'null', ''):
            return None
        elif ',' in value:
            # カンマ区切りの場合はリストに変換
            return [item.strip() for item in value.split(',') if item.strip()]
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
    
    def set(self, key: str, value: Any, persist: bool = False):
        """
        設定値を設定
        
        Args:
            key: 設定キー
            value: 設定値
            persist: 設定ファイルに永続化するか
        """
        # 環境変数に設定（ランタイム用）
        env_key = key.upper().replace('.', '_')
        os.environ[env_key] = str(value)
        
        if persist:
            # 設定ファイルに永続化
            if '.' in key:
                keys = key.split('.')
                section = keys[0]
                
                if section not in self._config_cache:
                    self._config_cache[section] = {}
                
                # ネストした設定を更新
                config_section = self._config_cache[section]
                for k in keys[1:-1]:
                    if k not in config_section:
                        config_section[k] = {}
                    config_section = config_section[k]
                
                config_section[keys[-1]] = value
                
                # ファイルに保存
                config_file = self.config_dir / f"{section}.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._config_cache[section], f, ensure_ascii=False, indent=2)
    
    def get_wordpress_config(self) -> Dict[str, Any]:
        """WordPress設定を取得"""
        return {
            'wp_url': self.get('wordpress.url', ''),
            'wp_user': self.get('wordpress.user', ''),
            'wp_app_pass': self.get('wordpress.app_pass', ''),
            'post_settings': {
                'status': self.get('wordpress.post.status', 'publish'),
                'category_id': self.get('wordpress.post.category_id', 1),
                'tags': self.get('wordpress.post.default_tags', []),
                'author_id': self.get('wordpress.post.author_id', 1),
                'featured_media': self.get('wordpress.post.featured_media', None)
            },
            'slug_settings': {
                'auto_generate': self.get('wordpress.slug.auto_generate', True),
                'prefix': self.get('wordpress.slug.prefix', ''),
                'max_length': self.get('wordpress.slug.max_length', 50)
            }
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """OpenAI設定を取得"""
        return {
            'api_key': self.get('openai.api_key', ''),
            'model': self.get('openai.model', 'gpt-3.5-turbo'),
            'max_tokens': self.get('openai.max_tokens', 2000),
            'temperature': self.get('openai.temperature', 0.7),
            'image_model': self.get('openai.image_model', 'dall-e-3'),
            'image_size': self.get('openai.image_size', '1024x1024')
        }
    
    def get_collection_config(self) -> Dict[str, Any]:
        """収集設定を取得"""
        return {
            'max_articles_per_day': self.get('collection.max_articles_per_day', 10),
            'max_articles_per_source': self.get('collection.max_articles_per_source', 5),
            'time_range_hours': self.get('collection.time_range_hours', 24),
            'sources': {
                'news_sites': self.get('collection.sources.news_sites', True),
                'tech_blogs': self.get('collection.sources.tech_blogs', True),
                'x_posts': self.get('collection.sources.x_posts', False)  # デフォルトで無効
            },
            'filters': {
                'min_content_length': self.get('collection.filters.min_content_length', 100),
                'exclude_keywords': self.get('collection.filters.exclude_keywords', []),
                'required_keywords': self.get('collection.filters.required_keywords', ['AI', '人工知能'])
            }
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """システム設定を取得"""
        return {
            'log_level': self.get('system.log_level', 'INFO'),
            'log_file': self.get('system.log_file', 'logs/ai_news_collector.log'),
            'data_dir': self.get('system.data_dir', 'data'),
            'cache_dir': self.get('system.cache_dir', 'cache'),
            'backup_enabled': self.get('system.backup_enabled', True),
            'max_concurrent_requests': self.get('system.max_concurrent_requests', 10)
        }
    
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
            value = self.get(key)
            if value is None or value == '':
                missing_keys.append(key)
        return missing_keys
    
    def create_default_configs(self):
        """デフォルト設定ファイルを作成"""
        default_configs = {
            'wordpress.json': {
                "url": "",
                "user": "",
                "app_pass": "",
                "post": {
                    "status": "publish",
                    "category_id": 1,
                    "default_tags": ["AI", "技術動向"],
                    "author_id": 1
                },
                "slug": {
                    "auto_generate": True,
                    "prefix": "",
                    "max_length": 50
                }
            },
            'openai.json': {
                "api_key": "",
                "model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "image_model": "dall-e-3",
                "image_size": "1024x1024"
            },
            'collection.json': {
                "max_articles_per_day": 10,
                "max_articles_per_source": 5,
                "time_range_hours": 24,
                "sources": {
                    "news_sites": True,
                    "tech_blogs": True,
                    "x_posts": False
                },
                "filters": {
                    "min_content_length": 100,
                    "exclude_keywords": ["広告", "PR"],
                    "required_keywords": ["AI", "人工知能", "機械学習"]
                }
            },
            'system.json': {
                "log_level": "INFO",
                "log_file": "logs/ai_news_collector.log",
                "data_dir": "data",
                "cache_dir": "cache",
                "backup_enabled": True,
                "max_concurrent_requests": 10
            }
        }
        
        for filename, config_data in default_configs.items():
            config_path = self.config_dir / filename
            if not config_path.exists():
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Created default config: {filename}")
    
    def print_config_summary(self):
        """設定の概要を表示"""
        self.logger.info("=== Configuration Summary ===")
        
        wp_config = self.get_wordpress_config()
        self.logger.info(f"WordPress URL: {wp_config['wp_url']}")
        self.logger.info(f"WordPress User: {wp_config['wp_user']}")
        
        openai_config = self.get_openai_config()
        api_key = openai_config['api_key']
        self.logger.info(f"OpenAI API Key: {'configured' if api_key else 'not configured'}")
        
        collection_config = self.get_collection_config()
        self.logger.info(f"Max articles per day: {collection_config['max_articles_per_day']}")
        
        system_config = self.get_system_config()
        self.logger.info(f"Log level: {system_config['log_level']}")
        self.logger.info("==============================") 