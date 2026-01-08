# CFST数据提取器 - 轮询模式与并行处理使用指南

## 概述

本指南介绍CFST数据提取器的新功能：轮询模式、并行处理和自动清理。

## 新功能特点

### 1. 轮询模式 (Polling Mode)
自动扫描并处理指定目录下的所有子文件夹，无需手动干预。

### 2. 并行处理 (Parallel Processing)
同时处理多个PDF文件，大幅提升处理速度（理论提升7-8倍）。

### 3. 自动清理 (Auto Cleanup)
每个子文件夹处理完成后，自动删除Excel文件并移动源码到归档位置。

## 快速开始

### 配置启用新功能

编辑 `config.json` 文件：

```json
{
  "windows_source_path": "/mnt/e/Documents/data_unextracted",
  "archive_destination": "/mnt/e/Documents/data_extracted",
  "auto_cleanup": true,
  "auto_increment": true,
  "delete_existing_before_import": true,
  "cleanup_after_archive": true,

  "polling_mode": true,                    // 启用轮询模式
  "polling_source_path": "/mnt/e/Documents/data_unextracted",
  "processed_dirs_location": "/mnt/e/Documents/processed_directories",
  "parallel_processing": true,             // 启用并行处理
  "max_concurrent_files": 10,              // 最大并发文件数
  "delete_excel_after_archive": true,      // 处理后删除Excel
  "move_source_after_processing": true     // 处理后移动源码
}
```

### 目录结构要求

启用轮询模式前，确保目录结构如下：

```
/mnt/e/Documents/data_unextracted/
├── database1/           # 子文件夹1
│   ├── paper1.pdf
│   ├── paper2.pdf
│   └── ...
├── database2/           # 子文件夹2
│   ├── paper3.pdf
│   └── ...
└── database3/           # 子文件夹3
    └── ...
```

处理完成后：
- Excel文件生成在脚本目录（临时）
- 处理完成后自动删除Excel
- 源码移动到 `/mnt/e/Documents/processed_directories/`

## 使用模式

### 模式1：轮询 + 并行（推荐）

**配置：**
```json
{
  "polling_mode": true,
  "parallel_processing": true,
  "max_concurrent_files": 10
}
```

**特点：**
- 自动扫描所有子目录
- 同时处理多个PDF文件
- 最高性能，适合大量PDF

**运行：**
```bash
python3 main.py
```

### 模式2：轮询 + 顺序

**配置：**
```json
{
  "polling_mode": true,
  "parallel_processing": false
}
```

**特点：**
- 自动扫描所有子目录
- 逐个处理PDF文件
- 更稳定，适合API不稳定的情况

### 模式3：传统模式（向后兼容）

**配置：**
```json
{
  "polling_mode": false,
  "auto_cleanup": true
}
```

**特点：**
- 保持原有行为不变
- 从 `windows_source_path` 导入PDF
- 处理 `files/` 目录中的PDF

## 配置详解

### 核心配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `polling_mode` | boolean | false | 启用轮询模式 |
| `polling_source_path` | string | "/mnt/e/Documents/data_unextracted" | 待处理的根目录 |
| `processed_dirs_location` | string | "/mnt/e/Documents/processed_directories" | 已处理目录存放位置 |
| `parallel_processing` | boolean | false | 启用并行处理 |
| `max_concurrent_files` | integer | 10 | 最大并发文件数 |
| `delete_excel_after_archive` | boolean | true | 处理后删除Excel |
| `move_source_after_processing` | boolean | true | 处理后移动源码 |

### 性能调优建议

#### 并行处理并发数
- **10** (默认)：保守设置，适合大多数情况
- **15-20**：如果API响应快，可提升并发
- **5**：如果API不稳定或网络延迟高

调整方法：
```json
"max_concurrent_files": 15
```

#### 处理大量文件
- 启用 `polling_mode` 自动处理所有目录
- 设置合适的 `max_concurrent_files` (10-15)
- 确保 `processed_dirs_location` 有足够磁盘空间

## 状态追踪

### state.json 结构

```json
{
  "batch_number": 8,
  "last_archive_date": "2026-01-07",
  "total_archives": 3,
  "last_import_date": "2026-01-07",
  "polling_processed_dirs": [           // 新：已处理的目录
    "/mnt/e/Documents/data_unextracted/database1",
    "/mnt/e/Documents/data_unextracted/database2"
  ],
  "current_processing_dir": null,      // 新：当前处理的目录
  "last_polling_check": "2026-01-07T14:30:00"  // 新：最后检查时间
}
```

### 断点续传

如果程序中断，重新运行时会：
1. 读取 `state.json` 中的已处理目录列表
2. 跳过已处理的目录
3. 继续处理未完成的目录

## 监控和日志

### 控制台输出

```
============================================================
POLLING MODE ENABLED
============================================================

Found 3 directories to process:
  1. database1 (5 PDFs)
  2. database2 (8 PDFs)
  3. database3 (3 PDFs)

============================================================
Processing [1/3]: database1
============================================================
Mode: parallel
Max concurrent files: 10

...
✅ Completed database1

============================================================
Processing [2/3]: database2
============================================================
...
```

### 处理统计

每个目录处理完成后显示：
- 成功处理的文件数
- 排除的文件数（不符合要求）
- 失败的文件数（API错误）
- 提取的试件总数

## 故障排除

### 问题1：ModuleNotFoundError

**错误：**
```
ModuleNotFoundError: No module named 'pdfplumber'
```

**解决：**
```bash
pip3 install -r requirements/requirements.txt
```

### 问题2：API调用失败

**现象：**
- 大量PDF处理失败
- 报错：Connection timeout 或 API error

**解决：**
1. 降低并发数：
   ```json
   "max_concurrent_files": 5
   ```

2. 切换到顺序处理：
   ```json
   "parallel_processing": false
   ```

### 问题3：内存不足

**现象：**
- 程序崩溃或系统变慢
- 处理大PDF文件时出现问题

**解决：**
1. 降低并发数：
   ```json
   "max_concurrent_files": 3
   ```

2. 分批处理，手动移动已处理的目录

### 问题4：state.json损坏

**现象：**
- 报错：JSON decode error
- 程序无法读取状态

**解决：**
1. 备份现有的 state.json：
   ```bash
   cp state.json state.json.backup
   ```

2. 删除或重置 state.json：
   ```bash
   rm state.json
   ```

3. 重新运行程序（会创建新的 state.json）

## 性能对比

### 测试场景：10个PDF文件

| 模式 | 并发数 | 预计时间 | 性能提升 |
|------|--------|----------|----------|
| 传统顺序 | 1 | ~150秒 | 1x |
| 轮询顺序 | 1 | ~150秒 | 1x |
| 轮询并行 | 5 | ~35秒 | 4.3x |
| 轮询并行 | 10 | ~20秒 | 7.5x |

*注：实际时间取决于API响应速度和PDF文件大小*

## 最佳实践

### ✅ 推荐配置

**标准模式：**
```json
{
  "polling_mode": true,
  "parallel_processing": true,
  "max_concurrent_files": 10,
  "delete_excel_after_archive": true,
  "move_source_after_processing": true
}
```

**保守模式（API不稳定时）：**
```json
{
  "polling_mode": true,
  "parallel_processing": false,
  "delete_excel_after_archive": true,
  "move_source_after_processing": true
}
```

### ❌ 不推荐

1. **极高的并发数** (>20)
   - 可能导致API限制或服务器拒绝

2. **禁用清理功能** 长期运行
   - 会积累大量临时文件

3. **手动修改 state.json**
   - 可能导致状态不一致

## 迁移指南

### 从旧版本升级

1. **备份现有数据：**
   ```bash
   cp config.json config.json.backup
   cp state.json state.json.backup
   ```

2. **代码会自动扩展配置和状态文件**
   - 首次运行时添加新参数
   - 保持向后兼容

3. **测试新功能：**
   ```bash
   # 先测试传统模式
   python3 main.py

   # 然后启用轮询模式测试
   # 编辑 config.json 设置 "polling_mode": true
   python3 main.py
   ```

### 回滚到旧版本

如果需要回滚：

1. **恢复备份文件：**
   ```bash
   cp config.json.backup config.json
   cp state.json.backup state.json
   ```

2. **使用旧版代码**（如果有Git，可以checkout到之前的commit）

## 总结

新功能提供三种使用模式：

1. **全自动模式**：轮询 + 并行（最高效率）
2. **稳定模式**：轮询 + 顺序（更可靠）
3. **传统模式**：保持原有行为（向后兼容）

根据您的需求选择合适的配置，享受更高效的数据提取体验！

## 技术支持

如有问题，请检查：
1. `config.json` 配置是否正确
2. `state.json` 状态是否正常
3. 查看控制台输出的错误信息
4. 检查 `files/`, `NotInput/`, `Excluded/` 目录中的文件
