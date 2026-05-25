# AgentDevInsight — 需求文档

## 项目定位

兼容 LangFuse 协议的生产级 Agent 评估与可观测性平台。
提供 SDK + LangChain/LangGraph 回调双模接入，
覆盖 **Trace → 自动评估 → 多模型对比 → 回归测试** 完整链路。

---

## 一、核心功能模块

### 模块 1：全链路追踪 (Trace)

**数据采集层级（三级树形结构）：**

| 层级 | 说明 | 记录内容 |
|------|------|----------|
| Trace | 一次完整的 Agent 运行 | trace_id, 起止时间, 状态, 元数据 |
| Span | LLM 调用 / Tool 调用 / 自定义节点 | span 类型, 耗时, 入参, 出参, 错误信息 |
| Generation | 单次 LLM 请求的 prompt + completion | model, token_usage, cost, 延迟 |

**前端可视化：**
- Waterfall 时间瀑布图，展示 Trace 下所有 Span 的执行时序
- 每个 Span 点击展开 → 完整 JSON 详情
- 完整对话回放（还原 Agent 运行的每一步）
- 支持按 Agent 名称、时间范围、状态、模型等维度过滤查询

---

### 模块 2：自动评估 (Auto Evaluation)

**内置评估维度：**

| 评估指标 | 判断方式 |
|----------|----------|
| 任务完成率 | LLM-as-Judge 对比预期输出与实际输出 |
| 工具调用准确率 | 比对调用的工具名及参数是否合理 |
| 延迟分位数 | P50 / P95 / P99 自动统计 |
| Token 消耗 | 输入/输出 Token 汇总与成本换算 |
| 幻觉检测 | 答案声明是否与工具返回结果一致 |

**自定义评估规则：**
- 用户可编写评估 Prompt 模板
- 支持挂载到 Trace / Span 级别
- Score 数据结构兼容 LangFuse（name + value + comment + config_id）

**评估报告：**
- 单次 Run 的评估摘要卡片
- 所有 Score 的汇总视图

---

### 模块 3：多模型对比 (Model Comparison)

- 同一任务/同一批测试用例，并发调用多个模型
- 并排对比维度：延迟、Token 消耗、任务完成率、成本
- 可视化：雷达图 + 柱状图对比
- 支持模型：DeepSeek / Qwen / GPT / Claude 及任意 OpenAI 兼容接口

---

### 模块 4：回归测试 (Regression Testing)

**数据集管理：**
- UI 手动创建测试用例（输入 + 期望输出 + 评估标准）
- 从已有 Trace 一键转为测试用例
- 数据集支持分类和版本管理

**批量执行：**
- 一键对数据集跑回归
- 输出通过率变化（本次 vs 上次）
- 与 Git commit / Prompt 版本关联的 Snapshot 记录

---

### 模块 5：Dashboard

- 总览面板：总 Trace 数、平均延迟、总 Token 消耗、错误率
- Agent 健康面板：各 Agent 调用量、成功率、P95 延迟趋势
- 告警：延迟/错误率超过阈值时 **仅在 Dashboard 标记**，不做 Webhook 推送

---

## 二、接入方式

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| LangGraph / LangChain 回调 | 基于 LangGraph/LangChain 的 Agent | 框架级拦截，一行 import 即可 |
| Python SDK (@trace 装饰器) | 自定义 Agent、非 LangChain 框架 | 显式标记函数和 Span |
| HTTP API | 任意语言、任意框架 | 兼容 LangFuse 协议格式 |

---

## 三、技术架构

```
┌──────────────────────────────────┐
│  Next.js Dashboard (前端)          │
│  Waterfall / 评估 / 对比 / 回归    │
└───────────────┬──────────────────┘
                │ REST + WebSocket
┌───────────────▼──────────────────┐
│  FastAPI 后端服务                  │
│  - Trace 采集 API                 │
│  - 评估引擎                       │
│  - 批量对比 Runner                │
│  - 回归测试调度                   │
│  - 兼容 LangFuse 核心 API          │
└────────┬──────────────┬──────────┘
         │              │
┌────────▼──┐  ┌───────▼──────┐
│ PostgreSQL │  │    Redis      │
│ Trace/评估/│  │  缓存 / 队列   │
│ 数据集存储  │  │               │
└────────────┘  └──────────────┘
```

**技术栈：**

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | Python + FastAPI |
| ORM | SQLAlchemy (async) |
| 数据库 | PostgreSQL |
| 缓存/队列 | Redis + Celery |
| 前端 | Next.js + Tailwind CSS |
| 图表 | Recharts |
| 部署 | Docker Compose |

---

## 四、数据模型概要

```
Project（项目/应用）
  └── Trace（一次完整的 Agent 运行）
        ├── Span（LLM 调用 / Tool 调用 / 自定义节点）
        │     └── Generation（单次 LLM prompt + completion）
        └── Score（评估分数）

Dataset（测试数据集）
  ├── DatasetItem（单条用例：input + expected_output + eval_criteria）
  └── DatasetRun（一次回归执行，关联多条 Trace）

Experiment（对比实验）
  ├── 多个 Run（不同模型/配置执行同一任务）
  └── ComparisonResult（对比结论）
```

---

## 五、已确认的设计决策

| 决策项 | 结论 |
|--------|------|
| 项目名称 | **AgentDevInsight** |
| 生态定位 | 兼容 LangFuse Trace/Score API 协议 |
| 接入方式 | SDK 装饰器 + LangChain/LangGraph 回调，两者都要 |
| MVP 范围 | 完整 MVP（Trace + 评估 + 对比 + 回归测试） |
| 存储方案 | PostgreSQL + Redis |
| 告警通知 | 仅 Dashboard 标记，无 Webhook |
| 数据集来源 | UI 手动创建 + 从 Trace 一键生成 |
| 前端深度 | Trace 对话回放 + Span JSON 详情 |
| 迭代顺序 | Trace → 自动评估 → 模型对比 → 回归测试 |

---

## 六、不在本期范围

- Webhook / 钉钉 / 飞书 / 邮件告警推送
- 多租户 / 权限系统 / SSO 登录
- SaaS 化部署 / K8s Helm Chart
- Prompt 版本管理（Prompt Registry）
- A/B 实验统计显著性检验
