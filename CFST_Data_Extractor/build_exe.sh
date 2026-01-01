#!/bin/bash
# CFST Data Extractor 构建脚本
# 用于构建 Windows .exe 可执行文件

set -e  # 遇到错误时退出

echo "========================================"
echo "CFST Data Extractor 构建脚本"
echo "========================================"

# 检查是否在项目根目录
if [ ! -f "main_gui.py" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 清理旧构建
echo "清理旧构建文件..."
rm -rf build/ dist/ __pycache__/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 检查依赖
echo "检查Python依赖..."
if ! command -v python &> /dev/null; then
    echo "错误：未找到Python，请先安装Python 3.8+"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "错误：未找到pip，请先安装pip"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "错误：无法激活虚拟环境"
    exit 1
fi

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查PyInstaller
if ! pip show pyinstaller &> /dev/null; then
    echo "安装PyInstaller..."
    pip install pyinstaller
fi

# 创建必要的目录
echo "创建资源目录..."
mkdir -p resources
mkdir -p spec

# 检查图标文件
if [ ! -f "resources/app.ico" ]; then
    echo "警告：未找到应用程序图标 resources/app.ico"
    echo "将使用默认图标"
    # 这里可以添加生成默认图标的代码
fi

# 构建可执行文件
echo "开始构建可执行文件..."
echo "这可能需要几分钟时间..."

# 使用spec文件构建
if [ -f "spec/cfst_extractor.spec" ]; then
    echo "使用spec文件构建..."
    pyinstaller spec/cfst_extractor.spec --clean
else
    echo "使用命令行参数构建..."
    pyinstaller \
        --name="CFST_Data_Extractor" \
        --windowed \
        --icon=resources/app.ico \
        --add-data="resources/config.ini;resources" \
        --add-data="resources/styles.qss;resources" \
        --add-data="resources/app.ico;resources" \
        --hidden-import=instructor \
        --hidden-import=pydantic \
        --hidden-import=keyring.backends.Windows \
        --hidden-import=cryptography \
        --collect-all=pdfplumber \
        --clean \
        --onefile \
        main_gui.py
fi

# 检查构建结果
if [ -f "dist/CFST_Data_Extractor.exe" ]; then
    echo "构建成功！"
    echo "可执行文件: dist/CFST_Data_Extractor.exe"

    # 显示文件信息
    echo ""
    echo "文件信息:"
    ls -lh "dist/CFST_Data_Extractor.exe"

    # 复制资源文件
    echo "复制资源文件..."
    cp -r resources dist/ 2>/dev/null || true

    # 创建示例目录结构
    echo "创建示例目录结构..."
    mkdir -p "dist/files"
    mkdir -p "dist/NotInput"
    mkdir -p "dist/Excluded"
    mkdir -p "dist/logs"

    echo ""
    echo "目录结构:"
    echo "dist/"
    echo "├── CFST_Data_Extractor.exe"
    echo "├── resources/"
    echo "│   ├── app.ico"
    echo "│   ├── config.ini"
    echo "│   └── styles.qss"
    echo "├── files/          # 放置PDF文件"
    echo "├── NotInput/       # 失败文件"
    echo "├── Excluded/       # 排除文件"
    echo "└── logs/          # 日志文件"

    echo ""
    echo "使用说明:"
    echo "1. 将PDF文件放入 dist/files/ 目录"
    echo "2. 运行 dist/CFST_Data_Extractor.exe"
    echo "3. 输入DeepSeek API密钥"
    echo "4. 点击'开始处理'"

else
    echo "错误：构建失败，未生成可执行文件"
    exit 1
fi

echo ""
echo "========================================"
echo "构建完成！"
echo "========================================"

# 可选：创建ZIP包
read -p "是否创建ZIP分发包？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "创建ZIP分发包..."
    cd dist
    zip -r "../CFST_Data_Extractor_v1.0.zip" .
    cd ..
    echo "ZIP包已创建: CFST_Data_Extractor_v1.0.zip"
fi

# 停用虚拟环境
deactivate

echo ""
echo "提示："
echo "- 在干净的Windows系统上测试可执行文件"
echo "- 确保目标系统已安装必要的运行时库"
echo "- 如有问题，检查logs/目录中的日志文件"