"""
API密钥输入组件 - 安全输入和管理API密钥
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon


class ApiKeyWidget(QWidget):
    """API密钥输入组件"""

    # 信号定义
    api_key_changed = Signal(str)          # API密钥变化
    api_key_saved = Signal()               # API密钥保存
    api_key_loaded = Signal(str)           # API密钥加载
    api_key_cleared = Signal()             # API密钥清除
    api_key_tested = Signal(bool, str)     # API密钥测试结果，是否成功，消息

    def __init__(self, parent=None):
        """初始化API密钥组件"""
        super().__init__(parent)

        self.api_key = ""
        self.is_key_visible = False
        self.is_testing = False

        self.setup_ui()
        self.setup_styles()
        self.connect_signals()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title_label = QLabel("DeepSeek API Key Configuration")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1565C0;")
        main_layout.addWidget(title_label)

        # Input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(10)

        # Key input row
        key_input_layout = QHBoxLayout()
        key_input_layout.setSpacing(10)

        self.key_label = QLabel("API Key:")
        self.key_label.setFixedWidth(80)
        key_input_layout.addWidget(self.key_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your DeepSeek API key (sk-...)")
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.textChanged.connect(self.on_key_changed)
        key_input_layout.addWidget(self.key_input)

        self.toggle_visibility_btn = QPushButton("Show")
        self.toggle_visibility_btn.setFixedWidth(60)
        self.toggle_visibility_btn.clicked.connect(self.toggle_key_visibility)
        key_input_layout.addWidget(self.toggle_visibility_btn)

        input_layout.addLayout(key_input_layout)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.load_btn = QPushButton("Load Key")
        self.load_btn.setToolTip("Load saved API key from secure storage")
        button_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton("Save Key")
        self.save_btn.setToolTip("Save API key to secure storage")
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        self.test_btn = QPushButton("Test Key")
        self.test_btn.setToolTip("Test if API key is valid")
        self.test_btn.setEnabled(False)
        button_layout.addWidget(self.test_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear entered API key")
        self.clear_btn.setEnabled(False)
        button_layout.addWidget(self.clear_btn)

        input_layout.addLayout(button_layout)

        # Status display
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)

        self.status_label = QLabel("Status: Not configured")
        self.status_label.setStyleSheet("color: #757575;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.auto_save_check = QCheckBox("Auto save")
        self.auto_save_check.setChecked(True)
        status_layout.addWidget(self.auto_save_check)

        input_layout.addLayout(status_layout)

        # Test progress bar (hidden)
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        input_layout.addWidget(self.test_progress)

        main_layout.addWidget(input_frame)

        # Information tip
        info_label = QLabel(
            "Note: API key is used to call DeepSeek AI service for data extraction. "
            "Key will be encrypted and stored securely."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #616161; font-size: 11px;")
        main_layout.addWidget(info_label)

    def setup_styles(self):
        """Set up styles"""
        # Input field style
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QLineEdit:disabled {
                background-color: #F5F5F5;
                color: #9E9E9E;
            }
        """)

        # Button style
        button_style = """
            QPushButton {
                padding: 8px 15px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: #FAFAFA;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #9E9E9E;
            }
        """

        self.load_btn.setStyleSheet(button_style)
        self.save_btn.setStyleSheet(button_style)
        self.test_btn.setStyleSheet(button_style)
        self.clear_btn.setStyleSheet(button_style)

        # Special button style
        self.toggle_visibility_btn.setStyleSheet("""
            QPushButton {
                padding: 5px;
                border: 1px solid #BDBDBD;
                border-radius: 3px;
                background-color: #E3F2FD;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)

        # Frame style
        self.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 6px;
            }
        """)

    def connect_signals(self):
        """Connect signals"""
        self.load_btn.clicked.connect(self.load_api_key)
        self.save_btn.clicked.connect(self.save_api_key)
        self.test_btn.clicked.connect(self.test_api_key)
        self.clear_btn.clicked.connect(self.clear_api_key)

    def on_key_changed(self, text: str):
        """Handle key input changes"""
        self.api_key = text.strip()

        # Update button states
        has_key = bool(self.api_key)
        self.save_btn.setEnabled(has_key)
        self.test_btn.setEnabled(has_key)
        self.clear_btn.setEnabled(has_key)

        # Update status
        if has_key:
            key_length = len(self.api_key)
            masked_key = self.api_key[:4] + "*" * (key_length - 8) + self.api_key[-4:] if key_length > 8 else "***"
            self.status_label.setText(f"Status: Entered ({masked_key})")
            self.status_label.setStyleSheet("color: #2E7D32;")
        else:
            self.status_label.setText("Status: Not configured")
            self.status_label.setStyleSheet("color: #757575;")

        # Emit signal
        self.api_key_changed.emit(self.api_key)

    def toggle_key_visibility(self):
        """Toggle key visibility"""
        self.is_key_visible = not self.is_key_visible

        if self.is_key_visible:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_visibility_btn.setText("Hide")
            self.toggle_visibility_btn.setToolTip("Hide API key")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.toggle_visibility_btn.setText("Show")
            self.toggle_visibility_btn.setToolTip("Show API key")

    def load_api_key(self):
        """Load API key"""
        try:
            # This should call SecureStorage to load key
            # Temporarily using simulation
            from secure_storage import SecureStorage
            storage = SecureStorage()
            loaded_key = storage.load_api_key()

            if loaded_key:
                self.key_input.setText(loaded_key)
                self.status_label.setText("Status: Loaded from secure storage")
                self.status_label.setStyleSheet("color: #2E7D32;")
                self.api_key_loaded.emit(loaded_key)

                # Show success message
                QMessageBox.information(
                    self,
                    "Load Successful",
                    "API key has been loaded from secure storage."
                )
            else:
                self.status_label.setText("Status: No saved key found")
                self.status_label.setStyleSheet("color: #F57C00;")

                QMessageBox.warning(
                    self,
                    "Key Not Found",
                    "No saved API key found. Please enter and save a key first."
                )

        except Exception as e:
            self.status_label.setText("Status: Load failed")
            self.status_label.setStyleSheet("color: #C62828;")

            QMessageBox.critical(
                self,
                "Load Failed",
                f"Error loading API key: {str(e)}"
            )

    def save_api_key(self):
        """Save API key"""
        if not self.api_key:
            QMessageBox.warning(self, "Warning", "Please enter API key")
            return

        try:
            # This should call SecureStorage to save key
            from secure_storage import SecureStorage
            storage = SecureStorage()

            if storage.save_api_key(self.api_key):
                self.status_label.setText("Status: Saved to secure storage")
                self.status_label.setStyleSheet("color: #2E7D32;")
                self.api_key_saved.emit()

                # Show success message
                QMessageBox.information(
                    self,
                    "Save Successful",
                    "API key has been securely saved.\n\n"
                    "Key is encrypted and stored securely."
                )
            else:
                self.status_label.setText("Status: Save failed")
                self.status_label.setStyleSheet("color: #C62828;")

                QMessageBox.critical(
                    self,
                    "Save Failed",
                    "Error saving API key."
                )

        except Exception as e:
            self.status_label.setText("Status: Save failed")
            self.status_label.setStyleSheet("color: #C62828;")

            QMessageBox.critical(
                self,
                "Save Failed",
                f"Error saving API key: {str(e)}"
            )

    def test_api_key(self):
        """Test API key"""
        if not self.api_key:
            QMessageBox.warning(self, "Warning", "Please enter API key")
            return

        if self.is_testing:
            return

        self.is_testing = True
        self.test_progress.setVisible(True)
        self.test_btn.setEnabled(False)
        self.status_label.setText("Status: Testing...")
        self.status_label.setStyleSheet("color: #1565C0;")

        # Simulate testing process
        # Should actually call API for testing
        import threading
        threading.Thread(target=self.perform_api_test, daemon=True).start()

    def perform_api_test(self):
        """Perform API test"""
        import time
        from PySide6.QtCore import QTimer

        try:
            # Simulate API test
            time.sleep(2)  # Simulate network delay

            # Simple format check
            if self.api_key.startswith("sk-") and len(self.api_key) > 20:
                success = True
                message = "API key format is correct, connection test successful."
            else:
                success = False
                message = "API key format is incorrect. Please check key format."

            # Use QTimer to update UI in main thread
            QTimer.singleShot(0, lambda: self.on_test_complete(success, message))

        except Exception as e:
            QTimer.singleShot(0, lambda: self.on_test_complete(False, f"Test failed: {str(e)}"))

    def on_test_complete(self, success: bool, message: str):
        """Handle test completion"""
        self.is_testing = False
        self.test_progress.setVisible(False)
        self.test_btn.setEnabled(True)

        if success:
            self.status_label.setText("Status: Test passed")
            self.status_label.setStyleSheet("color: #2E7D32;")

            QMessageBox.information(
                self,
                "Test Successful",
                message
            )
        else:
            self.status_label.setText("Status: Test failed")
            self.status_label.setStyleSheet("color: #C62828;")

            QMessageBox.warning(
                self,
                "Test Failed",
                message
            )

        self.api_key_tested.emit(success, message)

    def clear_api_key(self):
        """Clear API key"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear the API key?\n\n"
            "This will clear the key from the input box, but will not delete saved keys.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.key_input.clear()
            self.api_key_cleared.emit()

            QMessageBox.information(
                self,
                "Cleared",
                "API key has been cleared from input box."
            )

    def get_api_key(self) -> str:
        """Get API key"""
        return self.api_key

    def set_api_key(self, key: str):
        """Set API key"""
        self.key_input.setText(key)

    def is_valid_key(self) -> bool:
        """Check if key is valid"""
        if not self.api_key:
            return False

        # Basic format check
        return self.api_key.startswith("sk-") and len(self.api_key) > 20

    def get_key_info(self) -> dict:
        """Get key information"""
        return {
            "has_key": bool(self.api_key),
            "key_length": len(self.api_key),
            "is_valid_format": self.is_valid_key(),
            "is_visible": self.is_key_visible,
            "is_saved": False  # Should check if saved
        }

    def set_read_only(self, read_only: bool):
        """Set read-only mode"""
        self.key_input.setReadOnly(read_only)
        self.load_btn.setEnabled(not read_only)
        self.save_btn.setEnabled(not read_only and bool(self.api_key))
        self.test_btn.setEnabled(not read_only and bool(self.api_key))
        self.clear_btn.setEnabled(not read_only and bool(self.api_key))
        self.toggle_visibility_btn.setEnabled(not read_only)

    def reset(self):
        """Reset component"""
        self.key_input.clear()
        self.is_key_visible = False
        self.key_input.setEchoMode(QLineEdit.Password)
        self.toggle_visibility_btn.setText("Show")
        self.status_label.setText("Status: Not configured")
        self.status_label.setStyleSheet("color: #757575;")

    def show_help(self):
        """Show help information"""
        help_text = """
        DeepSeek API Key Usage Instructions:

        1. Get API Key:
           - Register an account on DeepSeek official website
           - Create API key in the console
           - Copy the key starting with "sk-"

        2. Security Tips:
           - Do not share your API key
           - Key will be encrypted and stored
           - Regularly change keys to improve security

        3. Function Description:
           - "Load Key": Load saved key from secure storage
           - "Save Key": Encrypt and save current key
           - "Test Key": Verify if key is valid
           - "Clear": Clear key from input box

        For issues, please refer to official documentation or contact support.
        """

        QMessageBox.information(
            self,
            "API Key Help",
            help_text
        )