import asyncio
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from config import ConfigManager
from version_manager import VersionManager
from download_manager import DownloadManager
from game_launcher import GameLauncher

logger = logging.getLogger(__name__)

class LauncherCore:
    """启动器核心"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.version_manager = VersionManager(self.config)
        self.download_manager = DownloadManager(
            max_concurrent=self.config.config.download_threads
        )
        self.game_launcher = GameLauncher(self.config)
    
    async def fetch_versions(self):
        """获取版本列表"""
        return await self.version_manager.fetch_version_manifest()
    
    def get_installed_versions(self):
        """获取已安装版本"""
        return self.version_manager.get_installed_versions()
    
    async def download_version(self, version_id: str):
        """下载版本"""
        return await self.version_manager.download_version_json(version_id)
    
    async def download_assets(self, version_data: Dict, progress_callback=None):
        """下载资源文件"""
        return await self.version_manager.download_assets(version_data, progress_callback)
    
    async def download_libraries(self, version_data: Dict, progress_callback=None):
        """下载库文件"""
        return await self.version_manager.download_libraries(version_data, progress_callback)
    
    async def launch_game(self, version_id: str):
        """启动游戏"""
        return await self.game_launcher.launch(version_id)