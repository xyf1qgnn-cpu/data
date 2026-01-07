# 需求文档: PDF缓存处理优化

## 引言

### 概述
当前PDF处理流程直接将提取的图片编码为base64并调用API，缺乏中间缓存机制。本需求旨在通过引入缓存机制，将PDF处理流程拆分为两阶段（图片提取 + API调用），提升处理可靠性并支持失败重试。

### 价值
- **可靠性提升**: API调用失败后可从缓存重试，无需重新提取图片
- **日志优化**: 移除日志中的base64编码，提升日志可读性
- **数据归档**: 自动将提取的图片归档到指定位置，便于后续使用
- **代码简化**: 移除过时的智能筛选功能，降低维护成本

## 需求

### 需求1: 优化日志输出

**用户故事**: 作为运维人员，我希望日志不包含base64编码内容，以便快速定位问题

#### 验收标准

1. WHEN 调用 `call_vision_api` 记录payload日志 THEN 日志应显示图片数量而非实际base64内容
2. WHEN 记录API响应日志 AND 响应内容超过1000字符 THEN 日志应只显示前500字符+"..."
3. WHEN 响应内容少于1000字符 THEN 日志应显示完整内容
4. WHEN 记录payload日志 THEN 日志应包含模型名称、图片数量、max_token参数

### 需求2: 支持两阶段PDF处理模式

**用户故事**: 作为开发者，我希望能将PDF处理分离为图片提取和API调用两个阶段，以便实现失败重试

#### 验收标准

1. WHEN `process_pdf` 以 mode="full" 调用 THEN 函数应完整处理PDF（保持向后兼容）
2. WHEN `process_pdf` 以 mode="extract_only" 调用 THEN 函数应返回cache目录和图片列表
3. WHEN `process_pdf` 解析PDF时 AND PDF页数大于1 THEN 应处理除最后一页外的所有页面
4. WHEN `process_pdf` 以 mode="extract_only" 调用完成 THEN 图片应保存到 `./cache/{pdf_name}/` 目录
5. WHEN 图片保存到cache时 THEN应保存为JPEG格式，质量设置为95

### 需求3: 实现缓存处理函数

**用户故事**: 作为开发者，我希望能够从缓存中读取图片并调用API，以便在API失败时重试

#### 验收标准

1. GIVEN cache目录和图片路径列表 WHEN调用`process_from_cache` THEN 函数应返回API调用结果
2. WHEN `process_from_cache`处理图片时 THEN 应使用JPEG格式进行base64编码
3. WHEN `process_from_cache`调用API时 THEN 应重用现有的`encode_images_to_base64`和`call_vision_api`函数
4. WHEN `process_from_cache`执行过程中发生错误 THEN 应记录错误日志并返回None

### 需求4: 实现缓存归档功能

**用户故事**: 作为数据管理员，我希望自动归档提取的图片到指定位置，以便后续分析和备份

#### 验收标准

1. WHEN `archive_cache`被调用 THEN 应将cache目录压缩为zip文件
2. WHEN 创建归档时 THEN 文件名应为`{pdf_name}_images.zip`
3. WHEN 归档完成后路径应位于 `/mnt/e/Documents/data_extracted/Dataset ({batch_number}) {YYYY-MM-DD}/`
4. WHEN 归档成功 THEN 应删除原始cache目录以释放空间
5. WHEN 归档失败 THEN 应保留cache目录并记录错误日志

### 需求5: 更新主流程调用逻辑

**用户故事**: 作为用户，我希望PDF处理流程自动执行两阶段处理并归档，无需手动干预

#### 验收标准

1. WHEN 处理每个PDF时 THEN 应首先调用`process_pdf`的extract_only模式提取图片
2. WHEN 图片提取成功 THEN 应调用`process_from_cache`进行API处理
3. WHEN API处理成功 THEN 应调用`archive_cache`归档cache
4. WHEN 批次处理结束时 THEN 批次号应在state.json中正确递增
5. WHEN 任何阶段失败 THEN 应将PDF移动到NotInput目录并记录失败原因

### 需求6: 支持独立执行第二阶段

**用户故事**: 作为用户，我希望可以只执行第二阶段（从cache调用API），以便在API失败后重试而不重新提取图片

#### 验收标准

1. WHEN 运行程序时指定 `--mode process_from_cache` 参数 THEN 应跳过图片提取阶段
2. WHEN 使用 `-cache_dir` 参数指定cache目录 THEN 程序应读取该目录下的所有图片文件
3. WHEN 第二阶段独立执行时 THEN 应按指定PDF名称归档到正确的批次目录
4. WHEN 第二次从同一个cache执行时 THEN 不应重新创建zip归档（如已存在则跳过）
5. WHEN 从cache处理成功 THEN 应在state.json中记录该PDF的批次信息

### 需求7: 完善错误处理和批次管理

**用户故事**: 作为运维人员，我希望在失败时能清楚知道原因，并确保批次号管理正确

#### 验收标准

1. WHEN `process_pdf` 失败 THEN 应记录详细错误日志包括文件名和错误原因
2. WHEN API调用失败时 THEN 应能在不重提图片的情况下使用相同cache重试
3. WHEN 批次号递增时 THEN 应在每个PDF成功处理后更新state.json
4. WHEN 更新state.json时 THEN 应记录处理的PDF信息和批次号
5. WHEN 归档失败时 THEN 应保留cache目录不影响后续处理

### 需求8: 支持页数限制配置（性能优化）

**用户故事**: 作为用户，我希望可以设置最大处理页数，避免处理过长PDF导致超时

#### 验收标准

1. WHEN PDF页数超过配置的 `max_pages` THEN 只处理前 `max_pages` 页
2. WHEN `config.json` 中包含 `max_pages` 配置时 THEN `process_pdf` 应遵守该限制
3. WHEN `max_pages` 未配置 THEN 默认使用最大25页（与原系统8页相比，允许处理更长PDF）
4. WHEN 页数被限制时 THEN 日志应明确提示"处理前N页，共M页"
5. WHEN PDF页数超过25页 THEN 应在日志中发出警告，提示处理时间可能较长

### 需求9: 完善返回值设计

**用户故事**: 作为开发者，我希望函数返回值格式统一，便于调用端处理

#### 验收标准

1. WHEN `process_pdf` 以 mode="extract_only" 返回 THEN 应返回 `{"cache_dir": str, "image_paths": List[str]}`
2. WHEN `process_pdf` 以 mode="full" 返回 THEN 应返回 `{"result": Dict, "cache_dir": str}`
3. WHEN 返回字典时 THEN 所有字段都应存在且类型正确
4. WHEN 处理失败时 THEN 应返回None而非抛出异常

### 需求10: 清理过时代码

**用户故事**: 作为代码维护者，我希望移除不再使用的代码，降低维护负担

#### 验收标准

1. WHEN 部署完成后 THEN 应删除 `get_smart_pages_to_process` 函数
2. WHEN 部署完成后 THEN 应删除 `config.json` 中的页面筛选相关配置
3. WHEN 删除旧代码后 THEN 系统应仍能正常运行所有现有功能
4. WHEN 代码清理完成 THEN 应验证所有引用都已更新

### 需求11: 更新配置文件

**用户故事**: 作为系统管理员，我希望配置文件中只包含有效的配置项

#### 验收标准

1. WHEN `config.json` 更新后 THEN 应包含 `processing_settings` 配置块
2. WHEN `config.json` 包含 `paths` 配置 THEN 应正确定义 `archive_destination`
3. WHEN `config.json` 完成更新后 THEN 应删除所有 `page_filtering` 相关配置
4. WHEN 配置更新后 THEN 应用应能正确读取并使用新配置

## 非功能性需求

### 代码架构与模块化

- **单一职责原则**: 每个函数应有清晰定义的功能，如`process_pdf`负责图片提取，`process_from_cache`负责API调用
- **模块化设计**: 缓存处理逻辑应与PDF处理逻辑分离，便于独立测试
- **最小化依赖**: 新功能应重用现有工具函数，避免新增依赖
- **清晰接口**: 修改后`process_pdf`的mode参数应有明确的行为定义

### 性能要求

- WHEN 处理单页PDF时 THEN 缓存创建时间应小于500ms
- WHEN 处理8页PDF时 THEN 图片编码和保存时间应小于2秒
- WHEN zip归档大小在100MB内时 THEN 归档操作时间应小于10秒
- WHEN API调用失败时 THEN 从cache重试的时间应仅为API调用时间，不含图片提取时间

### 可靠性要求

- WHEN cache目录已存在 THEN `os.makedirs(cache_dir, exist_ok=True)`不应抛出异常
- WHEN 磁盘空间不足时 THEN 应在提取图片前检查并抛出有意义的错误提示
- WHEN zip文件已存在时 THEN `archive_cache` 应覆盖旧文件或创建备份
- WHEN 清理cache失败时 THEN 不应影响主流程的继续执行

### 可维护性要求

- WHEN 查看日志时 THEN 应能清晰识别处理的PDF名称、页数和阶段
- WHEN 查看归档目录时 THEN 应能通过批次号和日期快速定位数据
- WHEN 查看配置文件时 THEN 配置项应有清晰的命名和说明
- WHEN 代码出现错误时 THEN 错误信息应包含足够的上下文帮助诊断问题

### 安全性要求

- WHEN 保存图片到cache时 THEN 应不能使用可执行文件名
- WHEN 执行 `shutil.rmtree` 时 THEN 目标路径应限定在cache目录内
- WHEN 读取cache中的图片时 THEN 应验证文件确实是图片格式

### 可测试性要求

- WHEN 测试 `process_from_cache` 时 THEN 应能使用模拟的cache目录和image_paths
- WHEN 测试 `archive_cache` 时 THEN 应能指定临时的归档目标路径
- WHEN 测试失败场景时 THEN 函数应提供清晰的错误信息而非抛出未捕获异常

## 后续优化考虑

### 未来可能的需求

1. **增量处理**: 只处理未处理的页面
2. **并行批处理**: 同时从多个cache调用API
3. **Cache清理策略**: 基于时间或空间的自动清理
4. **处理进度恢复**: 从中断处继续处理
5. **图片格式选项**: 支持PNG、WebP等格式

## 参考资料

- 实施计划核心版: `/home/thelya/Work/data/实施计划_核心版.md`
- 审查结果: `/home/thelya/Work/data/实施计划_核心版_Review结果.md`
- 实现原则: 最小化新增代码，最大化复用现有函数
