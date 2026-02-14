import asyncio
import aiohttp
import hashlib
from pathlib import Path
from typing import List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class DownloadManager:
    """下载管理器"""
    
    def __init__(self, max_concurrent: int = 8):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_file(
        self,
        url: str,
        path: Path,
        sha1: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """下载单个文件"""
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            
                            path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if progress_callback and total_size > 0:
                                        progress_callback(url, downloaded, total_size)
                            
                            # 验证SHA1
                            if sha1:
                                file_sha1 = await self.calculate_sha1(path)
                                if file_sha1 != sha1:
                                    logger.warning(f"SHA1校验失败: {path}")
                                    return False
                            
                            return True
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {e}")
            return False
    
    async def calculate_sha1(self, path: Path) -> str:
        """计算文件的SHA1"""
        sha1 = hashlib.sha1()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()