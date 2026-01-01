# Initial Request

**Timestamp**: 2025-12-31-2352
**Slug**: workflow-upgrade
**Status**: Active

## Task Description

**任务目标**： 将现有数据提取工作流从**Workflow 1.0**升级为**Workflow 2.0**，实现结构化输出、物理模型校验和异常检测机制，提升数据准确率并降低人工干预。

## Core Task List

### 1. 集成Instructor与Pydantic模型
- 使用instructor库替代原始JSON解析方式
- 定义Pydantic模型SpecimenData，除了原程序中给基本字段外，新增一个字符串类型的source_evidence字段
- **要求**：确保source_evidence字段包含数据来源的原文句或表格行，实现可追溯性

### 2. 实现物理公式校验（"物理安检门"）
- 在DataFrame处理环节新增列：
  - **理论承载力N_theory**（公式：$N_t = A_s * f_y + A_c * f_c）$
    - $A_c = (b - 2t)(h - 2t) - (4 - \pi)r_1^2$
    - $A_s = 2t(b + h) - 4t^2 - (4 - \pi)(r_0^2 - r_1^2)$
    - 上述公式适用于所有截面类型
  - **校验系数$\xi$**（公式：$\xi = N_{exp} / N_t$）

- **判定规则**：
  | 校验结果 | 条件                | 行动建议               |
  | -------- | ------------------- | ---------------------- |
  | 正确     | 0.8 < xi < 2.5      | 数据正确，无需人工核查 |
  | 红灯     | xi > 10 或 xi < 0.1 | 单位错误，批量修正     |
  | 黄灯     | 其他情况            | 标记需人工核查         |

- 在DataFrame新增列needs_manual_check：
  - 若xi不在(0.8, 2.5)范围内，设为True
  - 使用pandas样式将needs_manual_check == True的行背景设为**浅红色**

### 3. 输出优化与人工核对支持
- 导出Excel文件时需满足：
  - source_evidence字段紧邻n_exp字段，便于定位原始数据
  - 所有needs_manual_check == True的数据行用浅红色高亮显示
- 导出后需添加计算列或运行脚本完成校验（而非直接结束流程）

### 4. 新旧工作流对比改进点（需体现在代码中）
- **输入处理**：从截取前50,000字符改为保留全文或智能切分（保留开头+附录），防止数据丢失
- **提示词**：用Pydantic模型替代手写JSON Prompt，确保格式正确
- **数据字段**：除数值（如N_exp）外，提取完整参数+source_evidence支持溯源
- **质量控制**：新增物理校验和自动标红，减少70%人工核对量
- **输出格式**：从CSV升级为带样式Excel，提升审查效率

## Delivery Requirements
- 代码需包含上述所有逻辑，确保可运行且符合规范
- 使用Python实现，集成必要库（如pandas, Pydantic, instructor）
- 最终输出为符合要求的Excel文件，含高亮标记和完整溯源信息

## Notes
- This is a data extraction workflow upgrade from Workflow 1.0 to Workflow 2.0
- Focus on structured output, physical model validation, and anomaly detection
- Goal: Improve data accuracy and reduce manual intervention