"""
Logging configuration for AI News Collector
"""

import logging
import os
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """カラー出力対応のフォーマッター"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # レベル名に色を付ける
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    colored_output: bool = True
) -> logging.Logger:
    """
    ログシステムの設定
    
    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルのパス（Noneの場合はファイル出力なし）
        console_output: コンソール出力の有効/無効
        colored_output: カラー出力の有効/無効
    
    Returns:
        設定されたロガー
    """
    logger = logging.getLogger("ai_news_collector")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマッターの設定
    if colored_output and console_output:
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # コンソールハンドラー
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # ファイルハンドラー
    if log_file:
        # ログディレクトリを作成
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # ファイル用のフォーマッター（色なし）
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    ロガーを取得
    
    Args:
        name: ロガー名（Noneの場合はデフォルト）
    
    Returns:
        ロガーインスタンス
    """
    if name:
        return logging.getLogger(f"ai_news_collector.{name}")
    return logging.getLogger("ai_news_collector")


def log_system_info():
    """システム情報をログに出力"""
    import sys
    logger = get_logger("system")
    logger.info("=== AI News Collector System Started ===")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")


def log_collection_stats(stats: dict):
    """収集統計をログに出力"""
    logger = get_logger("stats")
    logger.info("=== Collection Statistics ===")
    for key, value in stats.items():
        logger.info(f"{key}: {value}")


def log_error_with_context(error: Exception, context: str = ""):
    """エラーを詳細な情報と共にログに出力"""
    logger = get_logger("error")
    logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")
    
    # デバッグレベルでスタックトレースも出力
    import traceback
    logger.debug(f"Stack trace: {traceback.format_exc()}") 