import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui_window import LauncherWindow

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('launcher.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    setup_logging()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft启动器")
    app.setApplicationVersion("1.0.0")
    
    # 设置样式
    app.setStyle('Fusion')
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()