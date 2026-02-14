import sys
import asyncio
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QListWidget, QLabel, QLineEdit, QTextEdit,
    QProgressBar, QTabWidget, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QSplitter, QFileDialog, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QFormLayout, QStackedWidget,
    QFrame, QSizePolicy, QScrollArea, QToolBar, QStatusBar,
    QMenuBar, QMenu, QAction, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
import qasync
from launcher_core import LauncherCore

class DownloadThread(QThread):
    """下载线程"""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self, core, version_id):
        super().__init__()
        self.core = core
        self.version_id = version_id
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def download():
                self.status.emit(f"开始下载 {self.version_id}")
                self.log.emit(f"正在下载版本: {self.version_id}")
                
                # 下载版本JSON
                version_data = await self.core.download_version(self.version_id)
                if not version_data:
                    self.finished.emit(False, "下载版本信息失败")
                    return
                
                self.status.emit("下载资源文件...")
                await self.core.download_assets(version_data, self.progress_callback)
                
                self.status.emit("下载库文件...")
                await self.core.download_libraries(version_data, self.progress_callback)
                
                self.status.emit("下载完成")
                self.finished.emit(True, f"版本 {self.version_id} 安装完成")
            
            loop.run_until_complete(download())
        except Exception as e:
            self.log.emit(f"下载出错: {e}")
            self.finished.emit(False, str(e))

class ModernButton(QPushButton):
    """现代化按钮"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        
        # 添加悬停动画
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

class ModernLineEdit(QLineEdit):
    """现代化输入框"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #3e3e40;
                border-radius: 4px;
                background-color: #252526;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                background-color: #2a2d2e;
            }
        """)

class CardWidget(QFrame):
    """卡片部件"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: 600;
                    color: #cccccc;
                    margin-bottom: 12px;
                }
            """)
            layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

class LauncherWindow(QMainWindow):
    """启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.core = LauncherCore()
        self.download_thread = None
        self.current_downloads = {}
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Minecraft Launcher")
        self.setMinimumSize(1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部导航栏
        self.create_navbar(main_layout)
        
        # 主内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧边栏
        sidebar = self.create_sidebar()
        content_layout.addWidget(sidebar, 1)
        
        # 右侧主内容
        main_content = self.create_main_content()
        content_layout.addWidget(main_content, 3)
        
        main_layout.addWidget(content_widget)
        
        # 底部状态栏
        self.create_statusbar()
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
        """)
    
    def create_navbar(self, parent_layout):
        """创建导航栏"""
        navbar = QFrame()
        navbar.setFixedHeight(48)
        navbar.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-bottom: 1px solid #3e3e40;
            }
        """)
        
        nav_layout = QHBoxLayout(navbar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        
        # 标题
        title_label = QLabel("Minecraft Launcher")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #ffffff;
            }
        """)
        nav_layout.addWidget(title_label)
        
        nav_layout.addStretch()
        
        # 用户信息
        user_menu = QComboBox()
        user_menu.addItems(["离线模式", "正版登录", "微软账户"])
        user_menu.setFixedWidth(120)
        nav_layout.addWidget(user_menu)
        
        # 设置按钮
        settings_btn = ModernButton("⚙️")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.open_settings)
        nav_layout.addWidget(settings_btn)
        
        parent_layout.addWidget(navbar)
    
    def create_sidebar(self):
        """创建左侧边栏"""
        sidebar = CardWidget()
        sidebar.setFixedWidth(280)
        
        # 用户卡片
        user_card = CardWidget("用户信息")
        
        username_input = ModernLineEdit("玩家名称")
        username_input.setText(self.core.config.config.username)
        username_input.textChanged.connect(self.on_username_changed)
        
        user_card.content_layout.addWidget(username_input)
        
        # 版本管理卡片
        version_card = CardWidget("版本管理")
        
        refresh_btn = ModernButton("🔄 刷新版本列表")
        refresh_btn.setObjectName("primary")
        refresh_btn.clicked.connect(self.refresh_versions)
        
        install_btn = ModernButton("📥 安装新版本")
        install_btn.setObjectName("primary")
        install_btn.clicked.connect(self.install_version_dialog)
        
        version_card.content_layout.addWidget(refresh_btn)
        version_card.content_layout.addWidget(install_btn)
        
        # 已安装版本列表
        installed_card = CardWidget("已安装版本")
        
        self.installed_list = QListWidget()
        self.installed_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #3e3e40;
                border-radius: 4px;
                background-color: #252526;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3e3e40;
            }
            QListWidget::item:selected {
                background-color: #007acc;
            }
        """)
        installed_card.content_layout.addWidget(self.installed_list)
        
        # 布局
        sidebar.content_layout.addWidget(user_card)
        sidebar.content_layout.addWidget(version_card)
        sidebar.content_layout.addWidget(installed_card)
        sidebar.content_layout.addStretch()
        
        return sidebar
    
    def create_main_content(self):
        """创建主内容区域"""
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setSpacing(20)
        
        # 版本选择卡片
        version_select_card = CardWidget("选择游戏版本")
        
        self.version_tree = QTreeWidget()
        self.version_tree.setHeaderLabels(["版本", "类型", "发布日期"])
        self.version_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #3e3e40;
                border-radius: 4px;
                background-color: #252526;
                font-size: 14px;
            }
            QTreeWidget::item {
                height: 32px;
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)
        self.version_tree.itemDoubleClicked.connect(self.on_version_selected)
        
        version_select_card.content_layout.addWidget(self.version_tree)
        
        # 游戏设置卡片
        settings_card = CardWidget("游戏设置")
        
        settings_form = QFormLayout()
        settings_form.setSpacing(12)
        
        # Java路径
        java_layout = QHBoxLayout()
        self.java_path_input = ModernLineEdit("自动检测Java路径")
        java_browse_btn = ModernButton("浏览")
        java_browse_btn.setFixedWidth(80)
        java_browse_btn.clicked.connect(self.browse_java)
        java_layout.addWidget(self.java_path_input)
        java_layout.addWidget(java_browse_btn)
        settings_form.addRow("Java路径:", java_layout)
        
        # 内存设置
        memory_layout = QHBoxLayout()
        self.memory_min = QSpinBox()
        self.memory_min.setRange(512, 16384)
        self.memory_min.setValue(2048)
        self.memory_min.setSuffix(" MB")
        self.memory_min.setFixedWidth(120)
        
        self.memory_max = QSpinBox()
        self.memory_max.setRange(1024, 32768)
        self.memory_max.setValue(4096)
        self.memory_max.setSuffix(" MB")
        self.memory_max.setFixedWidth(120)
        
        memory_layout.addWidget(QLabel("最小:"))
        memory_layout.addWidget(self.memory_min)
        memory_layout.addWidget(QLabel("最大:"))
        memory_layout.addWidget(self.memory_max)
        memory_layout.addStretch()
        settings_form.addRow("内存分配:", memory_layout)
        
        # 游戏窗口设置
        window_layout = QHBoxLayout()
        self.window_width = QSpinBox()
        self.window_width.setRange(640, 7680)
        self.window_width.setValue(1280)
        self.window_width.setSuffix(" px")
        self.window_width.setFixedWidth(120)
        
        self.window_height = QSpinBox()
        self.window_height.setRange(480, 4320)
        self.window_height.setValue(720)
        self.window_height.setSuffix(" px")
        self.window_height.setFixedWidth(120)
        
        self.fullscreen_check = QCheckBox("全屏")
        
        window_layout.addWidget(QLabel("宽度:"))
        window_layout.addWidget(self.window_width)
        window_layout.addWidget(QLabel("高度:"))
        window_layout.addWidget(self.window_height)
        window_layout.addWidget(self.fullscreen_check)
        window_layout.addStretch()
        settings_form.addRow("窗口尺寸:", window_layout)
        
        settings_card.content_layout.addLayout(settings_form)
        
        # 启动按钮
        launch_card = CardWidget()
        launch_layout = QHBoxLayout()
        
        self.launch_btn = ModernButton("🚀 启动游戏")
        self.launch_btn.setObjectName("primary")
        self.launch_btn.setFixedHeight(48)
        self.launch_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: 600;
                background-color: #007acc;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1c97ea;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.launch_btn.clicked.connect(self.launch_game)
        
        launch_layout.addStretch()
        launch_layout.addWidget(self.launch_btn, 2)
        launch_layout.addStretch()
        
        launch_card.content_layout.addLayout(launch_layout)
        
        # 添加到主布局
        main_layout.addWidget(version_select_card, 3)
        main_layout.addWidget(settings_card, 2)
        main_layout.addWidget(launch_card, 1)
        
        return main_content
    
    def create_statusbar(self):
        """创建状态栏"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # 下载进度标签
        self.progress_label = QLabel("就绪")
        statusbar.addWidget(self.progress_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        statusbar.addWidget(self.progress_bar)
        
        # 状态消息
        self.status_label = QLabel("")
        statusbar.addPermanentWidget(self.status_label)
    
    def load_data(self):
        """加载数据"""
        # 加载配置
        config = self.core.config.config
        self.java_path_input.setText(config.java_path)
        self.memory_min.setValue(config.memory_min)
        self.memory_max.setValue(config.memory_max)
        self.window_width.setValue(config.window_width)
        self.window_height.setValue(config.window_height)
        self.fullscreen_check.setChecked(config.fullscreen)
        
        # 加载已安装版本
        self.load_installed_versions()
        
        # 延迟加载在线版本
        QTimer.singleShot(100, self.refresh_versions)
    
    def load_installed_versions(self):
        """加载已安装版本"""
        self.installed_list.clear()
        for version in self.core.get_installed_versions():
            self.installed_list.addItem(version)
    
    def refresh_versions(self):
        """刷新版本列表"""
        self.version_tree.clear()
        
        # 添加分类
        releases = QTreeWidgetItem(["正式版"])
        snapshots = QTreeWidgetItem(["快照版"])
        old_beta = QTreeWidgetItem(["旧测试版"])
        old_alpha = QTreeWidgetItem(["旧Alpha版"])
        
        # 异步获取版本
        async def fetch():
            await self.core.fetch_versions()
            
            for version_id, version_info in self.core.version_manager.versions.items():
                item = QTreeWidgetItem([version_id, version_info.type, version_info.release_time])
                
                if version_info.type == "release":
                    releases.addChild(item)
                elif version_info.type == "snapshot":
                    snapshots.addChild(item)
                elif version_info.type == "old_beta":
                    old_beta.addChild(item)
                elif version_info.type == "old_alpha":
                    old_alpha.addChild(item)
            
            self.version_tree.addTopLevelItem(releases)
            self.version_tree.addTopLevelItem(snapshots)
            self.version_tree.addTopLevelItem(old_beta)
            self.version_tree.addTopLevelItem(old_alpha)
            
            # 展开正式版
            releases.setExpanded(True)
        
        asyncio.create_task(fetch())
    
    def on_version_selected(self, item, column):
        """版本选择事件"""
        if item.childCount() == 0:  # 不是父项目
            version_id = item.text(0)
            self.status_label.setText(f"已选择: {version_id}")
    
    def install_version_dialog(self):
        """安装版本对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("安装新版本")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 版本选择
        version_combo = QComboBox()
        for version_id in self.core.version_manager.get_version_list():
            version_combo.addItem(version_id)
        
        layout.addWidget(QLabel("选择要安装的版本:"))
        layout.addWidget(version_combo)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.install_version(version_combo.currentText()))
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        dialog.exec_()
    
    def install_version(self, version_id):
        """安装版本"""
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "警告", "已有下载任务在进行中")
            return
        
        self.download_thread = DownloadThread(self.core, version_id)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.log.connect(self.log_message)
        self.download_thread.status.connect(self.status_label.setText)
        
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"正在下载 {version_id}...")
        self.download_thread.start()
    
    def update_progress(self, url, downloaded, total):
        """更新下载进度"""
        if total > 0:
            percent = int(downloaded / total * 100)
            self.progress_bar.setValue(percent)
    
    def download_finished(self, success, message):
        """下载完成"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        
        if success:
            self.progress_label.setText("下载完成")
            self.load_installed_versions()
            QMessageBox.information(self, "成功", message)
        else:
            self.progress_label.setText("下载失败")
            QMessageBox.warning(self, "错误", message)
    
    def launch_game(self):
        """启动游戏"""
        selected_items = self.version_tree.selectedItems()
        if not selected_items or selected_items[0].childCount() > 0:
            QMessageBox.warning(self, "错误", "请选择一个游戏版本")
            return
        
        version_id = selected_items[0].text(0)
        
        # 保存配置
        config = self.core.config.config
        config.java_path = self.java_path_input.text()
        config.memory_min = self.memory_min.value()
        config.memory_max = self.memory_max.value()
        config.window_width = self.window_width.value()
        config.window_height = self.window_height.value()
        config.fullscreen = self.fullscreen_check.isChecked()
        self.core.config.save()
        
        # 启动游戏
        self.progress_label.setText("正在启动游戏...")
        self.launch_btn.setEnabled(False)
        
        async def launch():
            success = await self.core.launch_game(version_id)
            self.launch_btn.setEnabled(True)
            if not success:
                self.progress_label.setText("启动失败")
                QMessageBox.warning(self, "错误", "启动游戏失败")
            else:
                self.progress_label.setText("游戏已启动")
        
        asyncio.create_task(launch())
    
    def browse_java(self):
        """浏览Java路径"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择Java可执行文件", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self.java_path_input.setText(path)
    
    def open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "设置", "设置对话框开发中...")
    
    def on_username_changed(self, text):
        """用户名改变"""
        self.core.config.config.username = text
        self.core.config.save()
    
    def log_message(self, message):
        """记录日志消息"""
        print(f"[LOG] {message}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
        
        self.core.config.save()
        event.accept()