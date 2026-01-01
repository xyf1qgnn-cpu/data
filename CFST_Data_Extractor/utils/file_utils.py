"""
文件操作工具函数
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
import logging


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def get_pdf_files(directory: str) -> List[str]:
        """
        获取目录中的所有PDF文件

        Args:
            directory: 目录路径

        Returns:
            PDF文件路径列表
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")

        pdf_files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    pdf_files.append(file_path)

        return sorted(pdf_files)

    @staticmethod
    def count_pdf_files(directory: str) -> int:
        """
        统计目录中的PDF文件数量

        Args:
            directory: 目录路径

        Returns:
            PDF文件数量
        """
        return len(FileUtils.get_pdf_files(directory))

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）

        Args:
            file_path: 文件路径

        Returns:
            文件大小（字节）
        """
        return os.path.getsize(file_path)

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        计算文件哈希值

        Args:
            file_path: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256）

        Returns:
            文件哈希值
        """
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    @staticmethod
    def create_directory(directory: str) -> bool:
        """
        创建目录（如果不存在）

        Args:
            directory: 目录路径

        Returns:
            是否成功创建
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败 {directory}: {e}")
            return False

    @staticmethod
    def safe_move_file(src_path: str, dst_path: str) -> bool:
        """
        安全移动文件

        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径

        Returns:
            是否成功移动
        """
        try:
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            FileUtils.create_directory(dst_dir)

            # 如果目标文件已存在，添加后缀
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(dst_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dst_path = f"{base}_{counter}{ext}"

            shutil.move(src_path, dst_path)
            return True
        except Exception as e:
            logging.error(f"移动文件失败 {src_path} -> {dst_path}: {e}")
            return False

    @staticmethod
    def safe_copy_file(src_path: str, dst_path: str) -> bool:
        """
        安全复制文件

        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径

        Returns:
            是否成功复制
        """
        try:
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            FileUtils.create_directory(dst_dir)

            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            logging.error(f"复制文件失败 {src_path} -> {dst_path}: {e}")
            return False

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logging.error(f"删除文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def secure_delete_file(file_path: str, passes: int = 3) -> bool:
        """
        安全删除文件（多次覆盖）

        Args:
            file_path: 文件路径
            passes: 覆盖次数

        Returns:
            是否成功删除
        """
        try:
            if not os.path.exists(file_path):
                return True

            file_size = os.path.getsize(file_path)

            # 多次覆盖文件内容
            with open(file_path, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    # 使用随机数据覆盖
                    f.write(os.urandom(file_size))

            # 删除文件
            os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"安全删除文件失败 {file_path}: {e}")
            # 回退到普通删除
            return FileUtils.delete_file(file_path)

    @staticmethod
    def get_file_info(file_path: str) -> Optional[dict]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)
            return {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            logging.error(f"获取文件信息失败 {file_path}: {e}")
            return None

    @staticmethod
    def validate_pdf_file(file_path: str) -> Tuple[bool, str]:
        """
        验证PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            (是否有效, 错误消息)
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "文件不存在"

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "文件为空"
            if file_size > 100 * 1024 * 1024:  # 100MB
                return False, "文件过大（超过100MB）"

            # 检查文件扩展名
            if not file_path.lower().endswith('.pdf'):
                return False, "文件扩展名不是.pdf"

            # 检查文件是否可读
            if not os.access(file_path, os.R_OK):
                return False, "文件不可读"

            # 简单的PDF文件头检查
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False, "不是有效的PDF文件"

            return True, "文件有效"

        except Exception as e:
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24) -> int:
        """
        清理临时文件

        Args:
            temp_dir: 临时目录
            max_age_hours: 最大保留时间（小时）

        Returns:
            删除的文件数量
        """
        import time
        deleted_count = 0

        if not os.path.exists(temp_dir):
            return 0

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
            except Exception as e:
                logging.error(f"清理临时文件失败 {file_path}: {e}")

        return deleted_count

    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        获取目录大小（字节）

        Args:
            directory: 目录路径

        Returns:
            目录大小（字节）
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    @staticmethod
    def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
        """
        按模式查找文件

        Args:
            directory: 目录路径
            pattern: 文件模式（支持通配符）

        Returns:
            匹配的文件路径列表
        """
        import fnmatch
        matches = []
        for root, dirs, files in os.walk(directory):
            for filename in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, filename))
        return matches