"""
进度显示组件 - 显示处理进度和状态信息
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta


class ProgressWidget(QWidget):
    """进度显示组件"""

    def __init__(self, parent=None):
        """初始化进度组件"""
        super().__init__(parent)

        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.current_file = ""
        self.is_processing = False

        self.setup_ui()
        self.setup_styles()
        self.setup_timer()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Overall progress group
        overall_group = QGroupBox("Overall Progress")
        overall_layout = QVBoxLayout(overall_group)
        overall_layout.setContentsMargins(15, 15, 15, 15)
        overall_layout.setSpacing(10)

        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFormat("Ready")
        overall_layout.addWidget(self.overall_progress)

        # Overall statistics
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        self.total_label = QLabel("Total: 0")
        self.total_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.total_label)

        self.processed_label = QLabel("Processed: 0")
        self.processed_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.processed_label)

        self.remaining_label = QLabel("Remaining: 0")
        self.remaining_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.remaining_label)

        self.success_rate_label = QLabel("Success Rate: 0%")
        self.success_rate_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.success_rate_label)

        overall_layout.addLayout(stats_layout)

        main_layout.addWidget(overall_group)

        # Current file progress group
        current_group = QGroupBox("Current File")
        current_layout = QVBoxLayout(current_group)
        current_layout.setContentsMargins(15, 15, 15, 15)
        current_layout.setSpacing(10)

        # Current file information
        file_info_layout = QHBoxLayout()
        file_info_layout.setSpacing(10)

        self.file_name_label = QLabel("File: None")
        self.file_name_label.setWordWrap(True)
        file_info_layout.addWidget(self.file_name_label, 3)

        self.file_status_label = QLabel("Status: Waiting")
        self.file_status_label.setAlignment(Qt.AlignRight)
        file_info_layout.addWidget(self.file_status_label, 1)

        current_layout.addLayout(file_info_layout)

        # Current file progress bar
        self.file_progress = QProgressBar()
        self.file_progress.setRange(0, 100)
        self.file_progress.setTextVisible(True)
        self.file_progress.setFormat("Waiting to start")
        current_layout.addWidget(self.file_progress)

        main_layout.addWidget(current_group)

        # Time information group
        time_group = QGroupBox("Time Information")
        time_layout = QVBoxLayout(time_group)
        time_layout.setContentsMargins(15, 15, 15, 15)
        time_layout.setSpacing(10)

        # Time information
        time_info_layout = QHBoxLayout()
        time_info_layout.setSpacing(20)

        self.start_time_label = QLabel("Start Time: --:--:--")
        time_info_layout.addWidget(self.start_time_label)

        self.elapsed_time_label = QLabel("Elapsed: 00:00:00")
        time_info_layout.addWidget(self.elapsed_time_label)

        self.estimated_time_label = QLabel("Estimated Remaining: --:--:--")
        time_info_layout.addWidget(self.estimated_time_label)

        time_layout.addLayout(time_info_layout)

        main_layout.addWidget(time_group)

    def setup_styles(self):
        """Set up styles"""
        # Group box style
        group_style = """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #424242;
            }
        """

        # Directly set styles, not using findChild
        for child in self.findChildren(QGroupBox):
            child.setStyleSheet(group_style)

        # Progress bar style
        progress_style = """
            QProgressBar {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """

        self.overall_progress.setStyleSheet(progress_style)
        self.file_progress.setStyleSheet(progress_style)

        # Label style
        label_style = """
            QLabel {
                font-size: 12px;
                color: #424242;
            }
        """

        for label in self.findChildren(QLabel):
            label.setStyleSheet(label_style)

        # Special label styles
        self.total_label.setStyleSheet("font-weight: bold; color: #1565C0;")
        self.processed_label.setStyleSheet("font-weight: bold; color: #2E7D32;")
        self.remaining_label.setStyleSheet("font-weight: bold; color: #F57C00;")
        self.success_rate_label.setStyleSheet("font-weight: bold; color: #7B1FA2;")

    def setup_timer(self):
        """Set up timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(1000)  # Update every second

    def start_processing(self, total_files: int):
        """Start processing"""
        self.start_time = datetime.now()
        self.total_files = total_files
        self.processed_files = 0
        self.is_processing = True

        # Reset display
        self.overall_progress.setValue(0)
        self.overall_progress.setFormat(f"0/{total_files} (0%)")
        self.file_progress.setValue(0)
        self.file_progress.setFormat("Waiting to start")

        # Update labels
        self.total_label.setText(f"Total: {total_files}")
        self.processed_label.setText("Processed: 0")
        self.remaining_label.setText(f"Remaining: {total_files}")
        self.success_rate_label.setText("Success Rate: 0%")

        self.start_time_label.setText(f"Start Time: {self.start_time.strftime('%H:%M:%S')}")
        self.elapsed_time_label.setText("Elapsed: 00:00:00")
        self.estimated_time_label.setText("Estimated Remaining: Calculating...")

        self.file_name_label.setText("File: Preparing to start")
        self.file_status_label.setText("Status: Initializing")

    def update_overall_progress(self, current: int, total: int):
        """Update overall progress"""
        self.processed_files = current
        percentage = int((current / total) * 100) if total > 0 else 0

        self.overall_progress.setValue(percentage)
        self.overall_progress.setFormat(f"{current}/{total} ({percentage}%)")

        # Update statistics labels
        self.processed_label.setText(f"Processed: {current}")
        self.remaining_label.setText(f"Remaining: {total - current}")

        # Calculate success rate (needs external success count)
        # Temporarily showing progress percentage
        self.success_rate_label.setText(f"Progress: {percentage}%")

    def update_file_progress(self, filename: str, progress: int, status: str = ""):
        """Update file progress"""
        self.current_file = filename

        # Update filename display
        if len(filename) > 30:
            display_name = filename[:27] + "..."
        else:
            display_name = filename

        self.file_name_label.setText(f"File: {display_name}")

        # Update progress bar
        self.file_progress.setValue(progress)
        if status:
            self.file_progress.setFormat(f"{status} ({progress}%)")
        else:
            self.file_progress.setFormat(f"{progress}%")

        # Update status label
        if progress < 30:
            file_status = "Extracting text"
        elif progress < 60:
            file_status = "AI processing"
        elif progress < 90:
            file_status = "Data validation"
        else:
            file_status = "Saving results"

        self.file_status_label.setText(f"Status: {file_status}")

    def update_file_status(self, filename: str, success: bool, message: str = ""):
        """Update file status"""
        if success:
            status_text = "✓ Success"
            color = "#2E7D32"
        else:
            status_text = "✗ Failed"
            color = "#C62828"

        if message:
            status_text += f" ({message})"

        self.file_status_label.setText(f"Status: {status_text}")
        self.file_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Reset file progress bar after file completion
        if success:
            self.file_progress.setValue(100)
            self.file_progress.setFormat("Complete")
        else:
            self.file_progress.setValue(0)
            self.file_progress.setFormat("Failed")

    def update_time_display(self):
        """Update time display"""
        if not self.is_processing or not self.start_time:
            return

        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds

        self.elapsed_time_label.setText(f"Elapsed: {elapsed_str}")

        # Calculate estimated remaining time
        if self.processed_files > 0 and self.total_files > 0:
            time_per_file = elapsed.total_seconds() / self.processed_files
            remaining_files = self.total_files - self.processed_files
            remaining_seconds = time_per_file * remaining_files

            if remaining_seconds > 0:
                remaining_time = timedelta(seconds=int(remaining_seconds))
                remaining_str = str(remaining_time)
                self.estimated_time_label.setText(f"Estimated Remaining: {remaining_str}")
            else:
                self.estimated_time_label.setText("Estimated Remaining: About to complete")

    def finish_processing(self, success_count: int, failed_count: int):
        """Finish processing"""
        self.is_processing = False

        # Update overall progress
        self.overall_progress.setValue(100)
        self.overall_progress.setFormat("Processing complete")

        # Calculate success rate
        total_processed = success_count + failed_count
        if total_processed > 0:
            success_rate = int((success_count / total_processed) * 100)
            self.success_rate_label.setText(f"Success Rate: {success_rate}%")
        else:
            self.success_rate_label.setText("Success Rate: N/A")

        # Update file status
        self.file_name_label.setText("File: Processing complete")
        self.file_status_label.setText("Status: Complete")
        self.file_status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")

        # Stop time updates
        self.timer.stop()

    def pause_processing(self):
        """Pause processing"""
        self.is_processing = False
        self.file_status_label.setText("Status: Paused")
        self.file_status_label.setStyleSheet("color: #F57C00; font-weight: bold;")

    def resume_processing(self):
        """Resume processing"""
        self.is_processing = True
        self.file_status_label.setText("Status: Resuming...")
        self.file_status_label.setStyleSheet("color: #1565C0; font-weight: bold;")

    def cancel_processing(self):
        """Cancel processing"""
        self.is_processing = False
        self.overall_progress.setFormat("Cancelled")
        self.file_progress.setFormat("Cancelled")
        self.file_status_label.setText("Status: Cancelled")
        self.file_status_label.setStyleSheet("color: #757575; font-weight: bold;")

        # Stop time updates
        self.timer.stop()

    def reset(self):
        """Reset progress display"""
        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.current_file = ""
        self.is_processing = False

        self.overall_progress.setValue(0)
        self.overall_progress.setFormat("Ready")
        self.file_progress.setValue(0)
        self.file_progress.setFormat("Waiting to start")

        self.total_label.setText("Total: 0")
        self.processed_label.setText("Processed: 0")
        self.remaining_label.setText("Remaining: 0")
        self.success_rate_label.setText("Success Rate: 0%")

        self.start_time_label.setText("Start Time: --:--:--")
        self.elapsed_time_label.setText("Elapsed: 00:00:00")
        self.estimated_time_label.setText("Estimated Remaining: --:--:--")

        self.file_name_label.setText("File: None")
        self.file_status_label.setText("Status: Waiting")

        # Restart timer
        if not self.timer.isActive():
            self.timer.start(1000)

    def get_progress_info(self) -> dict:
        """Get progress information"""
        return {
            "is_processing": self.is_processing,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "current_file": self.current_file,
            "overall_progress": self.overall_progress.value(),
            "file_progress": self.file_progress.value(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }

    def set_theme(self, theme: str):
        """Set theme"""
        if theme == "dark":
            # Dark theme
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    color: #E0E0E0;
                    background-color: #2D2D2D;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    color: #BDBDBD;
                }
            """

            progress_style = """
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 4px;
                    text-align: center;
                    height: 25px;
                    color: #E0E0E0;
                    background-color: #424242;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                    border-radius: 3px;
                }
            """

            label_style = """
                QLabel {
                    font-size: 12px;
                    color: #E0E0E0;
                }
            """

        else:
            # Light theme (default)
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #E0E0E0;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    color: #424242;
                }
            """

            progress_style = """
                QProgressBar {
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                    border-radius: 3px;
                }
            """

            label_style = """
                QLabel {
                    font-size: 12px;
                    color: #424242;
                }
            """

        # Apply styles
        for group_box in self.findChildren(QGroupBox):
            group_box.setStyleSheet(group_style)

        self.overall_progress.setStyleSheet(progress_style)
        self.file_progress.setStyleSheet(progress_style)

        # Apply label styles (excluding special labels)
        special_labels = {self.total_label, self.processed_label,
                         self.remaining_label, self.success_rate_label}
        for label in self.findChildren(QLabel):
            if label not in special_labels:
                label.setStyleSheet(label_style)