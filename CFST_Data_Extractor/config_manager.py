"""
配置管理器 - 处理应用程序设置和持久化
"""

import os
import json
import configparser
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器，处理应用程序设置"""

    def __init__(self, config_path: str = "config.ini"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.default_config = self.get_default_config()
        self.load_config()

    def get_default_config(self) -> Dict[str, Dict[str, str]]:
        """获取默认配置"""
        return {
            'General': {
                'last_directory': '',
                'window_width': '1000',
                'window_height': '700',
                'window_x': '100',
                'window_y': '100',
                'theme': 'default',
                'language': 'zh_CN',
                'auto_save_logs': 'true',
                'log_level': 'INFO'
            },
            'Processing': {
                'max_retries': '3',
                'retry_delay': '5',
                'timeout': '30',
                'batch_size': '1',
                'concurrent_files': '1',
                'auto_start_processing': 'false',
                'notify_on_completion': 'true'
            },
            'API': {
                'base_url': 'https://api.deepseek.com',
                'model_name': 'deepseek-chat',
                'temperature': '0.1',
                'max_tokens': '8192',
                'request_timeout': '60',
                'enable_streaming': 'false'
            },
            'Directories': {
                'not_input_dir': 'NotInput',
                'excluded_dir': 'Excluded',
                'output_dir': '.',
                'log_dir': 'logs',
                'temp_dir': 'temp'
            },
            'UI': {
                'show_welcome_message': 'true',
                'auto_scroll_logs': 'true',
                'show_line_numbers': 'true',
                'font_size': '10',
                'font_family': 'Microsoft YaHei'
            },
            'Security': {
                'encrypt_api_key': 'true',
                'clear_temp_files': 'true',
                'secure_delete': 'false',
                'log_sensitive_data': 'false'
            }
        }

    def load_config(self) -> bool:
        """
        加载配置文件

        Returns:
            是否成功加载
        """
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
                # 确保所有默认部分都存在
                self.ensure_default_sections()
                return True
            else:
                # 创建默认配置
                self.config.read_dict(self.default_config)
                self.save_config()
                return True
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用默认配置
            self.config.read_dict(self.default_config)
            return False

    def save_config(self) -> bool:
        """
        保存配置文件

        Returns:
            是否成功保存
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def ensure_default_sections(self):
        """确保所有默认部分都存在"""
        for section, options in self.default_config.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, default_value in options.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, default_value)

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取设置值

        Args:
            section: 配置部分
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        try:
            value = self.config.get(section, key)
            # 尝试转换为适当类型
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            elif value.isdigit():
                return int(value)
            elif self.is_float(value):
                return float(value)
            else:
                return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def set_setting(self, section: str, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            section: 配置部分
            key: 配置键
            value: 配置值

        Returns:
            是否成功设置
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, key, str(value))
            return True
        except Exception as e:
            print(f"设置配置失败: {e}")
            return False

    def get_processing_config(self) -> Dict[str, Any]:
        """获取处理配置"""
        return {
            'max_retries': self.get_setting('Processing', 'max_retries', 3),
            'retry_delay': self.get_setting('Processing', 'retry_delay', 5),
            'timeout': self.get_setting('Processing', 'timeout', 30),
            'batch_size': self.get_setting('Processing', 'batch_size', 1),
            'concurrent_files': self.get_setting('Processing', 'concurrent_files', 1)
        }

    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'base_url': self.get_setting('API', 'base_url', 'https://api.deepseek.com'),
            'model_name': self.get_setting('API', 'model_name', 'deepseek-chat'),
            'temperature': self.get_setting('API', 'temperature', 0.1),
            'max_tokens': self.get_setting('API', 'max_tokens', 8192),
            'request_timeout': self.get_setting('API', 'request_timeout', 60)
        }

    def get_directory_config(self) -> Dict[str, str]:
        """获取目录配置"""
        return {
            'not_input_dir': self.get_setting('Directories', 'not_input_dir', 'NotInput'),
            'excluded_dir': self.get_setting('Directories', 'excluded_dir', 'Excluded'),
            'output_dir': self.get_setting('Directories', 'output_dir', '.'),
            'log_dir': self.get_setting('Directories', 'log_dir', 'logs'),
            'temp_dir': self.get_setting('Directories', 'temp_dir', 'temp')
        }

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            'show_welcome_message': self.get_setting('UI', 'show_welcome_message', True),
            'auto_scroll_logs': self.get_setting('UI', 'auto_scroll_logs', True),
            'show_line_numbers': self.get_setting('UI', 'show_line_numbers', True),
            'font_size': self.get_setting('UI', 'font_size', 10),
            'font_family': self.get_setting('UI', 'font_family', 'Microsoft YaHei')
        }

    def get_security_config(self) -> Dict[str, bool]:
        """获取安全配置"""
        return {
            'encrypt_api_key': self.get_setting('Security', 'encrypt_api_key', True),
            'clear_temp_files': self.get_setting('Security', 'clear_temp_files', True),
            'secure_delete': self.get_setting('Security', 'secure_delete', False),
            'log_sensitive_data': self.get_setting('Security', 'log_sensitive_data', False)
        }

    def set_last_directory(self, directory: str) -> bool:
        """
        设置最后使用的目录

        Args:
            directory: 目录路径

        Returns:
            是否成功设置
        """
        return self.set_setting('General', 'last_directory', directory)

    def get_last_directory(self) -> str:
        """
        获取最后使用的目录

        Returns:
            目录路径
        """
        return self.get_setting('General', 'last_directory', '')

    def set_window_geometry(self, width: int, height: int, x: int, y: int) -> bool:
        """
        设置窗口几何信息

        Args:
            width: 窗口宽度
            height: 窗口高度
            x: 窗口X坐标
            y: 窗口Y坐标

        Returns:
            是否成功设置
        """
        success = True
        success &= self.set_setting('General', 'window_width', width)
        success &= self.set_setting('General', 'window_height', height)
        success &= self.set_setting('General', 'window_x', x)
        success &= self.set_setting('General', 'window_y', y)
        return success

    def get_window_geometry(self) -> Dict[str, int]:
        """
        获取窗口几何信息

        Returns:
            窗口几何信息字典
        """
        return {
            'width': self.get_setting('General', 'window_width', 1000),
            'height': self.get_setting('General', 'window_height', 700),
            'x': self.get_setting('General', 'window_x', 100),
            'y': self.get_setting('General', 'window_y', 100)
        }

    def export_config(self, export_path: str) -> bool:
        """
        导出配置到文件

        Args:
            export_path: 导出文件路径

        Returns:
            是否成功导出
        """
        try:
            export_config = configparser.ConfigParser()
            export_config.read_dict({section: dict(self.config.items(section))
                                    for section in self.config.sections()})

            with open(export_path, 'w', encoding='utf-8') as f:
                export_config.write(f)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """
        从文件导入配置

        Args:
            import_path: 导入文件路径

        Returns:
            是否成功导入
        """
        try:
            if not os.path.exists(import_path):
                return False

            import_config = configparser.ConfigParser()
            import_config.read(import_path, encoding='utf-8')

            # 合并配置
            for section in import_config.sections():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in import_config.items(section):
                    self.config.set(section, key, value)

            self.save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.config.clear()
            self.config.read_dict(self.default_config)
            return self.save_config()
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False

    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """获取所有设置"""
        settings = {}
        for section in self.config.sections():
            settings[section] = {}
            for key, value in self.config.items(section):
                settings[section][key] = self.get_setting(section, key)
        return settings

    @staticmethod
    def is_float(value: str) -> bool:
        """检查字符串是否可以转换为浮点数"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def ensure_directories_exist(self):
        """确保所有配置的目录都存在"""
        dir_config = self.get_directory_config()
        for dir_key, dir_path in dir_config.items():
            if dir_path and not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    print(f"创建目录失败 {dir_path}: {e}")