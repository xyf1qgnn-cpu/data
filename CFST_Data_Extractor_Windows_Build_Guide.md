# CFST Data Extractor Windows构建指南

## 概述

本文档提供在Windows系统上构建CFST Data Extractor可执行文件(.exe)的详细步骤。当前在Linux/WSL2上构建的是ELF文件，需要在Windows上重新构建以获得真正的.exe文件。

## 构建环境要求

### 1. 系统要求
- **操作系统**: Windows 10/11 64-bit
- **Python版本**: 3.8+ (推荐3.9-3.11)
- **内存**: 至少4GB RAM
- **磁盘空间**: 至少2GB可用空间

### 2. 软件安装
1. **安装Python**: 从[python.org](https://www.python.org/downloads/)下载并安装Python 3.8+
2. **安装Git**: 从[git-scm.com](https://git-scm.com/download/win)下载并安装
3. **可选**: 安装Visual Studio Build Tools (用于某些Python包)

## 构建步骤

### 步骤1: 获取源代码
```bash
# 克隆仓库或复制文件到Windows
git clone <repository-url>
# 或从Linux/WSL复制
# 将 /home/thelya/Work/test01/data/CFST_Data_Extractor/ 复制到Windows
```

### 步骤2: 设置Python环境
```bash
# 打开命令提示符或PowerShell
cd CFST_Data_Extractor

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# PowerShell:
venv\Scripts\Activate.ps1
# 或命令提示符:
venv\Scripts\activate.bat

# 升级pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装PyInstaller
pip install pyinstaller
```

### 步骤3: 准备图标文件
1. 创建或获取应用程序图标文件
2. 格式要求: `.ico` 格式，推荐尺寸: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16
3. 将图标文件保存为: `resources/app.ico`

**图标创建工具**:
- [IcoFX](https://icofx.ro/) - 专业图标编辑器
- [GIMP](https://www.gimp.org/) - 免费图像编辑器
- 在线转换工具: [convertio.co](https://convertio.co/png-ico/)

### 步骤4: 修改spec文件
编辑 `spec/cfst_extractor.spec`:

```python
# 修改项目根目录路径
project_root = Path(r"C:\path\to\CFST_Data_Extractor")  # 使用Windows路径

# 取消注释图标相关配置
icon=str(project_root / 'resources' / 'app.ico'),  # 应用程序图标

# 取消注释COLLECT部分（如果需要目录结构）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CFST_Data_Extractor',  # 输出目录名
)

# 取消注释VersionInfo部分
VersionInfo(
    version='1.0.0.0',
    company_name='CFST Research',
    file_description='CFST Data Extractor - Concrete-Filled Steel Tube Experimental Data Extraction Tool',
    internal_name='CFST Data Extractor',
    legal_copyright='Copyright © 2026 CFST Research. All rights reserved.',
    original_filename='CFST_Data_Extractor.exe',
    product_name='CFST Data Extractor',
    translations=[0, 0x409]  # 英语（美国）
)
```

### 步骤5: 构建可执行文件
```bash
# 使用spec文件构建
pyinstaller spec/cfst_extractor.spec --clean

# 或使用命令行参数构建
pyinstaller ^
    --name="CFST_Data_Extractor" ^
    --windowed ^
    --icon=resources/app.ico ^
    --add-data="resources/config.ini;resources" ^
    --add-data="resources/styles.qss;resources" ^
    --add-data="resources/app.ico;resources" ^
    --hidden-import=instructor ^
    --hidden-import=pydantic ^
    --hidden-import=keyring.backends.Windows ^
    --hidden-import=cryptography ^
    --collect-all=pdfplumber ^
    --clean ^
    --onefile ^
    main_gui.py
```

### 步骤6: 验证构建结果
1. 检查 `dist/` 目录是否包含 `CFST_Data_Extractor.exe`
2. 文件大小: 预计50-150MB
3. 右键属性查看版本信息

## 测试指南

### 1. 基本功能测试
```bash
# 运行应用程序
dist\CFST_Data_Extractor.exe
```

**测试项目**:
- [ ] 应用程序正常启动
- [ ] 窗口标题显示正确
- [ ] 所有菜单项可用
- [ ] 文件选择对话框正常工作
- [ ] API密钥输入框功能正常
- [ ] 按钮状态正确更新

### 2. 处理流程测试
1. **准备测试数据**: 创建 `test_files/` 目录，放入示例PDF文件
2. **API密钥测试**: 使用测试API密钥或实际DeepSeek API密钥
3. **处理测试**: 选择目录并开始处理
4. **结果验证**: 检查生成的Excel文件

### 3. 错误处理测试
- [ ] 无API密钥时尝试处理
- [ ] 无效API密钥测试
- [ ] 空目录处理
- [ ] 非PDF文件处理
- [ ] 网络中断测试

### 4. 性能测试
- [ ] 启动时间: <5秒
- [ ] 内存使用: <500MB
- [ ] 多文件处理稳定性
- [ ] 长时间运行稳定性

## 常见问题解决

### 1. 构建失败问题
**问题**: `ModuleNotFoundError`
**解决**: 确保所有依赖已安装，检查hiddenimports配置

**问题**: 图标文件找不到
**解决**: 确认图标文件路径正确，使用绝对路径

**问题**: 文件过大
**解决**: 启用UPX压缩，排除不必要的库

### 2. 运行时问题
**问题**: 应用程序闪退
**解决**:
1. 检查依赖库是否完整
2. 查看Windows事件查看器日志
3. 尝试在命令提示符运行查看错误信息

**问题**: 中文显示异常
**解决**: 已将所有界面翻译为英文，确保使用英文界面

**问题**: API密钥保存失败
**解决**: 检查Windows Credential Manager权限

### 3. 性能问题
**问题**: 启动缓慢
**解决**: 使用单文件模式，减少文件数量

**问题**: 内存占用高
**解决**: 优化图像资源，减少不必要的导入

## 打包分发

### 1. 创建安装包
```bash
# 使用Inno Setup创建安装程序
# 下载: https://jrsoftware.org/isdl.php

# 或使用NSIS
# 下载: https://nsis.sourceforge.io/Download
```

### 2. 创建ZIP分发包
```powershell
# PowerShell
Compress-Archive -Path dist\* -DestinationPath CFST_Data_Extractor_v1.0.zip

# 或手动创建包含以下内容的ZIP:
# - CFST_Data_Extractor.exe
# - resources/ 目录
# - README.md
# - 示例文件目录
```

### 3. 数字签名（可选）
```bash
# 使用signtool进行代码签名
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com CFST_Data_Extractor.exe
```

## 维护和更新

### 1. 版本管理
- 更新 `__init__.py` 中的版本号
- 更新spec文件中的VersionInfo
- 更新README.md中的版本信息

### 2. 依赖更新
```bash
# 更新requirements.txt
pip freeze > requirements.txt

# 测试新版本兼容性
pip install -U package_name
```

### 3. 构建自动化
创建 `build_windows.bat`:
```batch
@echo off
echo Building CFST Data Extractor for Windows...

REM 清理旧构建
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt

REM 构建
pyinstaller spec/cfst_extractor.spec --clean

echo Build complete!
pause
```

## 附录

### A. 推荐的图标尺寸
- 256x256 (Windows Vista+)
- 128x128
- 64x64
- 48x48
- 32x32
- 24x24
- 16x16

### B. Windows API密钥存储
应用程序使用Windows Credential Manager存储API密钥，位置:
- `控制面板` → `用户账户` → `凭据管理器` → `Windows凭据`

### C. 调试技巧
1. **控制台输出**: 构建时使用 `--console` 参数查看输出
2. **日志文件**: 检查应用程序生成的日志文件
3. **依赖检查**: 使用 `dependencywalker.com` 检查DLL依赖

### D. 联系方式
- 问题报告: GitHub Issues
- 技术支持: 项目维护团队
- 文档更新: 提交Pull Request

---
*最后更新: 2026-01-01*
*文档版本: 1.0*