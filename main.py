import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QPalette, QFont
import qasync
from ui_window import LauncherWindow

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
    def drawContents(self, painter):
        super().drawContents(painter)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, "Minecraft Launcher")

def setup_styles(app):
    """设置现代化样式"""
    # 设置字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # 深色调色板
    dark_palette = QPalette()
    
    # 基础颜色
    dark_palette.setColor(QPalette.Window, QColor(32, 32, 32))
    dark_palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Base, QColor(28, 28, 28))
    dark_palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    # 禁用状态颜色
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    
    app.setPalette(dark_palette)
    
    # 现代化样式表
    app.setStyleSheet("""
        /* 全局样式 */
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #2d2d30;
            border: 1px solid #3e3e40;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 28px;
            color: #ffffff;
        }
        
        QPushButton:hover {
            background-color: #3e3e40;
            border-color: #007acc;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
            border-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #252526;
            border-color: #3e3e40;
            color: #6e6e6e;
        }
        
        /* 主要操作按钮 */
        QPushButton.primary {
            background-color: #007acc;
            border-color: #007acc;
            font-weight: 600;
        }
        
        QPushButton.primary:hover {
            background-color: #1c97ea;
            border-color: #1c97ea;
        }
        
        QPushButton.primary:pressed {
            background-color: #005a9e;
            border-color: #005a9e;
        }
        
        /* 输入框样式 */
        QLineEdit, QTextEdit, QComboBox {
            background-color: #252526;
            border: 1px solid #3e3e40;
            border-radius: 4px;
            padding: 6px 8px;
            color: #ffffff;
            selection-background-color: #007acc;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #007acc;
            background-color: #2a2d2e;
        }
        
        QComboBox::drop-down {
            border: none;
            background-color: transparent;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #cccccc;
            margin-right: 8px;
        }
        
        /* 分组框 */
        QGroupBox {
            border: 1px solid #3e3e40;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
            background-color: #252526;
            font-weight: 600;
            color: #cccccc;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }
        
        /* 列表和树状视图 */
        QListWidget, QTreeWidget {
            background-color: #252526;
            border: 1px solid #3e3e40;
            border-radius: 4px;
            color: #ffffff;
            outline: none;
        }
        
        QListWidget::item, QTreeWidget::item {
            padding: 6px;
            border-radius: 2px;
        }
        
        QListWidget::item:selected, QTreeWidget::item:selected {
            background-color: #04395e;
            color: #ffffff;
        }
        
        QListWidget::item:hover, QTreeWidget::item:hover {
            background-color: #2a2d2e;
        }
        
        /* 标签页 */
        QTabWidget::pane {
            border: 1px solid #3e3e40;
            border-radius: 4px;
            background-color: #252526;
        }
        
        QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #252526;
            color: #ffffff;
            border-bottom: 2px solid #007acc;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #3e3e40;
        }
        
        /* 进度条 */
        QProgressBar {
            border: 1px solid #3e3e40;
            border-radius: 4px;
            text-align: center;
            background-color: #252526;
            color: #ffffff;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 3px;
        }
        
        /* 滚动条 */
        QScrollBar:vertical {
            background-color: #2d2d30;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4f4f4f;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6a6a6a;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* 分隔器 */
        QSplitter::handle {
            background-color: #3e3e40;
        }
        
        QSplitter::handle:hover {
            background-color: #007acc;
        }
        
        /* 工具提示 */
        QToolTip {
            background-color: #007acc;
            color: white;
            border: 1px solid #005a9e;
            border-radius: 4px;
            padding: 4px;
        }
        
        /* 复选框和单选框 */
        QCheckBox, QRadioButton {
            color: #ffffff;
            spacing: 8px;
        }
        
        QCheckBox::indicator, QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #3e3e40;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #007acc;
            border-color: #007acc;
            image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"><path fill="white" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>');
        }
        
        QRadioButton::indicator {
            border-radius: 9px;
        }
        
        QRadioButton::indicator:checked {
            background-color: #007acc;
            border-color: #007acc;
        }
    """)

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
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft Launcher")
    app.setApplicationVersion("2.0.0")
    app.setWindowIcon(app.style().standardIcon(app.style().SP_ComputerIcon))
    
    # 显示启动画面
    splash = SplashScreen()
    splash.show()
    
    # 设置现代化样式
    setup_styles(app)
    
    # 创建主窗口
    window = LauncherWindow()
    
    # 延迟显示主窗口并关闭启动画面
    QTimer.singleShot(1500, lambda: finish_startup(splash, window))
    
    # 使用qasync整合事件循环
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    with loop:
        sys.exit(loop.run_forever())

def finish_startup(splash, window):
    """完成启动过程"""
    window.show()
    window.showMaximized()  # 最大化显示
    splash.finish(window)

if __name__ == "__main__":
    main()