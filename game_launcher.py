import subprocess
import json
import platform
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class GameLauncher:
    """游戏启动器"""
    
    def __init__(self, config):
        self.config = config
    
    async def launch(self, version_id: str):
        """启动游戏"""
        try:
            version_dir = self.config.get_versions_dir() / version_id
            version_json = version_dir / f"{version_id}.json"
            
            if not version_json.exists():
                logger.error(f"版本JSON不存在: {version_json}")
                return False
            
            with open(version_json, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            # 构建启动命令
            cmd = self.build_launch_command(version_data, version_id)
            
            # 启动游戏
            process = subprocess.Popen(
                cmd,
                cwd=str(self.config.get_game_dir()),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            logger.info(f"游戏已启动 (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"启动游戏失败: {e}")
            return False
    
    def build_launch_command(self, version_data: Dict, version_id: str) -> List[str]:
        """构建启动命令"""
        cmd = []
        
        # Java路径
        java_path = self.config.config.java_path
        if not java_path:
            java_path = "java"  # 使用系统默认
        
        cmd.append(java_path)
        
        # 内存设置
        cmd.extend([
            f"-Xms{self.config.config.memory_min}M",
            f"-Xmx{self.config.config.memory_max}M",
            "-XX:+UseG1GC",
            "-XX:+ParallelRefProcEnabled",
            "-XX:MaxGCPauseMillis=200",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+DisableExplicitGC",
            "-XX:+AlwaysPreTouch",
            "-XX:G1NewSizePercent=30",
            "-XX:G1MaxNewSizePercent=40",
            "-XX:G1HeapRegionSize=8M",
            "-XX:G1ReservePercent=20",
            "-XX:G1HeapWastePercent=5",
            "-XX:G1MixedGCCountTarget=4",
            "-XX:InitiatingHeapOccupancyPercent=15",
            "-XX:G1MixedGCLiveThresholdPercent=90",
            "-XX:G1RSetUpdatingPauseTimePercent=5",
            "-XX:SurvivorRatio=32",
            "-XX:+PerfDisableSharedMem",
            "-XX:MaxTenuringThreshold=1",
            "-Dusing.aikars.flags=https://mcflags.emc.gs",
            "-Daikars.new.flags=true"
        ])
        
        # 主类
        main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")
        cmd.append(main_class)
        
        # 游戏参数
        cmd.extend([
            "--version", version_id,
            "--gameDir", str(self.config.get_game_dir()),
            "--assetsDir", str(self.config.get_assets_dir()),
            "--assetIndex", version_data.get("assets", version_id),
            "--username", self.config.config.username,
            "--uuid", self.config.config.uuid or "00000000-0000-0000-0000-000000000000",
            "--accessToken", self.config.config.access_token or "0",
            "--userType", "mojang" if self.config.config.access_token else "legacy",
            "--versionType", version_data.get("type", "release"),
            "--width", str(self.config.config.window_width),
            "--height", str(self.config.config.window_height),
            "--fullscreen" if self.config.config.fullscreen else ""
        ])
        
        # 移除空字符串
        cmd = [arg for arg in cmd if arg]
        
        return cmd