# -*- mode: python ; coding: utf-8 -*-
"""
CFST Data Extractor PyInstaller spec 文件
用于构建 Windows .exe 可执行文件
"""

import os
import sys
from pathlib import Path

# 项目根目录 - 使用绝对路径
project_root = Path("/home/thelya/Work/test01/data/CFST_Data_Extractor")

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(project_root))

# 块加密（可选）
block_cipher = None

# 分析阶段
a = Analysis(
    [str(project_root / 'main_gui.py')],  # 主入口文件
    pathex=[str(project_root)],  # 搜索路径
    binaries=[],  # 二进制文件
    datas=[
        # 资源文件
        (str(project_root / 'resources' / 'config.ini'), 'resources'),
        (str(project_root / 'resources' / 'styles.qss'), 'resources'),

        # 配置文件
        (str(project_root / 'config.ini'), '.'),

        # 图标文件（如果需要）
        # (str(project_root / '*.png'), 'icons'),
        # (str(project_root / '*.svg'), 'icons'),
    ],
    hiddenimports=[
        # PySide6 模块
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',

        # 数据处理模块
        'instructor',
        'pydantic',
        'pydantic_core',
        'pdfplumber',
        'openai',
        'numpy',
        'pandas',

        # 安全存储模块
        'keyring',
        'keyring.backends.Windows',
        'keyring.backends.macOS',
        'keyring.backends.SecretService',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.backends',

        # 系统工具
        'psutil',
        'configparser',

        # 标准库模块（可能被动态导入）
        'json',
        'hashlib',
        'base64',
        'datetime',
        'typing',
        'threading',
        'queue',
        'pathlib',
        'shutil',
        'traceback',
        'logging',
        'collections',
        'collections.abc',
        'importlib',
        'importlib.metadata',
        'importlib.resources',
    ],
    hookspath=[],  # 自定义钩子路径
    hooksconfig={},  # 钩子配置
    runtime_hooks=[],  # 运行时钩子
    excludes=[],  # 排除模块
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 收集 pdfplumber 的数据文件
try:
    import pdfplumber
    pdfplumber_path = Path(pdfplumber.__file__).parent
    for data_file in pdfplumber_path.rglob('*.json'):
        rel_path = data_file.relative_to(pdfplumber_path)
        a.datas.append((str(data_file), str(Path('pdfplumber') / rel_path)))
except ImportError:
    pass

# 收集 PySide6 的翻译文件
try:
    import PySide6
    pyside6_path = Path(PySide6.__file__).parent
    translations_path = pyside6_path / 'translations'
    if translations_path.exists():
        for qt_file in translations_path.glob('*.qm'):
            a.datas.append((str(qt_file), 'PySide6/translations'))
except ImportError:
    pass

# 收集 PySide6 的插件
try:
    import PySide6
    pyside6_path = Path(PySide6.__file__).parent
    plugins_path = pyside6_path / 'plugins'
    if plugins_path.exists():
        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir():
                for plugin_file in plugin_dir.rglob('*.dll'):
                    rel_path = plugin_file.relative_to(pyside6_path)
                    a.binaries.append((str(plugin_file), str(rel_path)))
except ImportError:
    pass

# 创建 PY 文件归档
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CFST_Data_Extractor',  # 可执行文件名
    debug=False,  # 调试模式
    bootloader_ignore_signals=False,
    strip=False,  # 剥离符号
    upx=True,  # 使用 UPX 压缩
    upx_exclude=[],  # UPX 排除文件
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    icon=None,  # 应用程序图标（无图标）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # 目标架构
    codesign_identity=None,  # 代码签名标识
    entitlements_file=None,  # 权限文件
)

# 收集阶段（如果需要额外的文件）
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='CFST_Data_Extractor',  # 输出目录名
# )

# 添加版本信息（可选）
# VersionInfo(
#     # 版本信息
#     version='1.0.0.0',
#     company_name='CFST Research',
#     file_description='CFST Data Extractor - 钢管混凝土实验数据提取工具',
#     internal_name='CFST Data Extractor',
#     legal_copyright='Copyright © 2026 CFST Research. All rights reserved.',
#     original_filename='CFST_Data_Extractor.exe',
#     product_name='CFST Data Extractor',
#     translations=[0, 0x409]  # 英语（美国）
# )