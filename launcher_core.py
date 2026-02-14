import asyncio
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional
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
        # 下载版本JSON
        version_data = await self.version_manager.download_version_json(version_id)
        if not version_data:
            return None
        
        return version_data
    
    async def download_assets(self, version_data: Dict, progress_callback=None):
        """下载资源文件"""
        assets_index = version_data.get("assetIndex", {})
        assets_url = assets_index.get("url", "")
        
        if self.config.use_bmclapi:
            assets_url = assets_url.replace(
                "https://launchermeta.mojang.com/",
                "https://bmclapi2.bangbang93.com/"
            )
        
        # 下载assets索引
        assets_dir = self.config.get_assets_dir()
        indexes_dir = assets_dir / "indexes"
        indexes_dir.mkdir(parents=True, exist_ok=True)
        
        assets_index_path = indexes_dir / f"{assets_index.get('id', '')}.json"
        
        async def download_assets_index():
            async with aiohttp.ClientSession() as session:
                async with session.get(assets_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(assets_index_path, 'wb') as f:
                            f.write(content)
                        
                        assets_data = json.loads(content)
                        return assets_data
            return None
        
        assets_data = await download_assets_index()
        if not assets_data:
            return False
        
        # 下载资源文件
        objects = assets_data.get("objects", {})
        download_tasks = []
        
        for obj_hash, obj_info in objects.items():
            hash_str = obj_hash
            if isinstance(obj_info, dict):
                hash_str = obj_info.get("hash", obj_hash)
            
            url = f"{self.config.mirrors['resources']}/{hash_str[:2]}/{hash_str}"
            path = assets_dir / "objects" / hash_str[:2] / hash_str
            
            if not path.exists():
                download_tasks.append({
                    'url': url,
                    'path': path,
                    'sha1': hash_str
                })
        
        if download_tasks:
            return await self.download_manager.download_multiple(
                download_tasks, progress_callback
            )
        
        return True
    
    async def download_libraries(self, version_data: Dict, progress_callback=None):
        """下载库文件"""
        libraries = version_data.get("libraries", [])
        download_tasks = []
        
        for lib in libraries:
            downloads = lib.get("downloads", {})
            
            # 主库文件
            artifact = downloads.get("artifact")
            if artifact:
                url = artifact.get("url", "")
                if self.config.use_bmclapi and "libraries.minecraft.net" in url:
                    url = url.replace(
                        "https://libraries.minecraft.net/",
                        self.config.mirrors["maven"]
                    )
                
                path = self.config.get_libraries_dir() / artifact["path"]
                if not path.exists():
                    download_tasks.append({
                        'url': url,
                        'path': path,
                        'sha1': artifact.get("sha1")
                    })
            
            # 原生库
            classifiers = downloads.get("classifiers", {})
            native_key = None
            
            # 检测系统架构
            system = platform.system().lower()
            arch = platform.machine().lower()
            
            if system == "windows":
                if "64" in arch:
                    native_key = "natives-windows-64"
                else:
                    native_key = "natives-windows-32"
            elif system == "linux":
                if "64" in arch:
                    native_key = "natives-linux-64"
                else:
                    native_key = "natives-linux-32"
            elif system == "darwin":
                native_key = "natives-osx"
            
            if native_key and native_key in classifiers:
                native_info = classifiers[native_key]
                url = native_info.get("url", "")
                path = self.config.get_libraries_dir() / native_info["path"]
                
                if not path.exists():
                    download_tasks.append({
                        'url': url,
                        'path': path,
                        'sha1': native_info.get("sha1")
                    })
        
        if download_tasks:
            return await self.download_manager.download_multiple(
                download_tasks, progress_callback
            )
        
        return True
    
    async def launch_game(self, version_id: str):
        """启动游戏"""
        return await self.game_launcher.launch(version_id)