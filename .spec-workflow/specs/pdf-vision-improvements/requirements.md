# Requirements Document

## Introduction

当前CFST数据提取系统已从文本分析（pdfplumber）升级到视觉分析（pdf2image + AI）。在实际测试中发现了两个关键问题需要解决：
1. AI模型返回的JSON响应因Token溢出而被截断，导致解析失败
2. 简单的页面截断策略（只读前N页）效率低下，可能漏掉关键数据或浪费API调用

本需求旨在通过Prompt约束和智能页面筛选机制，提升系统的可靠性和成本效率。

## Alignment with Product Vision

这些改进支持产品愿景中的以下目标：
- **提高数据提取成功率**：通过解决JSON截断问题，减少处理失败率
- **降低运营成本**：智能页面筛选减少不必要的API调用
- **提升数据完整性**：确保关键数据表不会被遗漏

**业务KPI指标**：
- 在保持或提升数据提取准确率的前提下，尽可能缩小所读页数
- 精准定位包含表格、试验数据的页面，提高数据提取的精确度和效率
- 长论文（>10页）的API调用成本预计降低30-50%

## Requirements

### Requirement 1: JSON输出格式约束

**User Story**: 作为系统管理员，我希望确保AI模型只返回纯JSON格式且reason字段受限，这样可以避免Token溢出导致的JSON截断和解析失败。

#### Acceptance Criteria

1. WHEN AI模型处理PDF并生成响应时 THEN 系统SHALL在System Prompt中明确要求：
   - 只输出纯JSON字符串，不包含Markdown代码块标记（```json）
   - reason字段必须为empty string `""` 或最多10个单词的简短说明
   - 不包含任何解释性文字或前言

2. IF AI返回的JSON包含被截断的字符串 THEN 系统SHALL记录该错误并优雅处理

3. WHEN AI返回有效JSON时 THEN 系统SHALL验证JSON结构完整性并正常解析

### Requirement 2: 智能页面筛选机制

**User Story**: 作为系统用户，我希望系统能智能识别包含试验数据的页面，而不是简单地截断前N页，这样可以确保提取到所有相关数据同时减少不必要的API成本。

#### Acceptance Criteria

1. WHEN 处理一个PDF文件时 THEN 系统SHALL执行两阶段分析：
   - 阶段一：文本侦察（本地CPU处理，不调用API）
     * 使用pdfplumber快速提取每页文本
     * 基于关键词命中率为每页打分
     * 按分数排序并选择Top N页（例如8页）
     * 强制包含第1页（摘要有助于模型识别文献类型）

   - 阶段二：视觉提取（调用AI API）
     * 只将阶段一选出的页面转换为图片
     * 使用现有视觉处理流程提取数据

2. 评分系统SHALL按以下规则计算每页得分：
   - 高权重 (+10)：检测到表格标题（"Table 1", "Tab. 2", 等）
   - 中权重 (+5)：检测到关键数据词汇（"Specimen", "Experimental", "kN", "mm", "B/t", "D/t"等）
   - 普通文本：+1
   - 参考文献/引用页：-5

3. IF PDF页数 ≤ 10页 THEN 系统SHALL跳过筛选机制，处理所有页面（短论文全量扫描）

4. WHEN 筛选完成时 THEN 系统SHALL记录选择的页面编号和分数，用于调试和验证

5. IF 选出的页面总数超过配置的最大限制（配置的max_scan_limit）THEN 系统SHALL只处理得分最高的N页

6. IF 删除参考文献和引用页（得分为负的页面）后不足10页 THEN 系统SHALL处理所有正分数的页面（有几页读几页）

## Non-Functional Requirements

### Code Architecture and Modularity
- **模块化设计**：智能筛选功能应独立成函数，易于测试和维护
- **向后兼容**：保持现有短论文全量扫描的逻辑不变
- **配置驱动**：评分权重和阈值应可配置，便于调优
- **错误隔离**：文本侦察阶段的错误不应影响视觉提取阶段

### Performance
- 文本侦察阶段应在100ms内完成典型PDF的处理
- 阶段一处理不得对整体处理时间产生显著影响
- WHEN 处理一个100页的PDF文件时 THEN 文本侦察阶段必须在200ms内完成

### Reliability
- 即使pdfplumber失败，系统应回退到简单的截断策略
- 保留现有错误处理和重试机制
- **JSON解析失败处理策略**：IF JSON解析失败 THEN 系统SHALL标记该文件为待人工审查 AND 继续批量处理其他文件
  - 日志级别：ERROR
  - 日志内容：文件名、解析错误信息、截断的JSON内容（前500字符）
  - 文件标记方式：移动到Manual_Review/目录，并在日志中记录

### Cost Efficiency
- 长论文的API调用成本应降低30-50%
- 数据提取成功率不应因页面筛选而下降
