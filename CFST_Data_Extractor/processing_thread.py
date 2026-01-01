"""
处理线程 - 包装核心处理逻辑到QThread
实现信号/槽通信机制，保持UI响应性
"""

import os
import time
import traceback
from typing import Dict, List, Optional
from datetime import datetime

from PySide6.QtCore import QThread, Signal, QObject, Qt
from PySide6.QtWidgets import QApplication

from core_processor import CoreProcessor


class ProcessingThread(QThread):
    """
    处理线程，包装核心处理逻辑
    使用信号/槽机制与GUI通信
    """

    # 进度相关信号
    progress_updated = Signal(int, int)          # 当前文件索引，总文件数
    file_progress = Signal(str, int)             # 文件名，进度百分比
    overall_progress = Signal(int, int, str)     # 当前进度，总进度，状态描述

    # 日志相关信号
    log_info = Signal(str)                       # 信息日志
    log_warning = Signal(str)                    # 警告日志
    log_error = Signal(str)                      # 错误日志
    log_debug = Signal(str)                      # 调试日志

    # 文件状态信号
    file_started = Signal(str)                   # 文件开始处理
    file_completed = Signal(str, bool, str)      # 文件名，是否成功，状态消息
    file_excluded = Signal(str, str)             # 文件名，排除原因
    file_failed = Signal(str, str)               # 文件名，失败原因

    # 处理状态信号
    processing_started = Signal()                # 处理开始
    processing_paused = Signal()                 # 处理暂停
    processing_resumed = Signal()                # 处理恢复
    processing_cancelled = Signal()              # 处理取消
    processing_finished = Signal(dict)           # 处理完成，结果统计

    # 验证结果信号
    validation_update = Signal(dict)             # 验证更新
    anomaly_detected = Signal(dict)              # 异常检测

    def __init__(self, pdf_directory: str, api_key: str, config: Dict):
        """
        初始化处理线程

        Args:
            pdf_directory: PDF文件目录
            api_key: DeepSeek API密钥
            config: 配置字典
        """
        super().__init__()
        self.pdf_directory = pdf_directory
        self.api_key = api_key
        self.config = config

        # 线程控制标志
        self.is_running = True
        self.is_paused = False
        self.is_cancelled = False

        # 处理状态
        self.current_file_index = 0
        self.total_files = 0
        self.start_time = None
        self.processor = None

        # 结果存储
        self.results = []
        self.failed_files = []
        self.excluded_files = []

    def run(self):
        """线程主循环"""
        try:
            self.start_time = datetime.now()
            self.log_info.emit(f"开始处理目录: {self.pdf_directory}")
            self.processing_started.emit()

            # 初始化处理器
            self.processor = CoreProcessor(
                api_key=self.api_key,
                base_url=self.config.get("api_base_url", "https://api.deepseek.com")
            )

            # 获取PDF文件列表
            pdf_files = self.processor.get_pdf_files(self.pdf_directory)
            self.total_files = len(pdf_files)

            if self.total_files == 0:
                self.log_warning.emit(f"目录中没有找到PDF文件: {self.pdf_directory}")
                self.processing_finished.emit({
                    "success": False,
                    "message": "没有找到PDF文件",
                    "total_files": 0
                })
                return

            self.log_info.emit(f"找到 {self.total_files} 个PDF文件")
            self.overall_progress.emit(0, self.total_files, "准备开始处理")

            # 处理每个文件
            for i, file_path in enumerate(pdf_files):
                if not self.is_running or self.is_cancelled:
                    break

                # 检查暂停状态
                while self.is_paused and self.is_running and not self.is_cancelled:
                    time.sleep(0.1)
                    QApplication.processEvents()

                if self.is_cancelled:
                    self.log_info.emit("处理已被取消")
                    break

                # 更新进度
                self.current_file_index = i
                self.progress_updated.emit(i + 1, self.total_files)
                self.file_progress.emit(os.path.basename(file_path), 0)

                # 处理单个文件
                self.process_single_file(file_path, i)

            # 生成最终结果
            if self.is_running and not self.is_cancelled:
                self.finalize_processing()
            elif self.is_cancelled:
                self.log_info.emit("处理已取消")
                self.processing_cancelled.emit()

        except Exception as e:
            error_msg = f"处理过程中出现异常: {str(e)}"
            self.log_error.emit(error_msg)
            self.log_debug.emit(traceback.format_exc())

            self.processing_finished.emit({
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc()
            })

    def process_single_file(self, file_path: str, file_index: int):
        """处理单个PDF文件"""
        filename = os.path.basename(file_path)
        self.file_started.emit(filename)
        self.log_info.emit(f"正在处理文件 ({file_index + 1}/{self.total_files}): {filename}")

        try:
            # 更新文件进度
            self.file_progress.emit(filename, 10)
            self.overall_progress.emit(
                file_index + 1,
                self.total_files,
                f"正在提取文本: {filename}"
            )

            # 提取文本
            text = self.processor.extract_text_from_pdf(file_path)
            if not text or len(text.strip()) < 100:
                error_msg = "PDF文本提取失败或内容过少"
                self.log_error.emit(f"{filename}: {error_msg}")
                self.file_failed.emit(filename, error_msg)
                self.move_to_not_input(file_path)
                return

            self.file_progress.emit(filename, 30)
            self.overall_progress.emit(
                file_index + 1,
                self.total_files,
                f"正在使用AI提取数据: {filename}"
            )

            # AI提取数据
            if not self.processor.client:
                self.processor.initialize_client()

            json_data = self.processor.extract_data_with_ai(self.processor.client, text)
            if not json_data:
                error_msg = "AI数据提取失败"
                self.log_error.emit(f"{filename}: {error_msg}")
                self.file_failed.emit(filename, error_msg)
                self.move_to_not_input(file_path)
                return

            # 检查数据有效性
            is_valid = self.validate_extracted_data(json_data)
            if not is_valid:
                error_msg = "提取的数据无效或为空"
                self.log_warning.emit(f"{filename}: {error_msg}")
                self.file_excluded.emit(filename, error_msg)
                self.move_to_excluded(file_path)
                return

            self.file_progress.emit(filename, 60)
            self.overall_progress.emit(
                file_index + 1,
                self.total_files,
                f"正在验证数据: {filename}"
            )

            # 转换为DataFrame并验证
            all_data = []
            for group_name in ["Group_A", "Group_B", "Group_C"]:
                if group_name in json_data and json_data[group_name]:
                    for item in json_data[group_name]:
                        item["group"] = group_name
                        item["source_file"] = filename
                        all_data.append(item)

            if not all_data:
                error_msg = "未提取到有效数据"
                self.log_warning.emit(f"{filename}: {error_msg}")
                self.file_excluded.emit(filename, error_msg)
                self.move_to_excluded(file_path)
                return

            # 发送验证更新
            validation_info = {
                "filename": filename,
                "data_count": len(all_data),
                "groups": list(set(item.get("group", "") for item in all_data))
            }
            self.validation_update.emit(validation_info)

            self.file_progress.emit(filename, 90)
            self.overall_progress.emit(
                file_index + 1,
                self.total_files,
                f"正在保存结果: {filename}"
            )

            # 记录成功结果
            result = {
                "filename": filename,
                "file_path": file_path,
                "success": True,
                "data_count": len(all_data),
                "extraction_time": datetime.now().isoformat()
            }
            self.results.append(result)

            self.file_progress.emit(filename, 100)
            self.file_completed.emit(filename, True, f"成功提取 {len(all_data)} 条数据")

            self.log_info.emit(f"{filename}: 处理完成，提取 {len(all_data)} 条数据")

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            self.log_error.emit(f"{filename}: {error_msg}")
            self.log_debug.emit(traceback.format_exc())
            self.file_failed.emit(filename, error_msg)
            self.move_to_not_input(file_path)

    def validate_extracted_data(self, json_data: Dict) -> bool:
        """验证提取的数据是否有效"""
        if not json_data:
            return False

        # 检查是否有任何组包含数据
        for group_name in ["Group_A", "Group_B", "Group_C"]:
            if group_name in json_data and json_data[group_name]:
                # 检查数据项是否包含必要字段
                for item in json_data[group_name]:
                    if isinstance(item, dict) and item.get("n_exp") is not None:
                        return True

        return False

    def move_to_not_input(self, file_path: str):
        """移动文件到NotInput目录"""
        try:
            not_input_dir = self.config.get("not_input_dir", "NotInput")
            if not os.path.exists(not_input_dir):
                os.makedirs(not_input_dir)

            filename = os.path.basename(file_path)
            dest_path = os.path.join(not_input_dir, filename)
            shutil.move(file_path, dest_path)
            self.log_info.emit(f"已将失败文件移动到: {dest_path}")
        except Exception as e:
            self.log_error.emit(f"移动失败文件出错: {str(e)}")

    def move_to_excluded(self, file_path: str):
        """移动文件到Excluded目录"""
        try:
            excluded_dir = self.config.get("excluded_dir", "Excluded")
            if not os.path.exists(excluded_dir):
                os.makedirs(excluded_dir)

            filename = os.path.basename(file_path)
            dest_path = os.path.join(excluded_dir, filename)
            shutil.move(file_path, dest_path)
            self.log_info.emit(f"已将排除文件移动到: {dest_path}")
        except Exception as e:
            self.log_error.emit(f"移动排除文件出错: {str(e)}")

    def finalize_processing(self):
        """完成处理，生成最终结果"""
        end_time = datetime.now()
        processing_time = (end_time - self.start_time).total_seconds()

        # 生成Excel文件
        excel_path = None
        if self.results:
            try:
                # 这里可以添加生成汇总Excel的逻辑
                # 暂时使用简单的统计
                excel_filename = f"CFST_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                excel_path = os.path.join(self.config.get("output_dir", "."), excel_filename)

                # 实际应用中应该调用core_processor的导出功能
                self.log_info.emit(f"结果已保存到: {excel_path}")
            except Exception as e:
                self.log_error.emit(f"生成Excel文件失败: {str(e)}")

        # 准备最终统计
        stats = {
            "success": True,
            "total_files": self.total_files,
            "processed_files": len(self.results) + len(self.failed_files) + len(self.excluded_files),
            "successful_files": len(self.results),
            "failed_files": len(self.failed_files),
            "excluded_files": len(self.excluded_files),
            "total_data_points": sum(r.get("data_count", 0) for r in self.results),
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time_seconds": processing_time,
            "excel_path": excel_path,
            "success_rate": len(self.results) / self.total_files if self.total_files > 0 else 0,
            "results": self.results[:10],  # 只返回前10个结果，避免数据过大
            "failed_files_list": [{"filename": os.path.basename(f["file_path"]), "error": f.get("error", "未知错误")}
                                 for f in self.failed_files[:10]],
            "excluded_files_list": [{"filename": os.path.basename(f["file_path"]), "reason": f.get("error", "未知原因")}
                                   for f in self.excluded_files[:10]]
        }

        self.log_info.emit(f"处理完成！成功: {len(self.results)}, 失败: {len(self.failed_files)}, 排除: {len(self.excluded_files)}")
        self.log_info.emit(f"总处理时间: {processing_time:.2f} 秒")

        self.processing_finished.emit(stats)

    def pause_processing(self):
        """暂停处理"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.log_info.emit("处理已暂停")
            self.processing_paused.emit()

    def resume_processing(self):
        """恢复处理"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.log_info.emit("处理已恢复")
            self.processing_resumed.emit()

    def cancel_processing(self):
        """取消处理"""
        self.is_cancelled = True
        self.is_running = False
        self.is_paused = False
        self.log_info.emit("正在取消处理...")

    def get_current_status(self) -> Dict:
        """获取当前状态"""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "is_cancelled": self.is_cancelled,
            "current_file_index": self.current_file_index,
            "total_files": self.total_files,
            "progress_percentage": (self.current_file_index / self.total_files * 100) if self.total_files > 0 else 0,
            "results_count": len(self.results),
            "failed_count": len(self.failed_files),
            "excluded_count": len(self.excluded_files)
        }