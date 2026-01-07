# 任务列表: PDF缓存处理优化

## 任务分解

### Phase 1: 核心函数改造与新增

- [ ] 1.1. 优化 call_vision_api 日志输出
  - **文件**: `/home/thelya/Work/data/processing.py`
  - **修改点**:
    - 第963行：修改 payload 日志，显示图片数量而非base64内容
    - 第975行：修改响应日志，超过1000字符时只显示前500字符+"..."
  - **目的**: 提升日志可读性，减少日志文件大小
  - **_Leverage**: 现有日志框架和logger实例
  - **_Requirements**: 需求1
  - **_Prompt**: |
      Role: Python Developer with expertise in logging and debugging

      Task: Optimize logging in call_vision_api function to improve readability and reduce log size.

      Specific changes:
      1. Around line 963: Replace payload logging with a summary showing image count, model name, and max_tokens
      2. Around line 975: Truncate response content logging - if content exceeds 1000 characters, only log first 500 characters with ellipsis

      Restrictions:
      - Do not remove any existing error logging
      - Maintain logging levels (debug for detailed info)
      - Ensure all critical information is still logged
      - No changes to function signature or core logic

      Success criteria:
      - Logs no longer contain base64 encoded strings
      - Response previews work correctly for long responses
      - All existing error handling and logging remains intact
      - Log file size is significantly reduced for PDF processing

- [ ] 1.2. 改造 process_pdf 函数支持双模式
  - **文件**: `/home/thelya/Work/data/processing.py`
  - **修改点**:
    - 添加 mode 参数 (默认 "full" 保持向后兼容)
    - 重构内部逻辑为两阶段：图片提取 → API调用
    - 添加cache保存逻辑（保存到 ./cache/{pdf_name}/）
    - 统一返回字典格式（不再是元组）
    - 添加页数限制支持（max_pages 配置）
  - **目的**: 支持两阶段处理，创建cache机制
  - **_Leverage**: encode_images_to_base64, build_vision_payload, call_vision_api, convert_pdf_to_images, get_page_count
  - **_Requirements**: 需求2, 需求7, 需求8
  - **_Prompt**: |
      Role: Python Developer with expertise in PDF processing and function refactoring

      Task: Refactor process_pdf function to support dual-mode operation with cache functionality.

      Key changes needed:
      1. Add mode parameter with default "full" for backward compatibility
      2. Extract image extraction logic into first phase
      3. Save extracted images to ./cache/{pdf_name}/ directory as JPEG (quality=95)
      4. Implement API call as second phase (when mode="full")
      5. Change return type to dictionary:
         - mode="extract_only": {"cache_dir": str, "image_paths": List[str]}
         - mode="full": {"result": Dict, "cache_dir": str}
      6. Add max_pages support: check config for max_pages (default 25), limit pages if exceeded
      7. Handle page selection: process pages 1 to (page_count-1) for multi-page PDFs, or 1 for single-page
      8. Return None on failure (don't raise exceptions)

      Restrictions:
      - Maintain backward compatibility (default mode="full")
      - Do not duplicate existing logic - reuse encode_images_to_base64 and other helper functions
      - Ensure proper error handling and logging
      - Create cache directory if it doesn't exist (os.makedirs with exist_ok=True)
      - Follow existing code style and patterns

      Success criteria:
      - mode="extract_only" returns cache info without calling API
      - mode="full" performs complete processing like original function
      - Images are correctly saved to cache directory
      - Return format is unified as dictionary
      - max_pages configuration is respected
      - Existing functionality remains unchanged for mode="full"

- [ ] 1.3. 新增 process_from_cache 函数
  - **文件**: `/home/thelya/Work/data/processing.py`
  - **新增位置**: 在 process_pdf 函数之后
  - **功能**: 从cache读取图片并调用API处理
  - **目的**: 实现第二阶段处理，支持失败重试
  - **_Leverage**: Image.open, encode_images_to_base64, build_vision_payload, call_vision_api
  - **_Requirements**: 需求3, 需求6
  - **_Prompt**: |
      Role: Python Developer with expertise in image processing and API integration

      Task: Implement process_from_cache function for second-phase processing.

      Function signature:
      def process_from_cache(
          cache_dir: str,
          pdf_name: str,
          image_paths: List[str],
          client,
          config: Dict[str, Any],
          system_prompt: str
      ) -> Optional[Dict[str, Any]]:

      Implementation requirements:
      1. Log cache processing info: cache directory name and image count
      2. Read images from provided image_paths using Image.open()
      3. Reuse encode_images_to_base64 to encode images (JPEG format)
      4. Reuse build_vision_payload to construct API request
      5. Reuse call_vision_api to call the vision API
      6. Return API result on success, None on failure
      7. Handle errors gracefully with proper logging

      Restrictions:
      - Do not modify cache directory or image files (read-only operation)
      - Reuse existing functions - do not duplicate encoding/payload logic
      - Add proper error handling for file reading failures
      - Follow existing error logging patterns
      - Include cache_dir in logs for traceability

      Success criteria:
      - Function successfully reads images from cache
      - API is called with correct payload
      - Result is properly returned
      - Errors are logged with clear context
      - Cache directory remains unchanged after processing

- [ ] 1.4. 新增 archive_cache 函数
  - **文件**: `/home/thelya/Work/data/main.py` （或 processing.py，建议放main.py）
  - **功能**: 将cache目录压缩并归档到指定位置
  - **目的**: 自动归档提取的图片，便于备份和后续使用
  - **_Leverage**: shutil.make_archive, shutil.rmtree, datetime
  - **_Requirements**: 需求4
  - **_Prompt**: |
      Role: Python Developer with expertise in file operations and archiving

      Task: Implement archive_cache function to zip and archive cache directories.

      Function signature:
      def archive_cache(
          cache_dir: str,
          pdf_name: str,
          batch_number: int,
          archive_base: str
      ) -> Optional[str]:

      Implementation requirements:
      1. Generate timestamp: datetime.now().strftime("%Y-%m-%d")
      2. Create archive directory: f"{archive_base}/Dataset ({batch_number}) {date_str}/"
      3. Create zip file: f"{archive_dir}/{pdf_name}_images.zip"
      4. Use shutil.make_archive to create zip (format='zip')
      5. On success: delete cache directory with shutil.rmtree
      6. On failure: catch exception, log error, keep cache directory, return None
      7. Return path to created zip file on success

      Restrictions:
      - Ensure archive_base directory exists (create with os.makedirs if needed)
      - Handle exceptions for zip creation and directory deletion
      - Validate that cache_dir is within expected location (security)
      - Do not archive if zip already exists (skip or overwrite based on design)
      - Follow existing logging patterns

      Success criteria:
      - Zip file is correctly created with all cache contents
      - Cache directory is deleted after successful archiving
      - Archive path follows format: Dataset ({batch}) YYYY-MM-DD/{name}_images.zip
      - Errors are properly caught and logged
      - Function returns correct path or None
      - Source directory is validated for security

### Phase 2: 主流程更新与错误处理

- [ ] 2.1. 更新 main.py 主流程调用逻辑
  - **文件**: `/home/thelya/Work/data/main.py`
  - **修改点**: 在处理循环中调用三阶段流程
  - **目的**: 实现完整的三阶段处理（提取→API→归档）
  - **_Leverage**: process_pdf, process_from_cache, archive_cache, state.json管理
  - **_Requirements**: 需求5, 需求7
  - **_Prompt**: |
      Role: Python Developer with expertise in workflow orchestration and error handling

      Task: Update main.py PDF processing loop to implement three-stage processing workflow.

      Changes needed in the PDF processing loop:
      1. Stage 1: Call process_pdf with mode="extract_only" to extract images
      2. Check if cache_result is not None
      3. Extract pdf_name from file_path using os.path.basename and os.path.splitext
      4. Stage 2: Call process_from_cache with extracted cache_dir, pdf_name, and image_paths
      5. Check if API result is not None
      6. Stage 3: Call archive_cache with cache_dir, pdf_name, batch_number, and archive_destination from config
      7. Update state.json after successful processing
      8. Add comprehensive error handling for each stage
      9. Move PDF to NotInput on permanent failures
      10. Log each stage progress with clear messages

      Restrictions:
      - Maintain existing batch processing logic
      - Do not break existing error handling patterns
      - Ensure proper cleanup on failures
      - Update state.json only on successful completion
      - Follow existing logging format and levels
      - Handle None returns from all three functions

      Success criteria:
      - Three-stage workflow is correctly implemented
      - Errors at each stage are properly handled
      - PDFs are moved to NotInput only on unrecoverable failures
      - Cache is preserved when API fails (for retry)
      - Progress is clearly logged at each stage
      - State.json is updated correctly

- [ ] 2.2. 添加命令行参数支持独立执行第二阶段
  - **文件**: `/home/thelya/Work/data/main.py`
  - **新增**: argparse 参数解析
  - **目的**: 支持 --mode, --cache_dir, --pdf_name 参数
  - **_Leverage**: argparse, sys.argv
  - **_Requirements**: 需求6
  - **_Prompt**: |
      Role: Python Developer with expertise in CLI interfaces and command-line parsing

      Task: Add command-line argument support for independent second-stage processing.

      Add argparse configuration for:
      1. --mode: choices=['full', 'extract_only', 'process_from_cache'], default='full'
      2. --cache_dir: required when mode='process_from_cache'
      3. --pdf_name: required when mode='process_from_cache'

      Implementation requirements:
      1. Set up argument parser at the beginning of main()
      2. Parse arguments and store in variables
      3. When mode='process_from_cache':
         - Validate cache_dir exists
         - Scan directory for .jpg files (sorted)
         - Skip stage 1 (image extraction)
         - Call process_from_cache directly
         - Check if already archived before archiving
      4. When mode='extract_only':
         - Call process_pdf with mode='extract_only' for all PDFs
         - Skip API processing
         - Do not archive
      5. Maintain default behavior (mode='full')

      Restrictions:
      - Add validation: cache_dir must exist and contain jpg files
      - Add validation: pdf_name must be valid filename
      - Do not break existing default behavior
      - Provide clear help messages for each argument
      - Follow existing code structure and imports

      Success criteria:
      - All three modes work correctly
      - Validation errors show clear messages
      - Default mode maintains backward compatibility
      - process_from_cache mode reads cache correctly
      - extract_only mode skips API calls
      - All arguments have proper help text

### Phase 3: 配置管理与清理

- [ ] 3.1. 更新 config.json 配置
  - **文件**: `/home/thelya/Work/data/config.json`
  - **修改点**:
    - 删除 page_filtering 配置块
    - 添加 max_pages 配置
    - 确认 archive_destination 路径
  - **目的**: 清理过时配置，添加新配置项
  - **_Leverage**: 现有config.json结构
  - **_Requirements**: 需求11
  - **_Prompt**: |
      Role: Configuration Manager with expertise in JSON configuration files

      Task: Update config.json to remove obsolete configurations and add new settings.

      Changes required:
      1. Remove entire "page_filtering" configuration block (lines 13-56)
      2. Add "max_pages" to "processing_settings" (default: 25)
      3. Verify "archive_destination" path in "paths" section exists and is correct:
         - Current: "/mnt/e/Documents/data_extracted"
      4. Verify "processing_settings" contains:
         - short_paper_threshold
         - max_scan_limit
         - image_dpi
         - enable_smart_filtering (can be removed or kept for backward compatibility)
         - absolute_max_pages (can be removed or repurposed)

      Restrictions:
      - Maintain valid JSON syntax
      - Do not remove other unrelated configurations
      - Keep existing structure and formatting
      - Ensure all paths are absolute and correct
      - Backup config.json before modification

      Success criteria:
      - config.json is valid JSON (no syntax errors)
      - page_filtering block is completely removed
      - max_pages is added with correct default value
      - All existing required configurations are preserved
      - File passes JSON validation

- [ ] 3.2. 删除过时函数和代码
  - **文件**: `/home/thelya/Work/data/processing.py`
  - **删除内容**:
    - get_smart_pages_to_process 函数
    - 所有页面筛选相关的代码
  - **目的**: 清理不再使用的代码
  - **_Leverage**: git history (for reference if needed)
  - **_Requirements**: 需求10
  - **_Prompt**: |
      Role: Code Maintenance Engineer with expertise in code cleanup and refactoring

      Task: Remove obsolete functions and code related to smart page filtering.

      Code to remove:
      1. get_smart_pages_to_process function (around lines 112-222)
      2. Any remaining references to page_filtering logic in other functions
      3. Any dead code detected after function removal

      Verification steps:
      1. Search for all references to "page_filtering" in processing.py
      2. Search for all references to "get_smart_pages_to_process"
      3. Remove function definition and all calls
      4. Update or remove any related code
      5. Ensure no breaking changes to remaining code

      Restrictions:
      - Do not remove functions that are still in use
      - Verify no other files import the removed functions
      - Check imports at the top of the file
      - Run basic tests after removal
      - Keep git commit history clean

      Success criteria:
      - get_smart_pages_to_process function is completely removed
      - No references to page_filtering logic remain
      - Code compiles without errors
      - All tests pass (if any)
      - No functional regression in remaining features

### Phase 4: 测试与验证

- [ ] 4.1. 编写单元测试
  - **文件**: `/home/thelya/Work/data/test_pdf_cache.py` (新建)
  - **测试内容**:
    - process_pdf 两种模式的测试
    - process_from_cache 正常和失败场景
    - archive_cache 归档功能测试
  - **目的**: 确保代码质量，便于后续维护
  - **_Leverage**: pytest, unittest.mock
  - **_Requirements**: (测试需求)
  - **_Prompt**: |
      Role: QA Engineer with expertise in Python testing and pytest framework

      Task: Create comprehensive unit tests for new and modified functions.

      Test coverage needed:
      1. Test process_pdf with mode="extract_only":
         - Verify cache directory is created
         - Verify correct number of images saved
         - Verify return format {"cache_dir", "image_paths"}
      2. Test process_pdf with mode="full":
         - Verify complete processing occurs
         - Verify return format {"result", "cache_dir"}
         - Mock API call to avoid actual API usage
      3. Test process_pdf with max_pages limit:
         - Create PDF with more pages than max_pages
         - Verify only max_pages are processed
         - Verify warning is logged
      4. Test process_from_cache success:
         - Create mock cache with sample images
         - Verify images are read correctly
         - Mock API call
         - Verify result is returned
      5. Test process_from_cache failure:
         - Mock API call to raise exception
         - Verify None is returned
         - Verify error is logged
      6. Test archive_cache success:
         - Create temp cache directory with images
         - Verify zip is created
         - Verify cache is deleted after archiving
         - Verify correct path is returned
      7. Test archive_cache failure:
         - Mock shutil.make_archive to raise exception
         - Verify None is returned
         - Verify cache is not deleted
      8. Test archive_cache duplicate:
         - Call archive_cache twice on same cache
         - Verify second call behavior (skip or overwrite)

      Restrictions:
      - Use pytest framework
      - Use unittest.mock for mocking API calls and file operations
      - Create temp directories for testing (use tmpdir fixture)
      - Clean up test artifacts after tests
      - Do not make actual API calls in tests
      - Test both success and failure scenarios

      Success criteria:
      - All test cases pass
      - Code coverage >80% for new functions
      - Tests are isolated and repeatable
      - Mock external dependencies properly
      - Clear test names and docstrings

- [ ] 4.2. 集成测试与部署验证
  - **测试内容**:
    - 端到端完整流程测试
    - 失败重试场景测试
    - 性能对比测试
  - **目的**: 验证系统整体功能和性能
  - **_Leverage**: 真实PDF文件, 计时器, 日志分析
  - **_Requirements**: (所有需求)
  - **_Prompt**: |
      Role: QA Engineer with expertise in integration testing and performance validation

      Task: Perform comprehensive integration testing and deployment validation.

      Test scenarios:
      1. End-to-end happy path:
         - Process 3-5 real PDF files
         - Verify all three stages execute correctly
         - Verify data is extracted correctly
         - Verify cache is created and archived
         - Verify state.json is updated
      2. Failure and retry scenario:
         - Process PDF with simulated API failure
         - Verify cache is preserved
         - Retry with process_from_cache mode
         - Verify successful second attempt
      3. Performance comparison:
         - Measure time for full processing (including image extraction)
         - Measure time for second stage only (from cache)
         - Verify second stage is significantly faster
      4. Log analysis:
         - Process multiple PDFs
         - Analyze log file size
         - Verify base64 content is removed
         - Verify response truncation works
      5. Batch processing:
         - Process 10+ PDFs in batch
         - Verify batch number increments correctly
         - Verify all caches are archived
         - Check for memory leaks
      6. Edge cases:
         - Single page PDF
         - Very large PDF (25+ pages)
         - PDF with no extractable data
         - Corrupted PDF file

      Restrictions:
      - Use test PDFs that are representative of real data
      - Do not use production API keys in tests
      - Monitor disk space during testing
      - Clean up test artifacts after completion
      - Document all test results

      Success criteria:
      - All end-to-end tests pass
      - Second stage processing is at least 50% faster than full processing
      - Log files are significantly smaller (at least 90% reduction in size)
      - Batch processing completes without errors
      - All edge cases are handled gracefully
      - No memory leaks detected

### Phase 5: 文档与部署

- [ ] 5.1. 更新文档和 README
  - **文件**: `/home/thelya/Work/data/README.md`
  - **更新内容**:
    - 新增缓存机制说明
    - 两阶段处理流程说明
    - 命令行参数使用说明
    - 归档结构说明
  - **目的**: 帮助用户理解新功能
  - **_Leverage**: 现有README结构
  - **_Prompt**: |
      Role: Technical Writer with expertise in software documentation

      Task: Update README.md to document new cache features and two-phase processing.

      Documentation sections to add/update:
      1. Overview of cache mechanism:
         - Explain two-phase processing concept
         - Benefits (reliability, performance)
         - Cache directory structure
      2. Configuration section:
         - Document max_pages setting
         - Document archive_destination path
      3. Usage section:
         - Default mode (full processing)
         - Extract only mode with example
         - Process from cache mode with example
         - Command-line arguments table
      4. Workflow description:
         - Step-by-step processing flow
         - Error handling and retry process
         - Archive structure and location
      5. Troubleshooting:
         - Cache directory location
         - Manual retry process
         - Log file location and analysis

      Restrictions:
      - Maintain existing README structure
      - Use clear, concise language
      - Include code examples for CLI usage
      - Update table of contents
      - Keep documentation in sync with code

      Success criteria:
      - All new features are documented
      - Examples are accurate and tested
      - Documentation is clear and comprehensive
      - Formatting is consistent
      - Users can understand and use new features from docs

---

## 实施优先级

### Phase 1 (高优先级) - 核心功能
- 任务 1.1: 优化日志
- 任务 1.2: 改造 process_pdf
- 任务 1.3: 新增 process_from_cache
- 任务 1.4: 新增 archive_cache

### Phase 2 (高优先级) - 集成
- 任务 2.1: 更新主流程
- 任务 2.2: 命令行参数

### Phase 3 (中优先级) - 清理
- 任务 3.1: 更新配置
- 任务 3.2: 删除过时代码

### Phase 4 (中优先级) - 测试
- 任务 4.1: 单元测试
- 任务 4.2: 集成测试

### Phase 5 (低优先级) - 文档
- 任务 5.1: 更新文档

---

## 时间估算

| 阶段 | 任务 | 时间估算 |
|------|------|----------|
| Phase 1 | 任务 1.1-1.4 | 3-4小时 |
| Phase 2 | 任务 2.1-2.2 | 2-3小时 |
| Phase 3 | 任务 3.1-3.2 | 1小时 |
| Phase 4 | 任务 4.1-4.2 | 3-4小时 |
| Phase 5 | 任务 5.1 | 30分钟 |
| **总计** | | **10-13小时** (~1.5-2天) |

---

## 依赖关系

```
任务 1.1 (日志优化) → 无依赖
任务 1.2 (process_pdf改造) → 无依赖
任务 1.3 (process_from_cache) → 依赖 1.2
任务 1.4 (archive_cache) → 无依赖

任务 2.1 (主流程更新) → 依赖 1.2, 1.3, 1.4
任务 2.2 (CLI参数) → 依赖 1.3

任务 3.1 (配置更新) → 无依赖
任务 3.2 (代码清理) → 依赖 1.2, 2.1 (确保不再使用旧函数)

任务 4.1 (单元测试) → 依赖所有实现任务
任务 4.2 (集成测试) → 依赖 4.1

任务 5.1 (文档) → 依赖所有功能实现
```

---

## 验收标准

所有任务完成后需要验证：

1. ✅ 日志中不包含base64编码内容
2. ✅ process_pdf 支持 mode 参数且向后兼容
3. ✅ 图片正确保存到 ./cache/{pdf_name}/
4. ✅ process_from_cache 可以独立调用
5. ✅ archive_cache 正确创建zip并清理cache
6. ✅ 主流程执行三阶段处理
7. ✅ 命令行参数支持三种模式
8. ✅ 配置文件中已删除 page_filtering
9. ✅ 所有单元测试通过
10. ✅ 集成测试验证性能提升
11. ✅ 文档已更新
