# AgentDevInsight — 技术架构

## 总体架构

```
┌──────────────────────────────────┐
│  Next.js Dashboard (前端)          │
│  Waterfall / 评估 / 对比 / 回归    │
│  - React 18 + Tailwind CSS        │
│  - Recharts 图表                   │
│  - Zustand 状态管理                │
│  - WebSocket 实时更新              │
└───────────────┬──────────────────┘
                │ REST + WebSocket
┌───────────────▼──────────────────┐
│  FastAPI 后端服务                  │
│  - Trace 采集 API (LangFuse 兼容)  │
│  - 评估引擎                       │
│  - 批量对比 Runner                │
│  - 回归测试调度                   │
└────────┬──────────────┬──────────┘
         │              │
┌────────▼──┐  ┌───────▼──────┐
│ PostgreSQL │  │    Redis      │
│ - 持久存储  │  │ - 缓存/队列   │
│ - JSONB     │  │ - Pub/Sub    │
│ - GIN 索引  │  │ - Celery     │
└────────────┘  └──────────────┘
```

## 后端分层

```
api/          → 路由层：请求校验、响应格式
services/     → 业务层：TraceService, ScoreService, etc.
models/       → 数据层：SQLAlchemy ORM 模型
evaluators/   → 评估层：可插拔的评估器注册表
tasks/        → 异步层：Celery 任务处理
sdk/          → SDK 层：Python 客户端和回调处理器
```

## 数据流

### Trace 采集流
```
Agent SDK → POST /api/public/traces → TraceService → PostgreSQL
                                    ↘ Celery enrich_trace → 计算成本/延迟
                                    ↘ Redis Pub/Sub → WebSocket → 前端实时更新
```

### 评估流
```
完成 Trace → Celery evaluate_trace → EvaluatorRegistry → LLM-as-Judge
                                     ↘ Score 记录 → PostgreSQL
```

### 对比/回归流
```
Experiment → Celery execute_experiment → 并发跑多模型
                                       → 采集 Trace
                                       → 运行评估
                                       → ComparisonResult → 前端雷达图
```

## 关键技术决策

| 决策 | 理由 |
|------|------|
| PostgreSQL JSONB | 灵活的 Span metadata，支持 GIN 索引查询 |
| Celery + Redis | 异步 Trace 处理，不阻塞 Agent 执行 |
| LangFuse API 兼容 | 复用 LangFuse 生态工具和 SDK |
| 三级 Trace/Span/Generation | 业界标准的 trace 层级，兼容 OpenTelemetry 概念 |
| SQLite 测试 | 参考项目模式，快速隔离的测试数据库 |

## 模型定价表

内置于 `evaluators/builtin/token_cost.py`，支持常见模型：

| 模型 | 输入价格 ($/1M tokens) | 输出价格 ($/1M tokens) |
|------|----------------------|------------------------|
| deepseek-chat | 0.14 | 0.28 |
| gpt-4o | 2.50 | 10.00 |
| gpt-4o-mini | 0.15 | 0.60 |
| claude-3.5-sonnet | 3.00 | 15.00 |
| qwen-max | 0.50 | 2.00 |
