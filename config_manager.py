"""
Configuration Manager for CFST Data Extractor
Handles validation and management of config.json settings
"""

import json
import os
import shutil
import platform
from typing import Dict, Any


class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete configuration with detailed error messages.

    Args:
        config: Configuration dictionary

    Returns:
        Validated config with defaults applied

    Raises:
        ConfigError: If required configuration is missing or invalid
    """
    errors = []

    # Validate API settings
    if "api_settings" not in config or not isinstance(config["api_settings"], dict):
        errors.append("缺少 'api_settings' 配置节")
    else:
        errors.extend(validate_api_settings(config["api_settings"]))

    # Validate processing settings
    if "processing_settings" not in config or not isinstance(config["processing_settings"], dict):
        errors.append("缺少 'processing_settings' 配置节")
    else:
        errors.extend(validate_processing_settings(config["processing_settings"]))

    # Validate paths
    if "paths" not in config or not isinstance(config["paths"], dict):
        errors.append("缺少 'paths' 配置节")
    else:
        errors.extend(validate_paths(config["paths"]))

    # Check for any validation errors
    if errors:
        error_message = "配置验证失败:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ConfigError(error_message)

    return config


def validate_api_settings(api_settings: Dict[str, Any]) -> list:
    """
    Validate API settings with specific checks for each field.

    Args:
        api_settings: API settings dictionary

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check api_key
    if "api_key" not in api_settings or not api_settings["api_key"]:
        errors.append("api_settings.api_key: API密钥未填写，请在config.json中设置")
    elif api_settings["api_key"] == "YOUR_KEY_HERE":
        errors.append("api_settings.api_key: API密钥仍为默认值，请替换为实际密钥")
    elif not isinstance(api_settings["api_key"], str):
        errors.append("api_settings.api_key: API密钥必须是字符串")

    # Check base_url
    if "base_url" not in api_settings or not api_settings["base_url"]:
        errors.append("api_settings.base_url: Base URL未填写")
    elif not isinstance(api_settings["base_url"], str):
        errors.append("api_settings.base_url: Base URL必须是字符串")
    elif not api_settings["base_url"].startswith(("http://", "https://")):
        errors.append(f"api_settings.base_url: Base URL格式无效: {api_settings['base_url']}")

    # Check model_name
    if "model_name" not in api_settings or not api_settings["model_name"]:
        errors.append("api_settings.model_name: 模型名称未填写")
    elif not isinstance(api_settings["model_name"], str):
        errors.append("api_settings.model_name: 模型名称必须是字符串")

    return errors


def validate_processing_settings(processing_settings: Dict[str, Any]) -> list:
    """
    Validate processing settings with type checks and reasonable defaults.

    Args:
        processing_settings: Processing settings dictionary

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check short_paper_threshold
    if "short_paper_threshold" in processing_settings:
        threshold = processing_settings["short_paper_threshold"]
        if not isinstance(threshold, int):
            errors.append("processing_settings.short_paper_threshold: 必须是整数")
        elif threshold <= 0:
            errors.append(f"processing_settings.short_paper_threshold: 值必须大于0，当前: {threshold}")
        elif threshold > 1000:
            errors.append(f"processing_settings.short_paper_threshold: 值过大({threshold})，建议≤100")
    else:
        # Use default if not provided
        processing_settings["short_paper_threshold"] = 15

    # Check max_scan_limit
    if "max_scan_limit" in processing_settings:
        limit = processing_settings["max_scan_limit"]
        if not isinstance(limit, int):
            errors.append("processing_settings.max_scan_limit: 必须是整数")
        elif limit <= 0:
            errors.append(f"processing_settings.max_scan_limit: 值必须大于0，当前: {limit}")
        elif limit > 100:
            errors.append(f"processing_settings.max_scan_limit: 值过大({limit})，建议≤50")
    else:
        processing_settings["max_scan_limit"] = 10

    # Check image_dpi
    if "image_dpi" in processing_settings:
        dpi = processing_settings["image_dpi"]
        if not isinstance(dpi, int):
            errors.append("processing_settings.image_dpi: 必须是整数")
        elif dpi < 72:
            errors.append(f"processing_settings.image_dpi: DPI过低({dpi})，可能影响识别质量")
        elif dpi > 600:
            errors.append(f"processing_settings.image_dpi: DPI过高({dpi})，可能影响性能")
    else:
        processing_settings["image_dpi"] = 150

    return errors


def validate_paths(paths: Dict[str, Any]) -> list:
    """
    Validate path settings exist.

    Args:
        paths: Paths settings dictionary

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    required_paths = ["windows_source_path", "archive_destination"]

    for path_key in required_paths:
        if path_key not in paths or not paths[path_key]:
            errors.append(f"paths.{path_key}: 路径未填写")
        elif not isinstance(paths[path_key], str):
            errors.append(f"paths.{path_key}: 路径必须是字符串")

    # manual_review_path is optional but should be string if provided
    if "manual_review_path" in paths and paths["manual_review_path"]:
        if not isinstance(paths["manual_review_path"], str):
            errors.append("paths.manual_review_path: 路径必须是字符串")
    else:
        # Set default if not provided
        paths["manual_review_path"] = "./Manual_Review"

    return errors


def check_poppler_installation() -> tuple[bool, str]:
    """
    Check if poppler is installed and available in PATH.

    Returns:
        Tuple of (is_installed, error_message)
            is_installed: True if poppler is found, False otherwise
            error_message: Installation instructions if not found
    """
    # Check for poppler utilities that pdf2image uses
    poppler_utils = ['pdftoppm', 'pdfinfo', 'pdftocairo']
    found_utils = []

    for util in poppler_utils:
        if shutil.which(util):
            found_utils.append(util)

    # We primarily need pdftoppm for pdf2image
    if 'pdftoppm' not in found_utils:
        system = platform.system()
        if system == "Linux":
            # Check if it's Ubuntu/Debian
            if os.path.exists("/etc/debian_version"):
                install_cmd = "sudo apt-get update && sudo apt-get install -y poppler-utils"
            else:
                install_cmd = "# 请使用您的包管理器安装 poppler-utils"

            error_msg = f"""
❌ 错误: 未找到 poppler 工具（pdftoppm）

pdf2image 需要 poppler 工具才能将 PDF 转换为图片。

安装方法:
{install_cmd}

安装完成后，请重新运行此程序。
            """.strip()
        elif system == "Windows":
            error_msg = """
❌ 错误: 未找到 poppler 工具（pdftoppm）

pdf2image 需要 poppler 工具才能将 PDF 转换为图片。

安装方法:
1. 下载 poppler for Windows:
   https://github.com/oschwartz10612/poppler-windows/releases/

2. 解压并将 bin 文件夹添加到系统 PATH 环境变量

3. 重新启动终端/IDE 并运行此程序

详细说明: https://github.com/Belval/pdf2image#windows
            """.strip()
        elif system == "Darwin":  # macOS
            error_msg = """
❌ 错误: 未找到 poppler 工具（pdftoppm）

pdf2image 需要 poppler 工具才能将 PDF 转换为图片。

安装方法:
brew install poppler

如果未安装 Homebrew，请先安装:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            """.strip()
        else:
            error_msg = """
❌ 错误: 未找到 poppler 工具（pdftoppm）

pdf2image 需要 poppler 工具才能将 PDF 转换为图片。

请使用您的包管理器安装 poppler-utils 或 poppler。
            """.strip()

        return False, error_msg

    return True, ""


def load_and_validate_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file and validate it.

    Args:
        config_path: Path to config.json file

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    if config_path is None:
        # Default to config.json in same directory
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Default config structure
    default_config = {
        "api_settings": {
            "api_key": "YOUR_KEY_HERE",
            "base_url": "https://api.ohmygpt.com/v1",
            "model_name": "vertex-gemini-3-flash-preview"
        },
        "processing_settings": {
            "short_paper_threshold": 15,
            "max_scan_limit": 10,
            "image_dpi": 150
        },
        "paths": {
            "windows_source_path": "/mnt/c/Users/username/Documents/PDF_Source",
            "archive_destination": "/mnt/e/Documents/data_extracted",
            "manual_review_path": "./Manual_Review"
        },
        "auto_cleanup": True,
        "auto_increment": True,
        "delete_existing_before_import": True,
        "cleanup_after_archive": True
    }

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Check if using old flat structure (backward compatibility)
        if "api_settings" not in config:
            print("警告: config.json使用旧结构。正在迁移到新结构...")
            # Migrate old structure to new
            migrated_config = default_config.copy()

            # Copy old path settings
            if "windows_source_path" in config:
                migrated_config["paths"]["windows_source_path"] = config["windows_source_path"]
            if "archive_destination" in config:
                migrated_config["paths"]["archive_destination"] = config["archive_destination"]
            if "manual_review_path" in config:
                migrated_config["paths"]["manual_review_path"] = config["manual_review_path"]

            # Copy other settings
            for key in ["auto_cleanup", "auto_increment", "delete_existing_before_import", "cleanup_after_archive"]:
                if key in config:
                    migrated_config[key] = config[key]

            # Save migrated config
            with open(config_path, 'w', encoding='utf-8') as fw:
                json.dump(migrated_config, fw, indent=2, ensure_ascii=False)

            print(f"配置已迁移并保存到 {config_path}")
            config = migrated_config

        # Merge with defaults for new structure
        # Handle nested merging carefully
        for section, section_defaults in default_config.items():
            if isinstance(section_defaults, dict):
                # For nested dicts, merge individually
                if section not in config:
                    config[section] = {}
                for key, value in section_defaults.items():
                    if key not in config[section]:
                        config[section][key] = value
            else:
                # For top-level non-dict values
                if section not in config:
                    config[section] = section_defaults

    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file JSON格式错误: {str(e)}")
    except Exception as e:
        raise ConfigError(f"无法读取配置文件: {str(e)}")

    # Validate the configuration
    validated_config = validate_config(config)
    print("配置验证通过！")
    print(f"  API模型: {validated_config['api_settings']['model_name']}")
    print(f"  短论文阈值: {validated_config['processing_settings']['short_paper_threshold']}页")
    print(f"  最大扫描限制: {validated_config['processing_settings']['max_scan_limit']}页")

    return validated_config


# Example usage
if __name__ == "__main__":
    try:
        config = load_and_validate_config()
        print("配置验证通过！")
        print(f"API设置: {config['api_settings']['model_name']}")
        print(f"处理设置: {config['processing_settings']['short_paper_threshold']}页")
    except ConfigError as e:
        print(f"配置错误: {e}")
        exit(1)
