import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VersionInfo:
    """版本信息"""
    id: str
    type: str
    url: str
    time: str
    release_time: str
    sha1: str
    compliance_level: int = 0

class VersionManager:
    """版本管理器"""
    
    def __init__(self, config):
        self.config = config
        self.versions: Dict[str, VersionInfo] = {}
    
    async def fetch_version_manifest(self):
        """获取版本清单"""
        try:
            url = self.config.config.mirrors["version_manifest"]
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for version in data.get("versions", []):
                            self.versions[version["id"]] = VersionInfo(**version)
                        return True
        except Exception as e:
            logger.error(f"获取版本清单失败: {e}")
        return False
    
    def get_installed_versions(self):
        """获取已安装的版本"""
        versions_dir = self.config.get_versions_dir()
        installed = []
        if versions_dir.exists():
            for version_dir in versions_dir.iterdir():
                if version_dir.is_dir() and (version_dir / f"{version_dir.name}.json").exists():
                    installed.append(version_dir.name)
        return installed
    
    async def download_version_json(self, version_id: str):
        """下载版本JSON文件"""
        if version_id not in self.versions:
            return None
        
        version_info = self.versions[version_id]
        version_dir = self.config.get_versions_dir() / version_id
        version_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = version_dir / f"{version_id}.json"
        
        # 替换镜像源
        download_url = version_info.url
        if self.config.config.use_bmclapi:
            download_url = download_url.replace(
                "https://launchermeta.mojang.com/",
                "https://bmclapi2.bangbang93.com/"
            ).replace(
                "https://launcher.mojang.com/",
                "https://bmclapi2.bangbang93.com/"
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        data = json.loads(content)
                        
                        # 处理镜像替换
                        if self.config.config.use_bmclapi:
                            data = self._replace_mirrors_in_json(data)
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        
                        # 下载客户端jar
                        client_url = data.get("downloads", {}).get("client", {}).get("url", "")
                        if client_url:
                            client_path = version_dir / f"{version_id}.jar"
                            await self._download_file(client_url, client_path)
                        
                        return data
        except Exception as e:
            logger.error(f"下载版本JSON失败: {e}")
        return None
    
    async def _download_file(self, url: str, path: Path):
        """下载单个文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(path, 'wb') as f:
                            f.write(content)
                        return True
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {e}")
        return False
    
    def _replace_mirrors_in_json(self, data: Dict) -> Dict:
        """替换JSON中的镜像源"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    if "launchermeta.mojang.com" in value:
                        data[key] = value.replace(
                            "https://launchermeta.mojang.com/",
                            "https://bmclapi2.bangbang93.com/"
                        )
                    elif "launcher.mojang.com" in value:
                        data[key] = value.replace(
                            "https://launcher.mojang.com/",
                            "https://bmclapi2.bangbang93.com/"
                        )
                    elif "resources.download.minecraft.net" in value:
                        data[key] = value.replace(
                            "http://resources.download.minecraft.net",
                            "https://bmclapi2.bangbang93.com/assets"
                        )
                    elif "libraries.minecraft.net" in value:
                        data[key] = value.replace(
                            "https://libraries.minecraft.net/",
                            "https://bmclapi2.bangbang93.com/maven"
                        )
                elif isinstance(value, (dict, list)):
                    data[key] = self._replace_mirrors_in_json(value)
        elif isinstance(data, list):
            return [self._replace_mirrors_in_json(item) for item in data]
        return data
    
    def get_version_list(self) -> List[str]:
        """获取版本列表"""
        return list(self.versions.keys())
    
    async def download_assets(self, version_data: Dict, progress_callback=None):
        """下载资源文件"""
        # 简化的资源下载逻辑
        logger.info("开始下载资源文件...")
        if progress_callback:
            progress_callback("assets", 50, 100)
        await asyncio.sleep(0.5)  # 模拟下载
        if progress_callback:
            progress_callback("assets", 100, 100)
        return True
    
    async def download_libraries(self, version_data: Dict, progress_callback=None):
        """下载库文件"""
        # 简化的库文件下载逻辑
        logger.info("开始下载库文件...")
        libraries = version_data.get("libraries", [])
        for i, lib in enumerate(libraries):
            if progress_callback:
                progress_callback(f"library_{i}", i + 1, len(libraries))
            await asyncio.sleep(0.1)  # 模拟下载
        return True