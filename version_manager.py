import json
import requests
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

@dataclass
class DownloadableFile:
    """可下载文件"""
    url: str
    sha1: str
    size: int
    path: Path

class VersionManager:
    """版本管理器"""
    
    def __init__(self, config):
        self.config = config
        self.versions: Dict[str, VersionInfo] = {}
        self.local_versions: List[str] = []
    
    async def fetch_version_manifest(self):
        """获取版本清单"""
        try:
            url = self.config.mirrors["version_manifest"]
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
        if versions_dir.exists():
            for version_dir in versions_dir.iterdir():
                if (version_dir / f"{version_dir.name}.json").exists():
                    self.local_versions.append(version_dir.name)
        return self.local_versions
    
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
        if self.config.use_bmclapi:
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
                        if self.config.use_bmclapi:
                            data = self._replace_mirrors_in_json(data)
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        return data
        except Exception as e:
            logger.error(f"下载版本JSON失败: {e}")
        return None
    
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
    
    async def get_forge_versions(self, minecraft_version: str) -> List[str]:
        """获取Forge版本列表"""
        try:
            url = f"{self.config.mirrors['forge_maven']}/net/minecraftforge/forge/{minecraft_version}/maven-metadata.xml"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # 解析XML获取版本
                        import xml.etree.ElementTree as ET
                        content = await response.text()
                        root = ET.fromstring(content)
                        versions = []
                        for version in root.findall(".//version"):
                            versions.append(version.text)
                        return versions
        except Exception as e:
            logger.error(f"获取Forge版本失败: {e}")
        return []
    
    async def get_fabric_versions(self) -> Dict[str, List[str]]:
        """获取Fabric版本列表"""
        try:
            url = f"{self.config.mirrors['fabric_meta']}/v2/versions"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
        except Exception as e:
            logger.error(f"获取Fabric版本失败: {e}")
        return {}