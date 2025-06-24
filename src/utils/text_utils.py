"""
Text processing utilities for AI News Collector
"""

import re
import unicodedata
from typing import List, Set
from difflib import SequenceMatcher

try:
    import MeCab  # type: ignore
    MECAB_AVAILABLE = True
except ImportError:
    MECAB_AVAILABLE = False
    MeCab = None  # type: ignore


class TextProcessor:
    """テキスト処理クラス"""
    
    def __init__(self):
        """MeCabの初期化（利用可能な場合）"""
        if MECAB_AVAILABLE and MeCab is not None:
            try:
                self.mecab = MeCab.Tagger("-Owakati")  # type: ignore
                self.has_mecab = True
            except:
                self.mecab = None
                self.has_mecab = False
        else:
            self.mecab = None
            self.has_mecab = False
    
    def tokenize(self, text: str) -> List[str]:
        """テキストを単語に分割"""
        if self.has_mecab and self.mecab is not None:
            return self.mecab.parse(text).strip().split()
        else:
            # MeCabが利用できない場合の簡易分割
            return re.findall(r'\w+', text)


# グローバルインスタンス
_text_processor = TextProcessor()


def clean_text(text: str) -> str:
    """
    テキストをクリーニング
    
    Args:
        text: 入力テキスト
        
    Returns:
        クリーニングされたテキスト
    """
    if not text:
        return ""
    
    # HTMLタグを除去
    text = re.sub(r'<[^>]+>', '', text)
    
    # 特殊文字を除去（日本語文字は保持）
    text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBF]', ' ', text)
    
    # 連続する空白を単一の空白に変換
    text = re.sub(r'\s+', ' ', text)
    
    # Unicode正規化
    text = unicodedata.normalize('NFKC', text)
    
    return text.strip()


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """
    テキストからキーワードを抽出
    
    Args:
        text: 入力テキスト
        min_length: 最小キーワード長
        
    Returns:
        キーワードのリスト
    """
    if not text:
        return []
    
    # テキストをクリーニング
    cleaned_text = clean_text(text)
    
    # 単語に分割
    words = _text_processor.tokenize(cleaned_text)
    
    # キーワードをフィルタリング
    keywords = []
    for word in words:
        if len(word) >= min_length and not word.isdigit():
            keywords.append(word.lower())
    
    # 重複を除去して頻度順にソート
    word_counts = {}
    for word in keywords:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 頻度順にソート
    sorted_keywords = sorted(word_counts.keys(), key=lambda x: word_counts[x], reverse=True)
    
    return sorted_keywords[:20]  # 上位20個まで


def similarity_check(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    2つのテキストの類似度をチェック
    
    Args:
        text1: テキスト1
        text2: テキスト2
        threshold: 類似度の閾値
        
    Returns:
        類似度が閾値を超えるかどうか
    """
    if not text1 or not text2:
        return False
    
    # テキストをクリーニング
    clean1 = clean_text(text1).lower()
    clean2 = clean_text(text2).lower()
    
    # 類似度を計算
    similarity = SequenceMatcher(None, clean1, clean2).ratio()
    
    return similarity >= threshold


def extract_sentences(text: str, max_sentences: int = 3) -> List[str]:
    """
    テキストから文を抽出
    
    Args:
        text: 入力テキスト
        max_sentences: 最大文数
        
    Returns:
        文のリスト
    """
    if not text:
        return []
    
    # 文の区切り文字で分割
    sentences = re.split(r'[。！？\.\!\?]', text)
    
    # 空の文を除去
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences[:max_sentences]


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    テキストを指定長で切り詰め
    
    Args:
        text: 入力テキスト
        max_length: 最大長
        suffix: 省略記号
        
    Returns:
        切り詰められたテキスト
    """
    if not text or len(text) <= max_length:
        return text
    
    # 文の境界で切り詰める
    truncated = text[:max_length]
    
    # 最後の句読点を探す
    last_punct = max(
        truncated.rfind('。'),
        truncated.rfind('！'),
        truncated.rfind('？'),
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_punct > max_length * 0.7:  # 70%以上の位置にある場合
        return truncated[:last_punct + 1]
    else:
        return truncated + suffix


def contains_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    テキストが指定されたキーワードを含むかチェック
    
    Args:
        text: チェック対象のテキスト
        keywords: キーワードのリスト
        case_sensitive: 大文字小文字を区別するか
        
    Returns:
        キーワードが含まれるかどうか
    """
    if not text or not keywords:
        return False
    
    check_text = text if case_sensitive else text.lower()
    
    for keyword in keywords:
        check_keyword = keyword if case_sensitive else keyword.lower()
        if check_keyword in check_text:
            return True
    
    return False


def normalize_whitespace(text: str) -> str:
    """
    空白文字を正規化
    
    Args:
        text: 入力テキスト
        
    Returns:
        正規化されたテキスト
    """
    if not text:
        return ""
    
    # 全角空白を半角空白に変換
    text = text.replace('　', ' ')
    
    # 連続する空白を単一の空白に変換
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def remove_urls(text: str) -> str:
    """
    テキストからURLを除去
    
    Args:
        text: 入力テキスト
        
    Returns:
        URLが除去されたテキスト
    """
    if not text:
        return ""
    
    # URLパターンを除去
    url_pattern = r'https?://[^\s]+'
    text = re.sub(url_pattern, '', text)
    
    return normalize_whitespace(text) 