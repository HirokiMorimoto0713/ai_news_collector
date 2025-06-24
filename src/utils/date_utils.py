"""
Date utilities for AI News Collector
"""

from datetime import datetime, timedelta
from typing import Optional
import re


def parse_date(date_str: str) -> Optional[datetime]:
    """
    文字列から日付を解析
    
    Args:
        date_str: 日付文字列
        
    Returns:
        datetimeオブジェクト（解析失敗時はNone）
    """
    if not date_str:
        return None
    
    # 様々な日付フォーマットに対応
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y年%m月%d日 %H:%M:%S",
        "%Y年%m月%d日",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # ISO形式の処理
    try:
        # Zを+00:00に置換してからパース
        iso_str = date_str.replace('Z', '+00:00')
        return datetime.fromisoformat(iso_str)
    except ValueError:
        pass
    
    return None


def format_date(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    日付を文字列にフォーマット
    
    Args:
        dt: datetimeオブジェクト
        format_str: フォーマット文字列
        
    Returns:
        フォーマットされた日付文字列
    """
    if not dt:
        return ""
    
    return dt.strftime(format_str)


def is_recent(dt: datetime, hours: int = 24) -> bool:
    """
    指定された時間以内の日付かチェック
    
    Args:
        dt: チェック対象の日付
        hours: 時間数
        
    Returns:
        指定時間以内かどうか
    """
    if not dt:
        return False
    
    now = datetime.now()
    time_limit = now - timedelta(hours=hours)
    
    # タイムゾーンを除去して比較
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    
    return dt >= time_limit


def get_date_range(days_back: int = 7) -> tuple[datetime, datetime]:
    """
    指定日数前からの日付範囲を取得
    
    Args:
        days_back: 何日前まで
        
    Returns:
        (開始日時, 終了日時)のタプル
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return start_date, end_date


def extract_date_from_text(text: str) -> Optional[datetime]:
    """
    テキストから日付を抽出
    
    Args:
        text: テキスト
        
    Returns:
        抽出された日付（見つからない場合はNone）
    """
    if not text:
        return None
    
    # 日付パターンの正規表現
    patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 6:  # 日時
                    year, month, day, hour, minute, second = map(int, groups)
                    return datetime(year, month, day, hour, minute, second)
                elif len(groups) == 3:  # 日付のみ
                    year, month, day = map(int, groups)
                    return datetime(year, month, day)
            except ValueError:
                continue
    
    return None


def get_today_string(format_str: str = "%Y-%m-%d") -> str:
    """
    今日の日付を文字列で取得
    
    Args:
        format_str: フォーマット文字列
        
    Returns:
        今日の日付文字列
    """
    return datetime.now().strftime(format_str)


def days_between(date1: datetime, date2: datetime) -> int:
    """
    2つの日付間の日数を計算
    
    Args:
        date1: 日付1
        date2: 日付2
        
    Returns:
        日数の差
    """
    if not date1 or not date2:
        return 0
    
    # タイムゾーンを除去
    if date1.tzinfo:
        date1 = date1.replace(tzinfo=None)
    if date2.tzinfo:
        date2 = date2.replace(tzinfo=None)
    
    return abs((date2 - date1).days) 