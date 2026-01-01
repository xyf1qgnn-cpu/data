"""
CFST Data Extractor GUI 主应用程序
基于PySide6的图形用户界面
"""

import sys
import os
import traceback
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QStatusBar,
    QMenuBar, QMenu, QSplitter, QFrame
)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont

# 导入自定义组件
from config_manager import ConfigManager
from secure_storage import SecureStorage
from processing_thread import ProcessingThread
from widgets.api_key_widget import ApiKeyWidget
from widgets.progress_widget import ProgressWidget
from widgets.dual_output_widget import DualOutputWidget


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 初始化组件
        self.config_manager = ConfigManager()
        self.secure_storage = SecureStorage()
        self.processing_thread = None
        self.current_directory = ""

        # 设置窗口属性
        self.setWindowTitle("CFST Data Extractor")
        self.setMinimumSize(1000, 700)

        # 创建UI
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.connect_signals()

        # 加载设置
        self.load_settings()

        # 设置应用程序图标
        self.set_app_icon()

    def setup_ui(self):
        """设置UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # API密钥组件
        self.api_key_widget = ApiKeyWidget()
        main_layout.addWidget(self.api_key_widget)

        # 文件选择区域
        file_frame = QFrame()
        file_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(15, 15, 15, 15)
        file_layout.setSpacing(10)

        # 文件选择标题
        file_title = QLabel("PDF File Selection")
        file_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1565C0;")
        file_layout.addWidget(file_title)

        # 文件选择控件
        file_control_layout = QHBoxLayout()
        file_control_layout.setSpacing(10)

        self.dir_label = QLabel("Directory: Not selected")
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
        file_control_layout.addWidget(self.dir_label, 3)

        self.select_dir_btn = QPushButton("Select Directory")
        self.select_dir_btn.setFixedWidth(120)
        file_control_layout.addWidget(self.select_dir_btn)

        self.file_count_label = QLabel("Files: 0")
        self.file_count_label.setFixedWidth(80)
        self.file_count_label.setAlignment(Qt.AlignCenter)
        self.file_count_label.setStyleSheet("font-weight: bold; color: #1565C0;")
        file_control_layout.addWidget(self.file_count_label)

        file_layout.addLayout(file_control_layout)

        main_layout.addWidget(file_frame)

        # 进度组件
        self.progress_widget = ProgressWidget()
        main_layout.addWidget(self.progress_widget)

        # 双输出组件
        self.output_widget = DualOutputWidget()
        main_layout.addWidget(self.output_widget, 1)  # 给予更多空间

        # 控制按钮区域
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(20)

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setFixedWidth(140)
        self.start_btn.setEnabled(False)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedWidth(100)
        self.pause_btn.setEnabled(False)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setFixedWidth(100)
        self.resume_btn.setEnabled(False)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.setEnabled(False)

        control_layout.addStretch()
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.cancel_btn)
        control_layout.addStretch()

        main_layout.addWidget(control_frame)

    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Directory", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_directory)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 处理菜单
        process_menu = menubar.addMenu("Process")

        start_action = QAction("Start Processing", self)
        start_action.setShortcut("F5")
        start_action.triggered.connect(self.start_processing)
        process_menu.addAction(start_action)

        pause_action = QAction("Pause", self)
        pause_action.setShortcut("F6")
        pause_action.triggered.connect(self.pause_processing)
        process_menu.addAction(pause_action)

        resume_action = QAction("Resume", self)
        resume_action.setShortcut("F7")
        resume_action.triggered.connect(self.resume_processing)
        process_menu.addAction(resume_action)

        cancel_action = QAction("Cancel", self)
        cancel_action.setShortcut("F8")
        cancel_action.triggered.connect(self.cancel_processing)
        process_menu.addAction(cancel_action)

        # 设置菜单
        settings_menu = menubar.addMenu("Settings")

        api_settings_action = QAction("API Settings", self)
        api_settings_action.triggered.connect(self.show_api_settings)
        settings_menu.addAction(api_settings_action)

        processing_settings_action = QAction("Processing Settings", self)
        processing_settings_action.triggered.connect(self.show_processing_settings)
        settings_menu.addAction(processing_settings_action)

        ui_settings_action = QAction("UI Settings", self)
        ui_settings_action.triggered.connect(self.show_ui_settings)
        settings_menu.addAction(ui_settings_action)

        settings_menu.addSeparator()

        reset_settings_action = QAction("Reset Settings", self)
        reset_settings_action.triggered.connect(self.reset_settings)
        settings_menu.addAction(reset_settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        help_action = QAction("Help Documentation", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)

        # 内存使用标签
        self.memory_label = QLabel("Memory: --")
        self.status_bar.addPermanentWidget(self.memory_label)

        # 更新时间显示
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status_bar)
        self.update_timer.start(5000)  # 每5秒更新一次

    def connect_signals(self):
        """连接信号"""
        # 按钮信号
        self.select_dir_btn.clicked.connect(self.select_directory)
        self.start_btn.clicked.connect(self.start_processing)
        self.pause_btn.clicked.connect(self.pause_processing)
        self.resume_btn.clicked.connect(self.resume_processing)
        self.cancel_btn.clicked.connect(self.cancel_processing)

        # API密钥组件信号
        self.api_key_widget.api_key_changed.connect(self.on_api_key_changed)
        self.api_key_widget.api_key_tested.connect(self.on_api_key_tested)

        # 输出组件信号
        self.output_widget.export_requested.connect(self.on_export_requested)

    def load_settings(self):
        """加载设置"""
        try:
            # 加载窗口几何信息
            geometry = self.config_manager.get_window_geometry()
            self.resize(geometry['width'], geometry['height'])
            self.move(geometry['x'], geometry['y'])

            # 加载最后使用的目录
            last_dir = self.config_manager.get_last_directory()
            if last_dir and os.path.exists(last_dir):
                self.current_directory = last_dir
                self.update_directory_display()

            # 加载API密钥
            self.load_api_key()

            # 更新状态
            self.update_status("设置已加载")

        except Exception as e:
            self.output_widget.append_error(f"加载设置失败: {str(e)}", "CONFIG_ERROR")

    def save_settings(self):
        """保存设置"""
        try:
            # 保存窗口几何信息
            self.config_manager.set_window_geometry(
                self.width(), self.height(),
                self.x(), self.y()
            )

            # 保存当前目录
            if self.current_directory:
                self.config_manager.set_last_directory(self.current_directory)

            # 保存配置
            self.config_manager.save_config()

        except Exception as e:
            self.output_widget.append_error(f"保存设置失败: {str(e)}", "CONFIG_ERROR")

    def set_app_icon(self):
        """设置应用程序图标"""
        try:
            icon_path = "resources/app.ico"
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置图标失败: {e}")

    def select_directory(self):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select PDF File Directory",
            self.current_directory if self.current_directory else ".",
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.current_directory = directory
            self.update_directory_display()
            self.config_manager.set_last_directory(directory)

    def update_directory_display(self):
        """更新目录显示"""
        if not self.current_directory:
            return

        # 更新目录标签
        self.dir_label.setText(f"Directory: {self.current_directory}")

        # 统计PDF文件数量
        pdf_count = 0
        try:
            for filename in os.listdir(self.current_directory):
                if filename.lower().endswith('.pdf'):
                    pdf_count += 1
        except Exception as e:
            self.output_widget.append_error(f"Failed to count files: {str(e)}", "FILE_ERROR")
            pdf_count = 0

        self.file_count_label.setText(f"Files: {pdf_count}")

        # 更新开始按钮状态
        has_api_key = bool(self.api_key_widget.get_api_key())
        self.start_btn.setEnabled(pdf_count > 0 and has_api_key)

        # 更新状态
        if pdf_count > 0:
            self.update_status(f"Found {pdf_count} PDF files")
        else:
            self.update_status("No PDF files in directory")

    def on_api_key_changed(self, api_key: str):
        """API密钥变化处理"""
        has_api_key = bool(api_key)
        has_directory = self.file_count_label.text() != "Files: 0"

        self.start_btn.setEnabled(has_api_key and has_directory)

        if has_api_key:
            self.update_status("API key entered")
        else:
            self.update_status("Please enter API key")

    def on_api_key_tested(self, success: bool, message: str):
        """API密钥测试结果处理"""
        if success:
            self.output_widget.append_log(f"API key test successful: {message}", "INFO")
            self.update_status("API key test passed")
        else:
            self.output_widget.append_error(f"API key test failed: {message}", "API_ERROR")
            self.update_status("API key test failed")

    def start_processing(self):
        """开始处理"""
        # 检查条件
        if not self.current_directory:
            QMessageBox.warning(self, "Warning", "Please select PDF file directory first")
            return

        if not self.api_key_widget.get_api_key():
            QMessageBox.warning(self, "Warning", "Please enter API key")
            return

        # 确认开始
        reply = QMessageBox.question(
            self,
            "Confirm Start",
            f"Start processing {self.file_count_label.text()} PDF files?\n\n"
            "Processing may take some time, please ensure network connection is normal.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 准备配置
            config = {
                **self.config_manager.get_processing_config(),
                **self.config_manager.get_api_config(),
                **self.config_manager.get_directory_config()
            }

            # 创建处理线程
            self.processing_thread = ProcessingThread(
                pdf_directory=self.current_directory,
                api_key=self.api_key_widget.get_api_key(),
                config=config
            )

            # 连接线程信号
            self.connect_thread_signals()

            # 更新UI状态
            self.set_processing_ui_state(True)

            # 获取文件数量
            pdf_files = []
            for filename in os.listdir(self.current_directory):
                if filename.lower().endswith('.pdf'):
                    pdf_files.append(filename)

            # 启动进度显示
            self.progress_widget.start_processing(len(pdf_files))

            # 开始处理
            self.processing_thread.start()

            self.output_widget.append_log(f"Started processing {len(pdf_files)} PDF files", "INFO")
            self.update_status("Processing in progress...")

        except Exception as e:
            self.output_widget.append_error(f"启动处理失败: {str(e)}", "PROCESS_ERROR")
            self.update_status("启动失败")

    def connect_thread_signals(self):
        """连接线程信号"""
        if not self.processing_thread:
            return

        # 进度信号
        self.processing_thread.progress_updated.connect(self.on_progress_updated)
        self.processing_thread.file_progress.connect(self.on_file_progress)
        self.processing_thread.overall_progress.connect(self.on_overall_progress)

        # 日志信号
        self.processing_thread.log_info.connect(lambda msg: self.output_widget.append_log(msg, "INFO"))
        self.processing_thread.log_warning.connect(lambda msg: self.output_widget.append_log(msg, "WARNING"))
        self.processing_thread.log_error.connect(lambda msg: self.output_widget.append_error(msg, "THREAD_ERROR"))
        self.processing_thread.log_debug.connect(lambda msg: self.output_widget.append_log(msg, "DEBUG"))

        # 文件状态信号
        self.processing_thread.file_started.connect(self.on_file_started)
        self.processing_thread.file_completed.connect(self.on_file_completed)
        self.processing_thread.file_excluded.connect(self.on_file_excluded)
        self.processing_thread.file_failed.connect(self.on_file_failed)

        # 处理状态信号
        self.processing_thread.processing_started.connect(self.on_processing_started)
        self.processing_thread.processing_paused.connect(self.on_processing_paused)
        self.processing_thread.processing_resumed.connect(self.on_processing_resumed)
        self.processing_thread.processing_cancelled.connect(self.on_processing_cancelled)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)

        # 验证信号
        self.processing_thread.validation_update.connect(self.on_validation_update)
        self.processing_thread.anomaly_detected.connect(self.on_anomaly_detected)

    def on_progress_updated(self, current: int, total: int):
        """进度更新处理"""
        self.progress_widget.update_overall_progress(current, total)

    def on_file_progress(self, filename: str, progress: int):
        """文件进度更新处理"""
        self.progress_widget.update_file_progress(filename, progress)

    def on_overall_progress(self, current: int, total: int, status: str):
        """总体进度更新处理"""
        # 可以在这里添加额外的处理
        pass

    def on_file_started(self, filename: str):
        """文件开始处理"""
        self.output_widget.append_log(f"开始处理: {filename}", "INFO")

    def on_file_completed(self, filename: str, success: bool, message: str):
        """文件完成处理"""
        self.progress_widget.update_file_status(filename, success, message)

        if success:
            self.output_widget.append_log(f"完成: {filename} - {message}", "INFO")
        else:
            self.output_widget.append_error(f"失败: {filename} - {message}", "FILE_ERROR")

    def on_file_excluded(self, filename: str, reason: str):
        """文件被排除"""
        self.output_widget.append_log(f"排除: {filename} - {reason}", "WARNING")

    def on_file_failed(self, filename: str, reason: str):
        """文件处理失败"""
        self.output_widget.append_error(f"失败: {filename} - {reason}", "FILE_ERROR")

    def on_processing_started(self):
        """处理开始"""
        self.output_widget.append_log("处理线程已启动", "INFO")

    def on_processing_paused(self):
        """处理暂停"""
        self.set_processing_ui_state(False, paused=True)
        self.output_widget.append_log("处理已暂停", "WARNING")
        self.update_status("处理已暂停")

    def on_processing_resumed(self):
        """处理恢复"""
        self.set_processing_ui_state(True)
        self.output_widget.append_log("处理已恢复", "INFO")
        self.update_status("处理恢复中...")

    def on_processing_cancelled(self):
        """处理取消"""
        self.set_processing_ui_state(False)
        self.progress_widget.cancel_processing()
        self.output_widget.append_log("处理已取消", "WARNING")
        self.update_status("处理已取消")

    def on_processing_finished(self, results: dict):
        """处理完成"""
        self.set_processing_ui_state(False)

        if results.get("success", False):
            success_count = results.get("successful_files", 0)
            failed_count = results.get("failed_files", 0)
            excluded_count = results.get("excluded_files", 0)

            self.progress_widget.finish_processing(success_count, failed_count)

            summary = (
                f"处理完成！\n"
                f"成功: {success_count}, 失败: {failed_count}, 排除: {excluded_count}\n"
                f"总时间: {results.get('processing_time_seconds', 0):.1f}秒"
            )

            self.output_widget.append_log(summary, "INFO")

            if results.get("excel_path"):
                self.output_widget.append_log(f"结果已保存到: {results['excel_path']}", "INFO")

            # 显示完成对话框
            QMessageBox.information(self, "处理完成", summary)
            self.update_status("处理完成")

        else:
            error_msg = results.get("error", "未知错误")
            self.output_widget.append_error(f"处理失败: {error_msg}", "PROCESS_ERROR")
            self.update_status("处理失败")

        # 清理线程
        self.processing_thread = None

    def on_validation_update(self, validation_info: dict):
        """验证更新处理"""
        # 可以在这里处理验证信息
        pass

    def on_anomaly_detected(self, anomaly_info: dict):
        """异常检测处理"""
        self.output_widget.append_log(f"检测到异常: {anomaly_info}", "WARNING")

    def pause_processing(self):
        """暂停处理"""
        if self.processing_thread:
            self.processing_thread.pause_processing()

    def resume_processing(self):
        """恢复处理"""
        if self.processing_thread:
            self.processing_thread.resume_processing()

    def cancel_processing(self):
        """取消处理"""
        if not self.processing_thread:
            return

        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消当前处理吗？\n\n"
            "已处理的文件将保留，未处理的文件将停止。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.processing_thread.cancel_processing()

    def set_processing_ui_state(self, is_processing: bool, paused: bool = False):
        """设置处理UI状态"""
        self.start_btn.setEnabled(not is_processing)
        self.pause_btn.setEnabled(is_processing and not paused)
        self.resume_btn.setEnabled(is_processing and paused)
        self.cancel_btn.setEnabled(is_processing)
        self.select_dir_btn.setEnabled(not is_processing)
        self.api_key_widget.set_read_only(is_processing)

        if paused:
            self.progress_widget.pause_processing()
        elif is_processing:
            self.progress_widget.resume_processing()

    def update_status(self, message: str):
        """更新状态"""
        self.status_label.setText(message)

    def update_status_bar(self):
        """更新状态栏"""
        # 更新内存使用
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"内存: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("内存: N/A")
        except Exception:
            pass

    def load_api_key(self):
        """加载API密钥"""
        try:
            api_key = self.secure_storage.load_api_key()
            if api_key:
                self.api_key_widget.set_api_key(api_key)
                self.output_widget.append_log("API密钥已从安全存储加载", "INFO")
        except Exception as e:
            self.output_widget.append_error(f"加载API密钥失败: {str(e)}", "SECURITY_ERROR")

    def on_export_requested(self, export_type: str):
        """导出请求处理"""
        if export_type == 'log':
            content = self.output_widget.get_log_content()
            default_name = f"cfst_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            content = self.output_widget.get_error_content()
            default_name = f"cfst_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        if not content.strip():
            QMessageBox.warning(self, "警告", "没有内容可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出{export_type}",
            default_name,
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.output_widget.append_log(f"{export_type}已导出到: {file_path}", "INFO")
            except Exception as e:
                self.output_widget.append_error(f"导出失败: {str(e)}", "EXPORT_ERROR")

    def show_api_settings(self):
        """显示API设置"""
        # 这里可以打开API设置对话框
        QMessageBox.information(self, "API设置", "API设置功能开发中...")

    def show_processing_settings(self):
        """显示处理设置"""
        # 这里可以打开处理设置对话框
        QMessageBox.information(self, "处理设置", "处理设置功能开发中...")

    def show_ui_settings(self):
        """显示界面设置"""
        # 这里可以打开界面设置对话框
        QMessageBox.information(self, "界面设置", "界面设置功能开发中...")

    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置吗？\n\n"
            "这将恢复所有设置为默认值，但不会删除已保存的API密钥。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.config_manager.reset_to_defaults()
                self.load_settings()
                self.output_widget.append_log("设置已重置为默认值", "INFO")
                QMessageBox.information(self, "重置成功", "设置已重置为默认值")
            except Exception as e:
                self.output_widget.append_error(f"重置设置失败: {str(e)}", "CONFIG_ERROR")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        CFST Data Extractor v1.0

        钢管混凝土实验数据提取工具

        功能：
        - 批量处理PDF文件
        - 使用AI提取结构化数据
        - 物理公式验证
        - 导出带样式的Excel文件

        技术栈：
        - Python 3.8+
        - PySide6 (Qt for Python)
        - DeepSeek AI API
        - PyInstaller 打包

        版权所有 © 2026
        仅供学术研究使用
        """

        QMessageBox.about(self, "关于 CFST Data Extractor", about_text)

    def show_help(self):
        """显示帮助"""
        help_text = """
        CFST Data Extractor 使用帮助

        1. 基本流程：
           a. 输入DeepSeek API密钥
           b. 选择包含PDF文件的目录
           c. 点击"开始处理"
           d. 查看进度和结果

        2. API密钥：
           - 从DeepSeek官网获取API密钥
           - 密钥以"sk-"开头
           - 密钥将加密存储确保安全

        3. 文件处理：
           - 支持批量处理PDF文件
           - 自动提取实验数据
           - 应用物理公式验证
           - 生成Excel格式结果

        4. 输出说明：
           - 成功文件：提取数据并验证
           - 失败文件：移动到NotInput目录
           - 排除文件：移动到Excluded目录

        5. 常见问题：
           - 确保网络连接正常
           - API密钥有足够额度
           - PDF文件格式正确

        更多帮助请参考用户手册。
        """

        QMessageBox.information(self, "使用帮助", help_text)

    def closeEvent(self, event):
        """关闭事件处理"""
        # 保存设置
        self.save_settings()

        # 如果有处理线程正在运行，询问是否取消
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "处理线程正在运行，确定要退出吗？\n\n"
                "退出将取消当前处理。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.processing_thread:
                    self.processing_thread.cancel_processing()
                    self.processing_thread.wait(2000)  # 等待2秒
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("CFST Data Extractor")
    app.setOrganizationName("CFST Research")

    # 设置字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()