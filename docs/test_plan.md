# AgentDevInsight — 测试方案

## 测试范围

| # | 方案 | 类型 | 说明 |
|---|------|------|------|
| 1 | 后端单元测试 | 自动化 | pytest 69 用例 |
| 2 | API 端点全覆盖 | 手动 | 16 REST + 1 WS 全部端点 |
| 3 | 前端页面加载 | 手动 | 6 个路由页面渲染验证 |
| 4 | 数据集/实验 CRUD | 手动 | 完整增删改查链路 |
| 5 | 评估器准确性 | 手动 | 验证评分值合理性 |
| 6 | 错误处理 | 手动 | 404/400/500 响应验证 |
| 7 | SDK 集成 | 手动 | @trace 装饰器端到端 |
| 8 | 前端构建 | 自动化 | `npm run build` |

---

## 方案 1：后端单元测试

```bash
cd backend && venv\Scripts\activate && pytest tests/ -v
```

期望：69/69 全部通过

---

## 方案 2：API 端点全覆盖

| # | 方法 | 路径 | 期望 |
|---|------|------|------|
| 1 | GET | / | 200 + 项目名 |
| 2 | GET | /api/health | 200 + DB/Redis 状态 |
| 3 | POST | /api/public/traces | 201 + trace_id |
| 4 | GET | /api/public/traces | 200 + 列表 |
| 5 | POST | /api/public/spans | 201 + span_id |
| 6 | POST | /api/public/generations | 201 + gen_id |
| 7 | POST | /api/public/scores | 201 + score_id |
| 8 | GET | /api/traces | 200 + 分页列表 |
| 9 | GET | /api/traces/{id} | 200 + 详情含 spans/scores |
| 10 | GET | /api/traces/{id}/spans | 200 + spans 列表 |
| 11 | GET | /api/traces/{id}/replay | 200 + events |
| 12 | POST | /api/traces/{id}/complete | 200 |
| 13 | DELETE | /api/traces/{id} | 200 |
| 14 | POST | /api/traces/{id}/evaluate | 200 + scores |
| 15 | GET | /api/evaluators | 200 + 评估器列表 |
| 16 | GET | /api/dashboard/overview | 200 + 指标 |
| 17 | POST | /api/datasets | 201 |
| 18 | GET | /api/datasets | 200 |
| 19 | POST | /api/datasets/{id}/items | 201 |
| 20 | POST | /api/experiments | 201 |
| 21 | GET | /api/experiments | 200 |

---

## 方案 3：前端页面加载

| # | 路由 | 期望 |
|---|------|------|
| 1 | / | Dashboard 渲染，有指标卡片 |
| 2 | /traces | 列表页渲染，有搜索框和表格 |
| 3 | /traces/{id} | 详情页渲染，Waterfall/Replay/JSON 可切换 |
| 4 | /datasets | 占位页渲染 |
| 5 | /experiments | 占位页渲染 |
| 6 | /evaluations | 占位页渲染 |

---

## 方案 4：数据集/实验 CRUD

1. 创建 Dataset → 201
2. 添加 Item → 201
3. 从 Trace 生成 Item → 201
4. 创建 Experiment → 201
5. 添加 Run → 200
6. 完成 Run → 数据更新
7. 删除 Dataset → 200
8. 删除 Experiment → 200

---

## 方案 5：评估器准确性

1. 正常完成 Trace → completion_rate ≈ 0.95
2. Error 状态 Trace → completion_rate = 0.0
3. 有 Tool Span → tool_accuracy > 0
4. 有 Generation → total_tokens > 0
5. token_cost 价格计算正确

---

## 方案 6：错误处理

1. GET 不存在的 Trace → 404
2. DELETE 不存在的 Trace → 404
3. GET 不存在的 Dataset → 404
4. 非法 JSON 请求体 → 422
5. 缺少必填字段 → 422

---

## 方案 7：SDK 集成

1. `@trace` 装饰器包裹函数 → Trace 创建
2. `client.trace()` 上下文管理器 → 完整四级嵌套上报
3. `AgentDevInsightCallbackHandler` → LangChain 回调

---

## 方案 8：前端构建

```bash
cd frontend && npm run build
```

期望：编译成功，无类型错误
