import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

def calculate_sha1(filepath: Path) -> Optional[str]:
    """计算文件的SHA1哈希值"""
    try:
        sha1 = hashlib.sha1()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()
    except Exception:
        return None

def read_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """读取JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def write_json(filepath: Path, data: Dict[str, Any]):
    """写入JSON文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def extract_zip(zip_path: Path, extract_to: Path):
    """解压ZIP文件"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception:
        return False

def get_platform_string() -> str:
    """获取平台字符串"""
    import platform
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == "windows":
        if "64" in arch:
            return "windows-64"
        else:
            return "windows-32"
    elif system == "linux":
        if "64" in arch:
            return "linux-64"
        else:
            return "linux-32"
    elif system == "darwin":
        return "osx"
    else:
        return "unknown"