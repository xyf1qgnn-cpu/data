# PDF缓存处理集成测试指南

## 环境准备

### 安装依赖
```bash
pip install -r requirements.txt
# 或手动安装:
pip install pytest pillow numpy
```

### 确保Poppler已安装
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# 下载poppler并添加到PATH
```

## 测试准备

### 测试文件
准备3-5个不同大小的PDF文件（1-30页）用于测试：
- small.pdf (1-5页)
- medium.pdf (6-15页)
- large.pdf (16-30页)

### 配置检查
确保 `config.json` 配置正确：
```json
{
  "api_settings": {
    "api_key": "your_api_key",
    "base_url": "https://api.ohmygpt.com/v1",
    "model_name": "vertex-gemini-3-flash-preview"
  },
  "processing_settings": {
    "image_dpi": 150,
    "max_pages": 25
  },
  "paths": {
    "archive_destination": "/mnt/e/Documents/data_extracted"
  }
}
```

## 单元测试

运行单元测试：
```bash
python3 -m pytest test_pdf_cache.py -v
```

测试报告应显示：
- ✅ 所有测试通过（8个测试用例）
- ✅ 代码覆盖率 >80%

## 集成测试

### 测试1: 端到端完整流程

**目标**: 验证三阶段处理流程正常工作

**步骤**:
1. 准备3个测试PDF文件放入 `files/` 目录
2. 运行处理：
   ```bash
   python3 main.py
   ```
3. 观察输出：
   - 阶段1: 提取图片（显示"提取了X张图片"）
   - 阶段2: 调用API（显示"API调用成功"）
   - 阶段3: 归档cache（显示"归档到..."）

**预期结果**:
- ✅ 所有PDF成功处理
- ✅ `./cache/` 目录被创建并包含图片
- ✅ cache归档成功（zip文件创建）
- ✅ state.json批次号正确递增

**验证检查list**:
- [ ] 没有base64编码出现在日志中
- [ ] 响应长度日志显示正确
- [ ] 每个PDF都有对应的cache目录
- [ ] 归档目录 `Dataset (N) YYYY-MM-DD/` 存在
- [ ] Excel文件数据正确

### 测试2: 失败重试场景

**目标**: 验证API失败后可以从cache重试

**步骤**:
1. 使用 `max_pages=1` 配置快速测试
2. 临时修改API key为无效值：
   ```json
   "api_key": "invalid_key"
   ```
3. 运行处理（预计会失败）：
   ```bash
   python3 main.py
   ```
4. 验证cache保留（未删除）
5. 恢复正确的API key
6. 从cache重试：
   ```bash
   python3 main.py --mode process_from_cache --cache-dir ./cache/paper_name --pdf-name paper_name
   ```

**预期结果**:
- ✅ 第一次处理失败，但cache保留
- ✅ 第二次从cache处理成功
- ✅ 无需重新提取图片

**性能验证**:
- 重试时间应比完整处理快50%以上

### 测试3: 性能对比测试

**目标**: 验证第二阶段比完整处理快50%以上

**步骤**:
1. 准备15-20页的PDF
2. 计时完整处理：
   ```bash
   time python3 main.py --mode full
   ```
3. 清理（删除cache和归档）
4. 计时仅提取：
   ```bash
   time python3 main.py --mode extract_only
   ```
5. 计时第二阶段：
   ```bash
   time python3 main.py --mode process_from_cache --cache-dir ./cache/paper --pdf-name paper
   ```

**计算公式**:
- 提取时间 = 仅提取时间
- API调用时间 = 完整处理时间 - 仅提取时间
- 第二阶段时间 = 从cache处理时间

**预期结果**:
- ✅ 第二阶段时间 ≈ API调用时间（只调用API，不提取图片）
- ✅ 第二阶段比完整处理快50%以上

### 测试4: 日志大小对比

**目标**: 验证日志文件大小减少90%以上

**步骤**:
1. 处理5个PDF文件
2. 检查日志文件大小：
   ```bash
   ls -lh logs/
   ```
3. 查看日志内容：
   ```bash
   grep "base64" logs/Batch-*.log
   ```
   应该没有任何base64内容
4. 查看响应日志：
   ```bash
   grep "API响应长度" logs/Batch-*.log
   ```
   长度应显示正确，超过1000字符的应有预览

**预期结果**:
- ✅ 日志文件比优化前小90%以上
- ✅ 没有base64编码内容
- ✅ 响应预览正确显示

### 测试5: 批量处理

**目标**: 验证批量处理稳定运行

**步骤**:
1. 准备10个PDF文件（5-25页不等）
2. 运行批量处理：
   ```bash
   python3 main.py
   ```
3. 监控系统资源：
   ```bash
   # 在另一个终端
   watch -n 1 'free -h'
   # 或
   htop
   ```
4. 处理完成后检查：
   - 批次号更新
   - 所有cache归档成功
   - 无内存泄漏

**预期结果**:
- ✅ 所有10个PDF成功处理
- ✅ 批次号正确递增（如从1到2）
- ✅ 内存使用稳定，无持续增长
- ✅ 所有cache被归档，无残留

### 测试6: 边界情况

#### 6.1 单页PDF
```bash
cp single_page.pdf files/
python3 main.py
```
- ✅ 正确处理单页PDF
- ✅ 不报错

#### 6.2 30页PDF（超过max_pages=25）
```bash
cp large_30pages.pdf files/
python3 main.py
```
- ✅ 只处理前25页
- ✅ 日志显示警告信息

#### 6.3 PDF无数据
使用不含CFST数据的PDF：
```bash
cp no_data.pdf files/
python3 main.py
```
- ✅ 正确识别无数据
- ✅ 移动到 Manual_Review

#### 6.4 损坏的PDF
```bash
echo "not a pdf" > files/corrupted.pdf
python3 main.py
```
- ✅ 处理失败但程序不崩溃
- ✅ 移动到 NotInput

## 性能基准

记录典型性能数据：

| PDF页数 | 完整处理时间 | 仅提取时间 | API调用时间 | 第二阶段时间 |
|---------|--------------|------------|-------------|--------------|
| 5页     | ~30s         | ~5s        | ~25s        | ~25s         |
| 15页    | ~90s         | ~15s       | ~75s        | ~75s         |
| 25页    | ~150s        | ~25s       | ~125s       | ~125s        |

预期性能提升：
- 第二次处理（从cache）比第一次快83%（仅提取阶段的时间被节省）

## 日志验证

检查日志质量：

1. **检查base64编码**：
   ```bash
   grep -c "base64" logs/Batch-*.log || echo "✅ No base64 found"
   ```
   应该输出 "✅ No base64 found" 或显示0

2. **检查响应长度**：
   ```bash
   grep "API响应长度" logs/Batch-*.log | head -5
   ```
   应该显示长度信息，不是完整响应

3. **检查响应预览**：
   ```bash
   grep "响应预览" logs/Batch-*.log | head -3
   ```
   长响应应该显示预览而不是完整内容

4. **检查日志大小**：
   ```bash
   du -sh logs/
   ```
   应该比优化前小90%以上

## 部署验证

### 预部署检查
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 日志优化有效
- [ ] 性能提升达标
- [ ] config.json配置正确

### 部署步骤
1. 备份现有代码：
   ```bash
   cp main.py main.py.backup
   cp processing.py processing.py.backup
   cp config.json config.json.backup
   ```

2. 更新代码（已完成）

3. 运行小批量测试（3-5个PDF）

4. 验证结果正确

5. 完整部署

### 回滚方案
如果出现问题：
```bash
cp main.py.backup main.py
cp processing.py.backup processing.py
cp config.json.backup config.json
```

## 已知问题及解决

### 问题1: 单元测试依赖缺失
**解决**: 安装pytest
```bash
pip install pytest
```

### 问题2: 归档路径不存在
**解决**: 创建目录
```bash
mkdir -p /mnt/e/Documents/data_extracted
```

### 问题3: API调用失败
**解决**: 检查API密钥和网络连接
```bash
# 测试API连通性
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.ohmygpt.com/v1/models
```

## 待办事项

- [ ] 完成单元测试运行
- [ ] 完成集成测试运行
- [ ] 记录性能基准数据
- [ ] 更新README文档
- [ ] 清理过时函数（可选）
