"""
HTTP client utility for AI News Collector
"""

import asyncio
import aiohttp
import requests
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random


class HTTPClient:
    """統一HTTPクライアント"""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        user_agent: str = None
    ):
        """
        HTTPクライアントの初期化
        
        Args:
            timeout: タイムアウト秒数
            max_retries: 最大リトライ回数
            backoff_factor: リトライ間隔の倍率
            user_agent: User-Agentヘッダー
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # デフォルトUser-Agent
        if user_agent is None:
            user_agent = (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 同期クライアントの設定
        self.session = requests.Session()
        self._setup_retry_strategy()
    
    def _setup_retry_strategy(self):
        """リトライ戦略の設定"""
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # ヘッダーを設定
        self.session.headers.update(self.headers)
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        同期GET リクエスト
        
        Args:
            url: リクエストURL
            **kwargs: 追加のリクエストパラメータ
            
        Returns:
            レスポンスオブジェクト（失敗時はNone）
        """
        try:
            # レート制限対応
            self._rate_limit()
            
            response = self.session.get(
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"HTTP GET error for {url}: {e}")
            return None
    
    def post(self, url: str, data: Any = None, json: Any = None, **kwargs) -> Optional[requests.Response]:
        """
        同期POST リクエスト
        
        Args:
            url: リクエストURL
            data: POSTデータ
            json: JSONデータ
            **kwargs: 追加のリクエストパラメータ
            
        Returns:
            レスポンスオブジェクト（失敗時はNone）
        """
        try:
            # レート制限対応
            self._rate_limit()
            
            response = self.session.post(
                url,
                data=data,
                json=json,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"HTTP POST error for {url}: {e}")
            return None
    
    async def async_get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        非同期GET リクエスト
        
        Args:
            url: リクエストURL
            **kwargs: 追加のリクエストパラメータ
            
        Returns:
            レスポンスオブジェクト（失敗時はNone）
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=self.headers
            ) as session:
                # レート制限対応
                await self._async_rate_limit()
                
                async with session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    return response
                    
        except aiohttp.ClientError as e:
            print(f"Async HTTP GET error for {url}: {e}")
            return None
    
    async def async_get_multiple(self, urls: List[str], **kwargs) -> List[Optional[aiohttp.ClientResponse]]:
        """
        複数URLの非同期GET リクエスト
        
        Args:
            urls: リクエストURLのリスト
            **kwargs: 追加のリクエストパラメータ
            
        Returns:
            レスポンスオブジェクトのリスト
        """
        semaphore = asyncio.Semaphore(10)  # 同時リクエスト数制限
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return await self.async_get(url, **kwargs)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _rate_limit(self):
        """レート制限（同期版）"""
        # 0.1-0.5秒のランダムな遅延
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
    
    async def _async_rate_limit(self):
        """レート制限（非同期版）"""
        # 0.1-0.5秒のランダムな遅延
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)
    
    def set_headers(self, headers: Dict[str, str]):
        """ヘッダーを設定"""
        self.headers.update(headers)
        self.session.headers.update(headers)
    
    def close(self):
        """セッションを閉じる"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 