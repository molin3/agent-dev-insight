# AgentDevInsight — API 接口规范

## 公共 API（LangFuse 兼容）

所有接口前缀：`/api/public`

| 方法 | 路径 | 说明 | LangFuse 兼容 |
|------|------|------|--------------|
| POST | /api/public/traces | 创建/更新 Trace | 是 |
| POST | /api/public/spans | 创建 Span | 是 |
| POST | /api/public/generations | 创建 Generation | 是 |
| POST | /api/public/scores | 附加评估分数 | 是 |
| GET | /api/public/traces | 查询 Trace 列表 | 是 |

### POST /api/public/traces

```json
// Request
{
  "id": "uuid (optional)",
  "name": "my-agent-run",
  "user_id": "user-123 (optional)",
  "session_id": "sess-456 (optional)",
  "metadata": {"key": "value"},
  "tags": ["production", "v1.2"]
}

// Response
{
  "code": 201,
  "message": "success",
  "data": { "trace_id": "uuid" }
}
```

### POST /api/public/spans

```json
// Request
{
  "id": "uuid (optional)",
  "trace_id": "parent-trace-uuid",
  "parent_span_id": "uuid (optional)",
  "name": "llm-call",
  "type": "llm",
  "input": {"messages": [...]},
  "output": {"content": "..."},
  "model": "deepseek-chat",
  "metadata": {}
}
```

### POST /api/public/generations

```json
// Request
{
  "span_id": "parent-span-uuid",
  "model": "deepseek-chat",
  "prompt": [{"role": "user", "content": "..."}],
  "completion": "response text",
  "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
  "latency_ms": 1234.5
}
```

### POST /api/public/scores

```json
// Request
{
  "trace_id": "trace-uuid",
  "span_id": "span-uuid (optional)",
  "name": "completion_rate",
  "value": 0.95,
  "comment": "任务基本完成，缺少错误处理"
}
```

---

## 内部 API

所有接口前缀：`/api`

### Trace 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/traces | 分页查询 Trace 列表 |
| GET | /api/traces/{id} | 获取 Trace 详情（含 Span 树） |
| GET | /api/traces/{id}/spans | 获取 Span 瀑布流 |
| GET | /api/traces/{id}/replay | 获取对话回放数据 |
| DELETE | /api/traces/{id} | 删除 Trace |
| POST | /api/traces/{id}/complete | 标记完成 |

### 查询参数（GET /api/traces）

| 参数 | 类型 | 说明 |
|------|------|------|
| project_id | string | 按项目筛选 |
| status | string | in_progress / completed / error |
| start_date | ISO date | 起始日期 |
| end_date | ISO date | 结束日期 |
| tags | string[] | 标签筛选 |
| keyword | string | 关键词搜索 |
| page | int | 页码 (default: 1) |
| page_size | int | 每页数量 (default: 20) |

### Dashboard

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/dashboard/overview | 总览指标 |

### 评估

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/traces/{id}/evaluate | 对 Trace 执行评估 |
| GET | /api/traces/{id}/scores | 获取 Trace 的所有分数 |
| GET | /api/eval-configs | 列出评估配置 |

### 数据集

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/datasets | 创建数据集 |
| GET | /api/datasets | 列出数据集 |
| GET | /api/datasets/{id} | 获取数据集详情 |
| POST | /api/datasets/{id}/items | 添加测试用例 |
| POST | /api/datasets/{id}/items/from-trace | 从 Trace 生成用例 |
| POST | /api/datasets/{id}/run | 执行回归测试 |

### 实验（模型对比）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/experiments | 创建实验 |
| GET | /api/experiments | 列出实验 |
| GET | /api/experiments/{id} | 获取实验详情 |
| POST | /api/experiments/{id}/run | 执行实验 |
| GET | /api/experiments/{id}/comparison | 获取对比数据 |

### WebSocket

| 路径 | 说明 |
|------|------|
| /ws/live | 实时 Trace 更新推送 |

WebSocket 消息格式：
```json
// 客户端 → 服务端（订阅）
{"type": "subscribe", "project_id": "uuid"}
{"type": "subscribe", "trace_id": "uuid"}

// 服务端 → 客户端（推送）
{"type": "span_created", "trace_id": "uuid", "span": {...}}
{"type": "trace_completed", "trace_id": "uuid", "totals": {...}}
```

---

## 统一响应格式

```json
// 成功
{"code": 200, "message": "success", "data": { ... }}

// 创建成功
{"code": 201, "message": "创建成功", "data": { "id": "uuid" }}

// 错误
{"code": 400, "message": "请求参数错误", "detail": "..."}
{"code": 404, "message": "资源不存在", "detail": "..."}
```

## 分页响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [...]
  }
}
```
