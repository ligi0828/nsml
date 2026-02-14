import sys
import asyncio
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QLineEdit,
    QTextEdit, QProgressBar, QTabWidget, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QSplitter,
    QFileDialog, QMessageBox, QApplication, QTreeWidget,
    QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
import qasync
from launcher_core import LauncherCore

class DownloadThread(QThread):
    """下载线程"""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(bool)
    log = pyqtSignal(str)
    
    def __init__(self, core, version_id):
        super().__init__()
        self.core = core
        self.version_id = version_id
    
    def run(self):
        """运行下载"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def download():
                self.log.emit(f"开始下载版本 {self.version_id}")
                
                # 下载版本JSON
                version_data = await self.core.download_version(self.version_id)
                if not version_data:
                    self.finished.emit(False)
                    return
                
                # 下载资源
                await self.core.download_assets(version_data, self.progress_callback)
                
                # 下载库文件
                await self.core.download_libraries(version_data, self.progress_callback)
                
                self.log.emit("下载完成！")
                self.finished.emit(True)
            
            loop.run_until_complete(download())
        except Exception as e:
            self.log.emit(f"下载出错: {e}")
            self.finished.emit(False)
    
    def progress_callback(self, url, downloaded, total):
        """进度回调"""
        self.progress.emit(url, downloaded, total)

class LauncherWindow(QMainWindow):
    """启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.core = LauncherCore()
        self.download_thread = None
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Minecraft启动器")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部：用户信息
        user_group = QGroupBox("用户信息")
        user_layout = QHBoxLayout()
        
        self.username_input = QLineEdit("Player")
        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItems(["离线模式", "正版登录", "Authlib"])
        
        user_layout.addWidget(QLabel("用户名:"))
        user_layout.addWidget(self.username_input)
        user_layout.addWidget(QLabel("认证方式:"))
        user_layout.addWidget(self.auth_method_combo)
        user_group.setLayout(user_layout)
        main_layout.addWidget(user_group)
        
        # 中间：版本选择和下载
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：版本列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.version_list = QTreeWidget()
        self.version_list.setHeaderLabels(["版本", "类型", "状态"])
        self.version_list.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        left_layout.addWidget(QLabel("可用版本:"))
        left_layout.addWidget(self.version_list)
        
        refresh_btn = QPushButton("刷新版本列表")
        refresh_btn.clicked.connect(self.refresh_versions)
        left_layout.addWidget(refresh_btn)
        
        # 右侧：版本详情和设置
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 版本信息
        info_group = QGroupBox("版本信息")
        info_layout = QVBoxLayout()
        self.version_info = QTextEdit()
        self.version_info.setReadOnly(True)
        info_layout.addWidget(self.version_info)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        # 启动设置
        settings_group = QGroupBox("启动设置")
        settings_layout = QVBoxLayout()
        
        # Java路径
        java_layout = QHBoxLayout()
        self.java_path_input = QLineEdit()
        java_browse_btn = QPushButton("浏览")
        java_browse_btn.clicked.connect(self.browse_java)
        java_layout.addWidget(QLabel("Java路径:"))
        java_layout.addWidget(self.java_path_input)
        java_layout.addWidget(java_browse_btn)
        settings_layout.addLayout(java_layout)
        
        # 内存设置
        memory_layout = QHBoxLayout()
        self.memory_min = QSpinBox()
        self.memory_min.setRange(256, 16384)
        self.memory_min.setValue(1024)
        self.memory_max = QSpinBox()
        self.memory_max.setRange(256, 16384)
        self.memory_max.setValue(4096)
        
        memory_layout.addWidget(QLabel("最小内存(MB):"))
        memory_layout.addWidget(self.memory_min)
        memory_layout.addWidget(QLabel("最大内存(MB):"))
        memory_layout.addWidget(self.memory_max)
        settings_layout.addLayout(memory_layout)
        
        # 窗口设置
        window_layout = QHBoxLayout()
        self.window_width = QSpinBox()
        self.window_width.setRange(100, 7680)
        self.window_width.setValue(854)
        self.window_height = QSpinBox()
        self.window_height.setRange(100, 4320)
        self.window_height.setValue(480)
        self.fullscreen_check = QCheckBox("全屏")
        
        window_layout.addWidget(QLabel("宽度:"))
        window_layout.addWidget(self.window_width)
        window_layout.addWidget(QLabel("高度:"))
        window_layout.addWidget(self.window_height)
        window_layout.addWidget(self.fullscreen_check)
        settings_layout.addLayout(window_layout)
        
        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)
        
        # 底部：进度和日志
        bottom_group = QGroupBox("进度和日志")
        bottom_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("就绪")
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        
        bottom_layout.addWidget(self.progress_label)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.log_output)
        bottom_group.setLayout(bottom_layout)
        main_layout.addWidget(bottom_group)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("安装版本")
        self.install_btn.clicked.connect(self.install_version)
        
        self.launch_btn = QPushButton("启动游戏")
        self.launch_btn.clicked.connect(self.launch_game)
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.launch_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
    
    def load_data(self):
        """加载数据"""
        # 加载配置
        self.java_path_input.setText(self.core.config.config.java_path)
        self.memory_min.setValue(self.core.config.config.memory_min)
        self.memory_max.setValue(self.core.config.config.memory_max)
        self.window_width.setValue(self.core.config.config.window_width)
        self.window_height.setValue(self.core.config.config.window_height)
        self.fullscreen_check.setChecked(self.core.config.config.fullscreen)
        self.username_input.setText(self.core.config.config.username)
        
        # 异步加载版本列表
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.refresh_versions)
    
    def refresh_versions(self):
        """刷新版本列表"""
        self.version_list.clear()
        
        # 添加已安装版本
        installed_item = QTreeWidgetItem(["已安装版本"])
        self.version_list.addTopLevelItem(installed_item)
        
        for version in self.core.get_installed_versions():
            item = QTreeWidgetItem([version, "已安装", "✓"])
            installed_item.addChild(item)
        
        # 异步获取在线版本
        async def fetch_versions():
            await self.core.fetch_versions()
            self.populate_version_list()
        
        # 安全地运行异步任务
        try:
            # 尝试获取当前运行的事件循环
            loop = asyncio.get_running_loop()
            # 如果成功，则直接创建任务
            loop.create_task(fetch_versions())
        except RuntimeError:
            # 如果没有运行的事件循环（例如在初始化时），
            # 则稍后在事件循环中执行
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: asyncio.run(fetch_versions()))
    
    def populate_version_list(self):
        """填充版本列表"""
        releases_item = QTreeWidgetItem(["正式版"])
        snapshots_item = QTreeWidgetItem(["快照版"])
        
        for version_id, version_info in self.core.version_manager.versions.items():
            item = QTreeWidgetItem([version_id, version_info.type, ""])
            
            if version_info.type == "release":
                releases_item.addChild(item)
            elif version_info.type == "snapshot":
                snapshots_item.addChild(item)
        
        self.version_list.addTopLevelItem(releases_item)
        self.version_list.addTopLevelItem(snapshots_item)
    
    def install_version(self):
        """安装版本"""
        selected = self.version_list.currentItem()
        if selected and selected.childCount() == 0:  # 不是父项目
            version_id = selected.text(0)
            self.start_download(version_id)
    
    def start_download(self, version_id):
        """开始下载"""
        if self.download_thread and self.download_thread.isRunning():
            return
        
        self.download_thread = DownloadThread(self.core, version_id)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.log.connect(self.log_message)
        self.download_thread.start()
        
        self.install_btn.setEnabled(False)
        self.progress_label.setText(f"正在下载 {version_id}")
    
    def update_progress(self, url, downloaded, total):
        """更新进度"""
        if total > 0:
            percent = int(downloaded / total * 100)
            self.progress_bar.setValue(percent)
    
    def download_finished(self, success):
        """下载完成"""
        self.install_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        if success:
            self.progress_label.setText("下载完成")
            QMessageBox.information(self, "成功", "版本安装完成！")
            self.refresh_versions()
        else:
            self.progress_label.setText("下载失败")
            QMessageBox.warning(self, "错误", "版本安装失败！")
    
    def launch_game(self):
        """启动游戏"""
        selected = self.version_list.currentItem()
        if not selected or selected.childCount() > 0:
            QMessageBox.warning(self, "错误", "请选择一个版本！")
            return
        
        version_id = selected.text(0)
        
        # 更新配置
        self.core.config.config.java_path = self.java_path_input.text()
        self.core.config.config.memory_min = self.memory_min.value()
        self.core.config.config.memory_max = self.memory_max.value()
        self.core.config.config.window_width = self.window_width.value()
        self.core.config.config.window_height = self.window_height.value()
        self.core.config.config.fullscreen = self.fullscreen_check.isChecked()
        self.core.config.config.username = self.username_input.text()
        self.core.config.save()
        
        # 启动游戏
        async def launch():
            success = await self.core.launch_game(version_id)
            if not success:
                QMessageBox.warning(self, "错误", "启动游戏失败！")
        
        asyncio.create_task(launch())
    
    def browse_java(self):
        """浏览Java路径"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择Java可执行文件", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self.java_path_input.setText(path)
    
    def open_settings(self):
        """打开设置对话框"""
        # 这里可以添加更多设置选项
        QMessageBox.information(self, "设置", "设置功能开发中...")
    
    def log_message(self, message):
        """记录日志消息"""
        self.log_output.append(message)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
        self.core.config.save()
        event.accept()