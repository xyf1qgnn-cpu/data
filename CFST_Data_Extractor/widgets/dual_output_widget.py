"""
双输出区域组件 - 显示日志和错误信息
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QColor, QFont


class DualOutputWidget(QWidget):
    """双输出区域组件，显示日志和错误信息"""

    # 信号定义
    log_cleared = Signal()
    error_cleared = Signal()
    export_requested = Signal(str)  # 导出类型：'log' 或 'error'

    def __init__(self, parent=None):
        """初始化双输出区域组件"""
        super().__init__(parent)

        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(5, 5, 5, 5)

        self.log_label = QLabel("处理日志")
        self.log_label.setStyleSheet("font-weight: bold; color: #2E7D32;")
        title_layout.addWidget(self.log_label)

        title_layout.addStretch()

        self.error_label = QLabel("错误信息")
        self.error_label.setStyleSheet("font-weight: bold; color: #C62828;")
        title_layout.addWidget(self.error_label)

        main_layout.addLayout(title_layout)

        # 分割区域
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 日志区域
        self.log_widget = self.create_text_edit("log")
        self.splitter.addWidget(self.log_widget)

        # 错误区域
        self.error_widget = self.create_text_edit("error")
        self.splitter.addWidget(self.error_widget)

        # 设置初始分割比例
        self.splitter.setSizes([400, 400])

        main_layout.addWidget(self.splitter)

        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)

        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.export_log_btn = QPushButton("导出日志")
        self.export_log_btn.clicked.connect(lambda: self.export_requested.emit('log'))

        log_control_layout.addWidget(self.clear_log_btn)
        log_control_layout.addWidget(self.export_log_btn)
        log_control_layout.addStretch()

        # 错误控制按钮
        error_control_layout = QHBoxLayout()
        self.clear_error_btn = QPushButton("清空错误")
        self.clear_error_btn.clicked.connect(self.clear_error)
        self.export_error_btn = QPushButton("导出错误")
        self.export_error_btn.clicked.connect(lambda: self.export_requested.emit('error'))

        error_control_layout.addStretch()
        error_control_layout.addWidget(self.clear_error_btn)
        error_control_layout.addWidget(self.export_error_btn)

        control_layout.addLayout(log_control_layout)
        control_layout.addLayout(error_control_layout)

        main_layout.addLayout(control_layout)

    def create_text_edit(self, widget_type: str) -> QTextEdit:
        """创建文本编辑控件"""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)
        text_edit.setFont(QFont("Consolas", 9))

        # 设置最大长度（防止内存占用过大）
        text_edit.document().setMaximumBlockCount(10000)

        if widget_type == "log":
            text_edit.setPlaceholderText("处理日志将显示在这里...")
        else:
            text_edit.setPlaceholderText("错误信息将显示在这里...")

        return text_edit

    def setup_styles(self):
        """设置样式"""
        # 日志区域样式
        self.log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #F1F8E9;
                border: 1px solid #C5E1A5;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit:focus {
                border: 1px solid #7CB342;
            }
        """)

        # 错误区域样式
        self.error_widget.setStyleSheet("""
            QTextEdit {
                background-color: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit:focus {
                border: 1px solid #EF5350;
            }
        """)

        # 按钮样式
        button_style = """
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #BDBDBD;
                border-radius: 3px;
                background-color: #FAFAFA;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """
        self.clear_log_btn.setStyleSheet(button_style)
        self.export_log_btn.setStyleSheet(button_style)
        self.clear_error_btn.setStyleSheet(button_style)
        self.export_error_btn.setStyleSheet(button_style)

    def append_log(self, message: str, level: str = "INFO"):
        """
        添加日志消息

        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
        """
        timestamp = self.get_timestamp()
        formatted_message = f"[{timestamp}] [{level}] {message}"

        # 根据级别设置颜色
        if level == "INFO":
            color = "#2E7D32"  # 绿色
        elif level == "WARNING":
            color = "#F57C00"  # 橙色
        elif level == "ERROR":
            color = "#C62828"  # 红色
        elif level == "DEBUG":
            color = "#546E7A"  # 灰色
        else:
            color = "#000000"  # 黑色

        # 添加带颜色的文本
        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 插入带格式的文本
        self.log_widget.setTextColor(QColor(color))
        self.log_widget.append(formatted_message)

        # 自动滚动到底部
        self.log_widget.ensureCursorVisible()

    def append_error(self, message: str, error_type: str = "ERROR"):
        """
        添加错误消息

        Args:
            message: 错误消息
            error_type: 错误类型
        """
        timestamp = self.get_timestamp()
        formatted_message = f"[{timestamp}] [{error_type}] {message}"

        # 添加错误消息
        cursor = self.error_widget.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 设置红色文本
        self.error_widget.setTextColor(QColor("#C62828"))
        self.error_widget.append(formatted_message)

        # 自动滚动到底部
        self.error_widget.ensureCursorVisible()

    def clear_log(self):
        """清空日志区域"""
        self.log_widget.clear()
        self.log_cleared.emit()

    def clear_error(self):
        """清空错误区域"""
        self.error_widget.clear()
        self.error_cleared.emit()

    def get_log_content(self) -> str:
        """获取日志内容"""
        return self.log_widget.toPlainText()

    def get_error_content(self) -> str:
        """获取错误内容"""
        return self.error_widget.toPlainText()

    def get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def set_log_font(self, font_family: str, font_size: int):
        """设置日志字体"""
        font = QFont(font_family, font_size)
        self.log_widget.setFont(font)
        self.error_widget.setFont(font)

    def set_auto_scroll(self, enabled: bool):
        """设置自动滚动"""
        # 这个功能由append方法自动实现
        pass

    def set_max_lines(self, max_lines: int):
        """设置最大行数"""
        self.log_widget.document().setMaximumBlockCount(max_lines)
        self.error_widget.document().setMaximumBlockCount(max_lines)

    def copy_log_to_clipboard(self):
        """复制日志到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.get_log_content())

    def copy_error_to_clipboard(self):
        """复制错误到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.get_error_content())

    def search_in_log(self, search_text: str, case_sensitive: bool = False) -> bool:
        """
        在日志中搜索文本

        Args:
            search_text: 搜索文本
            case_sensitive: 是否区分大小写

        Returns:
            是否找到
        """
        return self.search_in_text_edit(self.log_widget, search_text, case_sensitive)

    def search_in_error(self, search_text: str, case_sensitive: bool = False) -> bool:
        """
        在错误中搜索文本

        Args:
            search_text: 搜索文本
            case_sensitive: 是否区分大小写

        Returns:
            是否找到
        """
        return self.search_in_text_edit(self.error_widget, search_text, case_sensitive)

    def search_in_text_edit(self, text_edit: QTextEdit, search_text: str,
                           case_sensitive: bool) -> bool:
        """在文本编辑控件中搜索文本"""
        if not search_text:
            return False

        cursor = text_edit.textCursor()
        text = text_edit.toPlainText()

        # 设置搜索选项
        if case_sensitive:
            index = text.find(search_text, cursor.position())
        else:
            index = text.lower().find(search_text.lower(), cursor.position())

        if index != -1:
            # 找到文本，选择它
            cursor.setPosition(index)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_text))
            text_edit.setTextCursor(cursor)
            text_edit.setFocus()
            return True
        else:
            # 从开头重新搜索
            if case_sensitive:
                index = text.find(search_text)
            else:
                index = text.lower().find(search_text.lower())

            if index != -1:
                cursor.setPosition(index)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_text))
                text_edit.setTextCursor(cursor)
                text_edit.setFocus()
                return True

        return False

    def highlight_errors(self):
        """高亮显示错误"""
        # 这里可以实现错误高亮逻辑
        pass

    def get_statistics(self) -> dict:
        """获取统计信息"""
        log_text = self.get_log_content()
        error_text = self.get_error_content()

        return {
            "log_lines": len(log_text.splitlines()),
            "log_chars": len(log_text),
            "error_lines": len(error_text.splitlines()),
            "error_chars": len(error_text),
            "has_errors": len(error_text.strip()) > 0
        }

    def save_log_to_file(self, file_path: str) -> bool:
        """
        保存日志到文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功保存
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get_log_content())
            return True
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            return False

    def save_error_to_file(self, file_path: str) -> bool:
        """
        保存错误到文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功保存
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get_error_content())
            return True
        except Exception as e:
            print(f"保存错误文件失败: {e}")
            return False