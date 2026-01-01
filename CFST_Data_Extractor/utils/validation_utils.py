"""
验证工具函数
"""

import re
import os
from typing import Tuple, Optional, Dict, Any
import logging


class ValidationUtils:
    """验证工具类"""

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """
        验证API密钥格式

        Args:
            api_key: API密钥

        Returns:
            (是否有效, 错误消息)
        """
        if not api_key:
            return False, "API密钥不能为空"

        # 检查长度
        if len(api_key) < 20:
            return False, "API密钥过短"

        # DeepSeek API密钥通常以 "sk-" 开头
        if not api_key.startswith("sk-"):
            return False, "API密钥格式不正确（应以'sk-'开头）"

        # 检查是否包含非法字符
        if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key[3:]):
            return False, "API密钥包含非法字符"

        return True, "API密钥格式正确"

    @staticmethod
    def validate_directory(directory: str) -> Tuple[bool, str]:
        """
        验证目录

        Args:
            directory: 目录路径

        Returns:
            (是否有效, 错误消息)
        """
        if not directory:
            return False, "目录路径不能为空"

        # 检查路径是否存在
        if not os.path.exists(directory):
            return False, "目录不存在"

        # 检查是否为目录
        if not os.path.isdir(directory):
            return False, "路径不是目录"

        # 检查目录是否可读
        if not os.access(directory, os.R_OK):
            return False, "目录不可读"

        # 检查目录是否可写（如果需要）
        if not os.access(directory, os.W_OK):
            return False, "目录不可写"

        return True, "目录有效"

    @staticmethod
    def validate_file_path(file_path: str, check_exists: bool = True) -> Tuple[bool, str]:
        """
        验证文件路径

        Args:
            file_path: 文件路径
            check_exists: 是否检查文件存在

        Returns:
            (是否有效, 错误消息)
        """
        if not file_path:
            return False, "文件路径不能为空"

        # 检查路径格式
        try:
            # 尝试规范化路径
            normalized_path = os.path.normpath(file_path)
            # 检查是否包含非法字符（Windows）
            if os.name == 'nt':
                illegal_chars = '<>:"|?*'
                if any(char in file_path for char in illegal_chars):
                    return False, f"文件路径包含非法字符: {illegal_chars}"
        except Exception as e:
            return False, f"文件路径格式错误: {str(e)}"

        # 检查文件是否存在
        if check_exists and not os.path.exists(file_path):
            return False, "文件不存在"

        # 检查是否为文件
        if check_exists and not os.path.isfile(file_path):
            return False, "路径不是文件"

        # 检查文件是否可读
        if check_exists and not os.access(file_path, os.R_OK):
            return False, "文件不可读"

        return True, "文件路径有效"

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        验证URL格式

        Args:
            url: URL地址

        Returns:
            (是否有效, 错误消息)
        """
        if not url:
            return False, "URL不能为空"

        # 简单的URL验证
        url_pattern = re.compile(
            r'^(https?://)'  # http:// or https://
            r'(([A-Z0-9][A-Z0-9_-]*)(\.[A-Z0-9][A-Z0-9_-]*)+)'  # domain
            r'(:\d+)?'  # optional port
            r'(/.*)?$',  # optional path
            re.IGNORECASE
        )

        if not url_pattern.match(url):
            return False, "URL格式不正确"

        return True, "URL格式正确"

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        验证电子邮件格式

        Args:
            email: 电子邮件地址

        Returns:
            (是否有效, 错误消息)
        """
        if not email:
            return False, "电子邮件不能为空"

        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

        if not email_pattern.match(email):
            return False, "电子邮件格式不正确"

        return True, "电子邮件格式正确"

    @staticmethod
    def validate_numeric_value(value: Any, min_val: Optional[float] = None,
                              max_val: Optional[float] = None) -> Tuple[bool, str]:
        """
        验证数值

        Args:
            value: 数值
            min_val: 最小值
            max_val: 最大值

        Returns:
            (是否有效, 错误消息)
        """
        try:
            # 尝试转换为浮点数
            num_value = float(value)

            # 检查最小值
            if min_val is not None and num_value < min_val:
                return False, f"值不能小于 {min_val}"

            # 检查最大值
            if max_val is not None and num_value > max_val:
                return False, f"值不能大于 {max_val}"

            # 检查是否为有限数
            if not float('-inf') < num_value < float('inf'):
                return False, "值不是有限数"

            return True, "数值有效"

        except (ValueError, TypeError):
            return False, "不是有效的数值"

    @staticmethod
    def validate_integer_value(value: Any, min_val: Optional[int] = None,
                              max_val: Optional[int] = None) -> Tuple[bool, str]:
        """
        验证整数值

        Args:
            value: 整数值
            min_val: 最小值
            max_val: 最大值

        Returns:
            (是否有效, 错误消息)
        """
        try:
            # 尝试转换为整数
            int_value = int(value)

            # 检查最小值
            if min_val is not None and int_value < min_val:
                return False, f"值不能小于 {min_val}"

            # 检查最大值
            if max_val is not None and int_value > max_val:
                return False, f"值不能大于 {max_val}"

            return True, "整数值有效"

        except (ValueError, TypeError):
            return False, "不是有效的整数"

    @staticmethod
    def validate_string(value: str, min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       pattern: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证字符串

        Args:
            value: 字符串值
            min_length: 最小长度
            max_length: 最大长度
            pattern: 正则表达式模式

        Returns:
            (是否有效, 错误消息)
        """
        if not isinstance(value, str):
            return False, "不是字符串"

        # 检查最小长度
        if min_length is not None and len(value) < min_length:
            return False, f"字符串长度不能小于 {min_length}"

        # 检查最大长度
        if max_length is not None and len(value) > max_length:
            return False, f"字符串长度不能大于 {max_length}"

        # 检查正则表达式模式
        if pattern is not None:
            if not re.match(pattern, value):
                return False, "字符串格式不正确"

        return True, "字符串有效"

    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: Dict[str, type]) -> Tuple[bool, str, Dict[str, str]]:
        """
        验证配置字典

        Args:
            config: 配置字典
            required_fields: 必需字段及其类型

        Returns:
            (是否有效, 错误消息, 详细错误信息)
        """
        errors = {}

        # 检查必需字段
        for field_name, field_type in required_fields.items():
            if field_name not in config:
                errors[field_name] = f"缺少必需字段: {field_name}"
                continue

            value = config[field_name]

            # 检查类型
            if not isinstance(value, field_type):
                errors[field_name] = f"字段类型错误，应为 {field_type.__name__}，实际为 {type(value).__name__}"
                continue

            # 特殊类型验证
            if field_type == str and not value:
                errors[field_name] = "字符串不能为空"
            elif field_type == int and value <= 0:
                errors[field_name] = "整数值必须大于0"
            elif field_type == float and value <= 0:
                errors[field_name] = "浮点数值必须大于0"

        if errors:
            return False, "配置验证失败", errors

        return True, "配置有效", {}

    @staticmethod
    def validate_pdf_content(file_path: str) -> Tuple[bool, str]:
        """
        验证PDF文件内容

        Args:
            file_path: PDF文件路径

        Returns:
            (是否有效, 错误消息)
        """
        try:
            import pdfplumber

            with pdfplumber.open(file_path) as pdf:
                # 检查页数
                if len(pdf.pages) == 0:
                    return False, "PDF文件没有页面"

                # 检查是否有文本内容
                total_text = ""
                for page in pdf.pages[:5]:  # 只检查前5页
                    text = page.extract_text()
                    if text:
                        total_text += text

                if len(total_text.strip()) < 100:
                    return False, "PDF文件文本内容过少（可能为扫描图像）"

                # 检查是否包含CFST相关关键词
                cfst_keywords = ['CFST', 'concrete-filled', '钢管混凝土', '实验', '数据']
                text_lower = total_text.lower()
                has_keywords = any(keyword.lower() in text_lower for keyword in cfst_keywords)

                if not has_keywords:
                    return False, "PDF文件可能不包含CFST实验数据"

                return True, "PDF文件内容有效"

        except Exception as e:
            return False, f"PDF内容验证失败: {str(e)}"

    @staticmethod
    def validate_excel_file(file_path: str) -> Tuple[bool, str]:
        """
        验证Excel文件

        Args:
            file_path: Excel文件路径

        Returns:
            (是否有效, 错误消息)
        """
        try:
            import pandas as pd

            # 检查文件扩展名
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return False, "文件扩展名不是Excel格式"

            # 尝试读取Excel文件
            try:
                df = pd.read_excel(file_path, nrows=5)  # 只读取前5行
                if df.empty:
                    return False, "Excel文件为空"
                return True, "Excel文件有效"
            except Exception as e:
                return False, f"Excel文件读取失败: {str(e)}"

        except ImportError:
            return False, "未安装pandas库，无法验证Excel文件"

    @staticmethod
    def validate_network_connection(url: str = "https://api.deepseek.com",
                                   timeout: int = 5) -> Tuple[bool, str]:
        """
        验证网络连接

        Args:
            url: 测试URL
            timeout: 超时时间（秒）

        Returns:
            (是否有效, 错误消息)
        """
        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, method='HEAD')
            response = urllib.request.urlopen(req, timeout=timeout)
            status_code = response.getcode()

            if 200 <= status_code < 400:
                return True, "网络连接正常"
            else:
                return False, f"网络连接异常，状态码: {status_code}"

        except urllib.error.URLError as e:
            return False, f"网络连接失败: {str(e)}"
        except Exception as e:
            return False, f"网络验证失败: {str(e)}"

    @staticmethod
    def validate_system_resources() -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证系统资源

        Returns:
            (是否有效, 错误消息, 资源信息)
        """
        try:
            import psutil
            import platform

            resources = {
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            }

            # 检查内存
            memory = psutil.virtual_memory()
            if memory.available < 500 * 1024 * 1024:  # 500MB
                return False, "系统内存不足", resources

            # 检查磁盘空间
            disk = psutil.disk_usage('/') if os.name != 'nt' else psutil.disk_usage('C:')
            if disk.free < 1 * 1024 * 1024 * 1024:  # 1GB
                return False, "磁盘空间不足", resources

            return True, "系统资源充足", resources

        except ImportError:
            return True, "无法检查系统资源（未安装psutil）", {}
        except Exception as e:
            return False, f"系统资源检查失败: {str(e)}", {}