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
                universal_newlines=True
            )
            
            # 记录输出
            async def log_output():
                for line in process.stdout:
                    logger.info(f"Minecraft: {line.strip()}")
                for line in process.stderr:
                    logger.error(f"Minecraft Error: {line.strip()}")
            
            import asyncio
            asyncio.create_task(log_output())
            
            return True
            
        except Exception as e:
            logger.error(f"启动游戏失败: {e}")
            return False
    
    def build_launch_command(self, version_data: Dict, version_id: str) -> List[str]:
        """构建启动命令"""
        cmd = []
        
        # Java路径
        java_path = self.config.config.java_path
        if not java_path or not Path(java_path).exists():
            # 自动查找Java
            java_path = self.find_java()
        
        if not java_path:
            raise Exception("未找到Java运行时环境")
        
        cmd.append(java_path)
        
        # JVM参数
        jvm_args = version_data.get("arguments", {}).get("jvm", [])
        for arg in jvm_args:
            if isinstance(arg, str):
                cmd.append(self.replace_placeholders(arg, version_data, version_id))
        
        # 自定义JVM参数
        cmd.extend([
            f"-Xms{self.config.config.memory_min}M",
            f"-Xmx{self.config.config.memory_max}M",
            "-Dfml.ignoreInvalidMinecraftCertificates=true",
            "-Dfml.ignorePatchDiscrepancies=true"
        ])
        
        # 主类
        main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")
        cmd.append(main_class)
        
        # 游戏参数
        game_args = version_data.get("arguments", {}).get("game", [])
        if not game_args:  # 旧版本格式
            game_args = version_data.get("minecraftArguments", "").split()
        
        for arg in game_args if isinstance(game_args, list) else game_args:
            if isinstance(arg, str):
                cmd.append(self.replace_placeholders(arg, version_data, version_id))
        
        return cmd
    
    def replace_placeholders(self, arg: str, version_data: Dict, version_id: str) -> str:
        """替换占位符"""
        replacements = {
            "${version_name}": version_id,
            "${game_directory}": str(self.config.get_game_dir()),
            "${assets_root}": str(self.config.get_assets_dir()),
            "${assets_index_name}": version_data.get("assets", version_id),
            "${auth_player_name}": self.config.config.username,
            "${auth_uuid}": self.config.config.uuid or "00000000-0000-0000-0000-000000000000",
            "${auth_access_token}": self.config.config.access_token or "0",
            "${user_type}": "mojang" if self.config.config.access_token else "legacy",
            "${version_type}": version_data.get("type", "release"),
            "${resolution_width}": str(self.config.config.window_width),
            "${resolution_height}": str(self.config.config.window_height),
            "${game_assets}": str(self.config.get_assets_dir()),
            "${classpath}": self.build_classpath(version_data, version_id),
        }
        
        for placeholder, value in replacements.items():
            arg = arg.replace(placeholder, value)
        
        return arg
    
    def build_classpath(self, version_data: Dict, version_id: str) -> str:
        """构建类路径"""
        libraries = version_data.get("libraries", [])
        classpath_parts = []
        
        for lib in libraries:
            downloads = lib.get("downloads", {})
            artifact = downloads.get("artifact")
            if artifact:
                path = self.config.get_libraries_dir() / artifact["path"]
                if path.exists():
                    classpath_parts.append(str(path))
        
        # 添加客户端jar
        client_jar = self.config.get_versions_dir() / version_id / f"{version_id}.jar"
        if client_jar.exists():
            classpath_parts.append(str(client_jar))
        
        # 根据系统使用不同的分隔符
        if platform.system() == "Windows":
            return ";".join(classpath_parts)
        else:
            return ":".join(classpath_parts)
    
    def find_java(self) -> str:
        """查找Java"""
        system = platform.system()
        
        if system == "Windows":
            # 在Windows上查找Java
            possible_paths = [
                "java",
                "javaw",
                "C:\\Program Files\\Java\\jre-*\\bin\\java.exe",
                "C:\\Program Files\\Java\\jdk-*\\bin\\java.exe",
            ]
        elif system == "Darwin":
            possible_paths = [
                "java",
                "/usr/bin/java",
                "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Home/bin/java",
            ]
        else:  # Linux
            possible_paths = [
                "java",
                "/usr/bin/java",
                "/usr/lib/jvm/*/bin/java",
            ]
        
        import shutil
        for path in possible_paths:
            if "*" in path:
                import glob
                for expanded in glob.glob(path):
                    if Path(expanded).exists():
                        return expanded
            else:
                found = shutil.which(path)
                if found:
                    return found
        
        return ""