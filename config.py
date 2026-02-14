import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional

@dataclass
class LauncherConfig:
    """启动器配置"""
    game_dir: str = str(Path.home() / ".minecraft")
    java_path: str = ""
    memory_min: int = 1024
    memory_max: int = 4096
    window_width: int = 854
    window_height: int = 480
    fullscreen: bool = False
    use_bmclapi: bool = True
    download_threads: int = 8
    selected_version: str = ""
    auth_method: str = "offline"  # offline, mojang, authlib
    username: str = "Player"
    uuid: str = ""
    access_token: str = ""
    
    # 镜像源配置
    mirrors: Dict[str, str] = field(default_factory=lambda: {
        "version_manifest": "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json",
        "version_manifest_v2": "https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json",
        "assets": "https://bmclapi2.bangbang93.com/assets",
        "maven": "https://bmclapi2.bangbang93.com/maven",
        "libraries": "https://bmclapi2.bangbang93.com/maven",
        "resources": "https://bmclapi2.bangbang93.com/assets",
        "authlib": "https://bmclapi2.bangbang93.com/mirrors/authlib-injector",
        "fabric_meta": "https://bmclapi2.bangbang93.com/fabric-meta",
        "forge_maven": "https://bmclapi2.bangbang93.com/maven",
        "neoforge": "https://bmclapi2.bangbang93.com/maven/net/neoforged/forge",
        "liteloader": "https://bmclapi.bangbang93.com/maven/com/mumfrey/liteloader/versions.json",
    })

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "launcher_config.json"):
        self.config_path = Path(config_path)
        self.config = LauncherConfig()
        self.load()
    
    def load(self):
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_game_dir(self):
        """获取游戏目录"""
        return Path(self.config.game_dir)
    
    def get_versions_dir(self):
        """获取版本目录"""
        return self.get_game_dir() / "versions"
    
    def get_libraries_dir(self):
        """获取库目录"""
        return self.get_game_dir() / "libraries"
    
    def get_assets_dir(self):
        """获取资源目录"""
        return self.get_game_dir() / "assets"