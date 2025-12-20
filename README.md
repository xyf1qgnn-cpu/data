# CFST Data Extractor

这是一个基于 Python 的自动化工具，旨在从学术文献（PDF格式）中提取钢管混凝土（CFST）构件的试验数据。利用 DeepSeek 大模型（OpenAI 兼容接口）进行智能文本分析和数据结构化，并将结果保存为 Excel 文件。

## 功能特性

- **自动批量处理**：扫描 `files` 目录下的所有 PDF 文件。
- **智能数据提取**：使用 AI 识别并提取关键试验参数（如尺寸、材料属性、承载力等）。
- **分类整理**：根据构件截面形状自动分类为 Group A (矩形/方形)、Group B (圆形)、Group C (圆端形)。
- **文件管理**：自动将处理失败或不符合要求的文件移动到相应目录，保持工作区整洁。
- **格式化输出**：生成包含多个 Sheet 的 Excel 报表。

## 目录结构

```
data/
├── main.py                # 主程序脚本
├── files/                 # [输入] 存放待处理 PDF 文件的目录
├── NotInput/              # [输出] 存放处理失败或无法读取的文件
├── Excluded/              # [输出] 存放被 AI 判定为无关或无效的文件
├── CFST_Extracted_Data.xlsx  # [输出] 最终生成的 Excel 数据表
└── README.md              # 说明文档
```

## 安装指南

### 1. 环境要求
- Python 3.8 或更高版本

### 2. 安装依赖
请在终端中运行以下命令安装所需的 Python 库：

```bash
pip install pdfplumber pandas openpyxl openai
```

## 使用说明

### 1. 准备文件
在项目根目录下创建一个名为 `files` 的文件夹（如果不存在），并将需要提取数据的 PDF 论文放入其中。

### 2. 配置 API Key
打开 `main.py`，找到以下代码行，将 `API_KEY` 替换为您自己的 DeepSeek 或兼容 OpenAI 格式的 API Key：

```python
API_KEY = "your-api-key-here"
```

### 3. 运行程序
在终端中切换到项目目录，并运行脚本：

```bash
python main.py
```

### 4. 查看结果
- **成功提取**：数据将保存在 `CFST_Extracted_Data.xlsx` 文件中。
- **无效文件**：不符合 CFST 试验数据要求的论文会被移动到 `Excluded` 文件夹。
- **处理失败**：无法读取或 API 调用失败的文件会被移动到 `NotInput` 文件夹。

## 贡献指南

欢迎提交 Pull Request 或 Issue 来改进本项目！
1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请联系项目维护者或提交 GitHub Issue。
