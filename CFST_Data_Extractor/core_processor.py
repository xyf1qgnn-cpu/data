"""
核心处理逻辑 - 适配现有工作流到GUI应用程序
基于现有main.py、models.py、processing.py、validation.py、styling.py模块
"""

import os
import json
import shutil
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pdfplumber
import pandas as pd
import numpy as np
from openai import OpenAI
import instructor
from pydantic import BaseModel, Field

# 导入现有模块
from models import SpecimenData, ExtractionResult
from processing import segment_pdf_text_intelligently, optimize_text_for_extraction
from validation import validate_dataframe, calculate_theoretical_capacity
from styling import apply_excel_styling, reorder_columns_for_export, export_to_excel_with_styling


class CoreProcessor:
    """核心处理器，包装现有工作流逻辑"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化核心处理器

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        self.results = []
        self.failed_files = []
        self.excluded_files = []

    def initialize_client(self) -> OpenAI:
        """初始化OpenAI客户端"""
        if not self.api_key:
            raise ValueError("API密钥未提供")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 配置instructor
        instructor.patch(self.client)
        return self.client

    def get_pdf_files(self, directory: str) -> List[str]:
        """
        获取目录中的所有PDF文件

        Args:
            directory: PDF文件目录

        Returns:
            PDF文件路径列表
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")

        pdf_files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(directory, filename)
                pdf_files.append(file_path)

        return sorted(pdf_files)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        从PDF提取文本

        Args:
            file_path: PDF文件路径

        Returns:
            提取的文本内容
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise Exception(f"PDF文本提取失败: {str(e)}")

    def extract_data_with_ai(self, client: OpenAI, text: str) -> Optional[Dict]:
        """
        使用AI提取结构化数据

        Args:
            client: OpenAI客户端
            text: PDF文本内容

        Returns:
            提取的数据字典，或None如果提取失败
        """
        try:
            # 智能文本分段和优化
            segmented_text = segment_pdf_text_intelligently(text)
            optimized_text = optimize_text_for_extraction(segmented_text)

            # 使用instructor进行结构化提取
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个CFST（钢管混凝土）实验数据提取专家。请从提供的文本中提取CFST试件的实验数据。"},
                    {"role": "user", "content": f"请从以下文本中提取CFST试件的实验数据：\n\n{optimized_text}"}
                ],
                response_model=ExtractionResult,
                temperature=0.1,
                max_tokens=8192
            )

            # 转换为字典格式
            result_dict = response.dict()

            # 添加提取元数据
            result_dict["extraction_timestamp"] = datetime.now().isoformat()
            result_dict["text_length"] = len(text)
            result_dict["optimized_text_length"] = len(optimized_text)

            return result_dict

        except Exception as e:
            print(f"AI数据提取失败: {str(e)}")
            return None

    def process_single_file(self, file_path: str, output_dir: str = ".") -> Dict:
        """
        处理单个PDF文件

        Args:
            file_path: PDF文件路径
            output_dir: 输出目录

        Returns:
            处理结果字典
        """
        filename = os.path.basename(file_path)
        result = {
            "filename": filename,
            "file_path": file_path,
            "success": False,
            "error": None,
            "data": None,
            "validation_results": None,
            "excel_path": None
        }

        try:
            # 1. 提取文本
            text = self.extract_text_from_pdf(file_path)
            if not text or len(text.strip()) < 100:
                result["error"] = "PDF文本提取失败或内容过少"
                return result

            # 2. AI提取数据
            if not self.client:
                self.initialize_client()

            json_data = self.extract_data_with_ai(self.client, text)
            if not json_data:
                result["error"] = "AI数据提取失败"
                return result

            # 3. 转换为DataFrame
            all_data = []
            for group_name in ["Group_A", "Group_B", "Group_C"]:
                if group_name in json_data and json_data[group_name]:
                    for item in json_data[group_name]:
                        item["group"] = group_name
                        item["source_file"] = filename
                        all_data.append(item)

            if not all_data:
                result["error"] = "未提取到有效数据"
                return result

            df = pd.DataFrame(all_data)

            # 4. 应用验证
            validation_df = validate_dataframe(df)

            # 5. 导出Excel
            excel_filename = f"CFST_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_path = os.path.join(output_dir, excel_filename)

            export_to_excel_with_styling(validation_df, excel_path)

            # 6. 更新结果
            result["success"] = True
            result["data"] = json_data
            result["validation_results"] = validation_df.to_dict("records")
            result["excel_path"] = excel_path
            result["data_count"] = len(all_data)

            # 添加到结果列表
            self.results.append(result)

        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            self.failed_files.append(result)

        return result

    def move_failed_file(self, file_path: str, not_input_dir: str) -> bool:
        """
        移动处理失败的文件到NotInput目录

        Args:
            file_path: 源文件路径
            not_input_dir: NotInput目录

        Returns:
            是否成功移动
        """
        try:
            if not os.path.exists(not_input_dir):
                os.makedirs(not_input_dir)

            filename = os.path.basename(file_path)
            dest_path = os.path.join(not_input_dir, filename)
            shutil.move(file_path, dest_path)
            return True
        except Exception as e:
            print(f"移动失败文件出错: {str(e)}")
            return False

    def move_excluded_file(self, file_path: str, excluded_dir: str) -> bool:
        """
        移动被排除的文件到Excluded目录

        Args:
            file_path: 源文件路径
            excluded_dir: Excluded目录

        Returns:
            是否成功移动
        """
        try:
            if not os.path.exists(excluded_dir):
                os.makedirs(excluded_dir)

            filename = os.path.basename(file_path)
            dest_path = os.path.join(excluded_dir, filename)
            shutil.move(file_path, dest_path)
            return True
        except Exception as e:
            print(f"移动排除文件出错: {str(e)}")
            return False

    def process_batch(self, pdf_directory: str, output_dir: str = ".",
                     not_input_dir: str = "NotInput", excluded_dir: str = "Excluded") -> Dict:
        """
        批量处理PDF文件

        Args:
            pdf_directory: PDF文件目录
            output_dir: 输出目录
            not_input_dir: NotInput目录
            excluded_dir: Excluded目录

        Returns:
            批量处理结果统计
        """
        # 重置结果
        self.results = []
        self.failed_files = []
        self.excluded_files = []

        # 获取PDF文件
        pdf_files = self.get_pdf_files(pdf_directory)
        total_files = len(pdf_files)

        stats = {
            "total_files": total_files,
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "excluded_files": 0,
            "total_data_points": 0,
            "start_time": datetime.now().isoformat(),
            "results": [],
            "summary": {}
        }

        for i, file_path in enumerate(pdf_files):
            try:
                # 处理单个文件
                result = self.process_single_file(file_path, output_dir)

                if result["success"]:
                    stats["successful_files"] += 1
                    stats["total_data_points"] += result.get("data_count", 0)
                else:
                    # 根据错误类型决定文件去向
                    error_msg = result.get("error", "").lower()
                    if "excluded" in error_msg or "无效" in error_msg or "无关" in error_msg:
                        # 移动到Excluded目录
                        if self.move_excluded_file(file_path, excluded_dir):
                            self.excluded_files.append(result)
                            stats["excluded_files"] += 1
                    else:
                        # 移动到NotInput目录
                        if self.move_failed_file(file_path, not_input_dir):
                            self.failed_files.append(result)
                            stats["failed_files"] += 1

                stats["processed_files"] += 1
                stats["results"].append(result)

            except Exception as e:
                # 处理过程中出现异常
                error_result = {
                    "filename": os.path.basename(file_path),
                    "file_path": file_path,
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                self.failed_files.append(error_result)
                stats["failed_files"] += 1
                stats["results"].append(error_result)

        # 计算统计摘要
        stats["end_time"] = datetime.now().isoformat()
        stats["summary"] = {
            "success_rate": stats["successful_files"] / total_files if total_files > 0 else 0,
            "failure_rate": stats["failed_files"] / total_files if total_files > 0 else 0,
            "exclusion_rate": stats["excluded_files"] / total_files if total_files > 0 else 0,
            "data_points_per_file": stats["total_data_points"] / stats["successful_files"] if stats["successful_files"] > 0 else 0
        }

        return stats

    def get_processing_summary(self) -> Dict:
        """获取处理摘要"""
        return {
            "total_results": len(self.results),
            "total_failed": len(self.failed_files),
            "total_excluded": len(self.excluded_files),
            "all_results": self.results,
            "failed_results": self.failed_files,
            "excluded_results": self.excluded_files
        }


# 兼容性函数，用于直接调用
def process_pdf_file(file_path: str, api_key: str, output_dir: str = ".") -> Dict:
    """处理单个PDF文件（兼容现有调用）"""
    processor = CoreProcessor(api_key)
    return processor.process_single_file(file_path, output_dir)


def process_pdf_directory(pdf_directory: str, api_key: str, output_dir: str = ".",
                         not_input_dir: str = "NotInput", excluded_dir: str = "Excluded") -> Dict:
    """处理PDF目录（兼容现有调用）"""
    processor = CoreProcessor(api_key)
    return processor.process_batch(pdf_directory, output_dir, not_input_dir, excluded_dir)