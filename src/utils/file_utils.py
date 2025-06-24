"""
File utilities for AI News Collector
"""

import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


def ensure_dir(path: str) -> Path:
    """
    ディレクトリが存在することを確認し、必要に応じて作成
    
    Args:
        path: ディレクトリパス
        
    Returns:
        Pathオブジェクト
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def save_json(data: Any, filepath: str, ensure_ascii: bool = False, indent: int = 2) -> bool:
    """
    データをJSONファイルに保存
    
    Args:
        data: 保存するデータ
        filepath: ファイルパス
        ensure_ascii: ASCII文字のみ使用するか
        indent: インデント数
        
    Returns:
        保存に成功したかどうか
    """
    try:
        # ディレクトリを確保
        file_path = Path(filepath)
        ensure_dir(str(file_path.parent))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        return True
        
    except Exception as e:
        print(f"Failed to save JSON to {filepath}: {e}")
        return False


def load_json(filepath: str, default: Any = None) -> Any:
    """
    JSONファイルからデータを読み込み
    
    Args:
        filepath: ファイルパス
        default: ファイルが存在しない場合のデフォルト値
        
    Returns:
        読み込まれたデータ
    """
    try:
        if not os.path.exists(filepath):
            return default
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"Failed to load JSON from {filepath}: {e}")
        return default


def backup_file(filepath: str, backup_dir: str = "backup") -> Optional[str]:
    """
    ファイルをバックアップ
    
    Args:
        filepath: バックアップ対象のファイルパス
        backup_dir: バックアップディレクトリ
        
    Returns:
        バックアップファイルのパス（失敗時はNone）
    """
    try:
        if not os.path.exists(filepath):
            return None
        
        # バックアップディレクトリを作成
        backup_path = ensure_dir(backup_dir)
        
        # タイムスタンプ付きのバックアップファイル名を生成
        original_path = Path(filepath)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{original_path.stem}_{timestamp}{original_path.suffix}"
        backup_filepath = backup_path / backup_filename
        
        # ファイルをコピー
        shutil.copy2(filepath, backup_filepath)
        
        return str(backup_filepath)
        
    except Exception as e:
        print(f"Failed to backup file {filepath}: {e}")
        return None


def create_data_structure():
    """プロジェクトのデータディレクトリ構造を作成"""
    directories = [
        "data",
        "data/articles", 
        "data/processed",
        "data/published",
        "logs",
        "cache",
        "backup",
        "config"
    ]
    
    for directory in directories:
        ensure_dir(directory)
        print(f"Created directory: {directory}") 