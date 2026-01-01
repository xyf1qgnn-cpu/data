# CFST Data Extractor GUI

Concrete-Filled Steel Tube Experimental Data Extraction Tool - Graphical User Interface Version

## 项目概述

CFST Data Extractor GUI is a PySide6-based Windows desktop application for batch processing PDF files, extracting concrete-filled steel tube experimental data, and performing structured processing through DeepSeek AI API.

**Project Upgrade Summary (2026-01-01):**
- ✅ **Complete GUI Application**: Full PySide6 GUI interface with English localization
- ✅ **Core Processing Logic**: Wrapped existing command-line workflow into reusable classes
- ✅ **Threaded Processing**: QThread-based background processing with real-time progress updates
- ✅ **Secure API Key Management**: Encrypted storage using Windows Credential Manager
- ✅ **Configuration Management**: INI-based settings with persistence
- ✅ **Dual Output Display**: Separate log and error display areas
- ✅ **Build System**: PyInstaller configuration for .exe packaging
- ✅ **English Interface**: All GUI text translated from Chinese to English

## Features

### Core Features
- **Batch PDF Processing**: Automatically scans PDF files in directories
- **AI Data Extraction**: Uses DeepSeek API for structured data extraction
- **Physical Validation**: Applies physical formulas to validate data rationality
- **Excel Export**: Generates styled Excel files
- **Error Handling**: Automatically classifies failed and excluded files

### User Interface
- **Modern GUI**: PySide6-based modern interface with English localization
- **Progress Display**: Real-time processing progress and status updates
- **Dual Output Areas**: Separate log and error display regions
- **API Key Management**: Secure storage and input of API keys
- **Settings Persistence**: Remembers user preferences and last used directories

### Security Features
- **API Key Encryption**: Uses Windows Credential Manager or encrypted file storage
- **Secure Deletion**: Optional secure deletion of temporary files
- **Input Validation**: Validates user input and file paths

## 系统要求

### 最低要求
- **操作系统**：Windows 10/11 (64-bit)
- **内存**：4GB RAM
- **存储空间**：500MB 可用空间
- **网络连接**：需要访问 DeepSeek API

### 推荐配置
- **操作系统**：Windows 11 (64-bit)
- **处理器**：Intel i5 或同等性能
- **内存**：8GB RAM
- **存储空间**：1GB 可用空间
- **网络连接**：稳定的互联网连接

## 安装说明

### 方法一：使用预编译的 .exe 文件
1. 下载最新版本的 `CFST_Data_Extractor_v1.0.zip`
2. 解压到任意目录
3. 运行 `CFST_Data_Extractor.exe`

### 方法二：从源代码构建
1. 安装 Python 3.8+
2. 克隆或下载源代码
3. 运行构建脚本：
   ```bash
   chmod +x build_exe.sh
   ./build_exe.sh
   ```

### 方法三：Python 环境运行
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行应用程序：
   ```bash
   python main_gui.py
   ```

## 使用指南

### 首次使用
1. **获取API密钥**：
   - 访问 [DeepSeek 官网](https://platform.deepseek.com/)
   - 注册账号并创建API密钥
   - 密钥以 "sk-" 开头

2. **准备PDF文件**：
   - 将PDF文件放入 `files/` 目录
   - 支持批量处理多个文件

3. **启动应用程序**：
   - 运行 `CFST_Data_Extractor.exe`
   - 输入API密钥并保存
   - 选择PDF文件目录

### 处理流程
1. **选择目录**：点击"选择目录"按钮，选择包含PDF文件的目录
2. **输入API密钥**：在API密钥输入框中输入您的DeepSeek API密钥
3. **开始处理**：点击"开始处理"按钮启动批量处理
4. **监控进度**：查看进度条和日志信息
5. **查看结果**：处理完成后，查看Excel文件和统计信息

### 目录结构
```
CFST_Data_Extractor/
├── files/          # 输入：放置PDF文件
├── NotInput/       # 输出：处理失败的文件
├── Excluded/       # 输出：被排除的文件
├── logs/           # 日志文件
└── config.ini      # 配置文件
```

## 配置说明

### 配置文件 (config.ini)
应用程序使用 `config.ini` 文件保存设置：

```ini
[General]
last_directory = 最后使用的目录
theme = default      # 界面主题
language = zh_CN     # 界面语言

[Processing]
max_retries = 3      # 最大重试次数
retry_delay = 5      # 重试延迟（秒）

[API]
base_url = https://api.deepseek.com
model_name = deepseek-chat
temperature = 0.1
```

### API密钥存储
- **Windows系统**：使用 Windows Credential Manager 安全存储
- **其他系统**：使用加密的配置文件存储
- **安全特性**：密钥在存储前加密，确保安全

## 故障排除

### 常见问题

#### 1. API密钥无效
- **症状**：API测试失败，无法处理文件
- **解决方案**：
  - 检查API密钥格式（应以 "sk-" 开头）
  - 确认API密钥有足够额度
  - 检查网络连接

#### 2. PDF文件无法处理
- **症状**：文件被移动到 NotInput/ 目录
- **解决方案**：
  - 检查PDF文件是否损坏
  - 确保PDF包含文本内容（非扫描图像）
  - 尝试使用其他PDF阅读器打开

#### 3. 内存不足
- **症状**：处理大文件时程序崩溃
- **解决方案**：
  - 减少同时处理的文件数量
  - 增加系统内存
  - 关闭其他占用内存的程序

#### 4. 网络连接问题
- **症状**：API调用超时或失败
- **解决方案**：
  - 检查网络连接
  - 增加超时时间设置
  - 使用代理服务器（如果需要）

### 日志文件
应用程序在 `logs/` 目录中生成日志文件：
- `app_YYYYMMDD.log`：应用程序日志
- `error_YYYYMMDD.log`：错误日志
- `debug_YYYYMMDD.log`：调试日志（如果启用）

## 开发指南

### 项目结构
```
CFST_Data_Extractor/
├── main_gui.py              # 主GUI应用程序
├── core_processor.py        # 核心处理逻辑
├── config_manager.py        # 配置管理
├── secure_storage.py        # 安全存储
├── processing_thread.py     # 处理线程
├── widgets/                 # 自定义GUI组件
│   ├── api_key_widget.py    # API密钥组件
│   ├── progress_widget.py   # 进度组件
│   └── dual_output_widget.py # 双输出组件
├── resources/               # 资源文件
│   ├── app.ico             # 应用程序图标
│   ├── config.ini          # 默认配置
│   └── styles.qss          # 样式表
├── spec/                    # PyInstaller配置
│   └── cfst_extractor.spec # 构建spec文件
└── requirements.txt         # Python依赖
```

### 代码规范
- **代码风格**：遵循 PEP 8 规范
- **类型提示**：使用 Python 类型提示
- **文档字符串**：所有函数和类都有文档字符串
- **错误处理**：适当的异常处理和日志记录

### 构建和打包
```bash
# 使用构建脚本
./build_exe.sh

# 手动构建
pyinstaller spec/cfst_extractor.spec
```

## 版本历史

### v1.0.0 (2026-01-01)
- 初始版本发布
- 完整的GUI界面
- PDF批量处理功能
- AI数据提取和验证
- Excel导出功能
- 安全API密钥存储

## 许可证

本项目仅供学术研究使用。

## 技术支持

如有问题或建议，请：
1. 查看 `logs/` 目录中的日志文件
2. 参考本文档的故障排除部分
3. 联系开发团队

## 免责声明

本软件按"原样"提供，不提供任何明示或暗示的担保。使用者需自行承担使用风险。

---

**重要提示**：使用本软件需要有效的 DeepSeek API 密钥，相关费用由用户承担。请合理使用API资源，遵守相关服务条款。