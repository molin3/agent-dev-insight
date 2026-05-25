# AgentDevInsight 手工功能体验指南

> 前置条件：后端 `:8000` 和前端 `:3001` 都已启动。

---

## 场景 1：模拟一次 Agent 运行，观察 Trace 采集与评估

**目的**：体验从 Agent 上报数据到平台展示评估结果的完整链路。

### 1.1 模拟 Agent 上报 Trace

打开终端，逐条执行（或用 Postman）：

```bash
# 1. 创建一个 Trace（Agent 开始运行）
curl -s -X POST http://localhost:8000/api/public/traces \
  -H "Content-Type: application/json" \
  -d '{"name":"我的测试Agent"}'

# 记下返回的 trace_id，例如 "abc123..."
```

回显示例：`{"code":201,"message":"Trace created","data":{"id":"abc123..."}}`

### 1.2 上报 Agent 各步骤的 Span

```bash
TRACE_ID="改成上一步的id"

# 步骤1：Agent 做任务规划（llm 类型）
curl -s -X POST http://localhost:8000/api/public/spans \
  -H "Content-Type: application/json" \
  -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"任务规划\",\"type\":\"agent\"}"

# 步骤2：Agent 调用搜索工具（tool 类型），带输出
curl -s -X POST http://localhost:8000/api/public/spans \
  -H "Content-Type: application/json" \
  -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"搜索知识库\",\"type\":\"tool\",\"output\":{\"results\":[\"匹配到3条记录\"]}}"

# 步骤3：Agent 调用数据库查询工具（tool 类型），带输出
curl -s -X POST http://localhost:8000/api/public/spans \
  -H "Content-Type: application/json" \
  -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"查询数据库\",\"type\":\"tool\",\"output\":{\"rows\":42,\"query_time_ms\":23}}"

# 步骤4：Agent 生成最终回复（llm 类型），带 token 用量
curl -s -X POST http://localhost:8000/api/public/spans \
  -H "Content-Type: application/json" \
  -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"生成回复\",\"type\":\"llm\",\"model\":\"deepseek-chat\",\"output\":{\"reply\":\"根据查询结果...\"}}"
```

### 1.3 完成 Trace

```bash
curl -s -X POST http://localhost:8000/api/traces/$TRACE_ID/complete
```

### 1.4 运行评估

```bash
curl -s -X POST http://localhost:8000/api/traces/$TRACE_ID/evaluate \
  -H "Content-Type: application/json" \
  -d '{"evaluator_names":["completion_rate","tool_accuracy","token_cost","hallucination","latency"]}'
```

### 1.5 在浏览器查看结果

打开 http://localhost:3001/traces → 点击刚才创建的 Trace → 你应该看到：

| 要检查的 | 预期看到 |
|----------|----------|
| Waterfall 时间线 | 4 条彩色横条：agent(靛蓝)、tool(绿)×2、llm(蓝) |
| Span 详情（点击横条） | Info/Input/Output/JSON 四个标签可切换 |
| Replay 标签 | 4 个步骤卡片 |
| Scores 区域 | completion_rate 约 0.95 / tool_accuracy 约 1.00 / hallucination_score 约 0.80 |

---

## 场景 2：Dashboard 数据观察

**目的**：验证 Dashboard 汇总数据是否正确。

### 2.1 打开 Dashboard

浏览器打开 http://localhost:3001

### 2.2 检查清单

| 卡片 | 检查点 |
|------|--------|
| Total Traces | 数字 ≥ 1 |
| Avg Latency | 显示毫秒数 |
| Total Tokens | > 0 |
| Total Cost | 显示 "$" 开头的金额 |
| 下方 Completion Stats | completed / errors 数量合理 |
| Alerts 区域 | 有报错则显示红色，无报错显示 "All systems normal" |

---

## 场景 3：Trace 列表搜索与筛选

**目的**：验证列表页的搜索和筛选功能。

### 3.1 操作步骤

1. 浏览器打开 http://localhost:3001/traces
2. 在搜索框输入一个 trace 名 → 按回车
3. 用状态下拉框选 "Completed" → 点 Search
4. 点击某个 trace 名称 → 跳转到详情页

### 3.2 检查清单

| 操作 | 预期 |
|------|------|
| 搜索 trace 名 | 只显示匹配的 trace |
| 筛选 Completed | 只显示已完成的 |
| 点击名称 | 跳转到 /traces/{id} |
| 分页 | 多于 20 条时出现 Previous/Next 按钮 |

---

## 场景 4：数据集管理

**目的**：验证数据集 CRUD 功能，为回归测试做准备。

### 4.1 操作步骤

1. 浏览器打开 http://localhost:3001/datasets
2. 点击 "New Dataset" → 输入名称 "回归测试集" → 点 Create
3. 确认表格中出现新行 → v1 版本号

### 4.2 通过 API 添加测试用例

```bash
# 记下数据集的 id（从页面 URL 或表格获取）
DATASET_ID="改成你的id"
TRACE_ID="改成场景1的trace_id"

# 手动添加用例
curl -s -X POST http://localhost:8000/api/datasets/$DATASET_ID/items \
  -H "Content-Type: application/json" \
  -d '{"input":{"query":"测试问题"},"expected_output":"预期答案"}'

# 从已有 Trace 一键生成用例
curl -s -X POST "http://localhost:8000/api/datasets/$DATASET_ID/items/from-trace?trace_id=$TRACE_ID"
```

刷新页面确认用例数增加。

---

## 场景 5：实验（模型对比）

**目的**：验证实验创建和管理功能。

### 5.1 操作步骤

1. 浏览器打开 http://localhost:3001/experiments
2. 点击 "New Experiment"
3. 填写：
   - Name: `模型对比测试`
   - Task description: `比较 DeepSeek 和 GPT-4o 在文本摘要任务上的表现`
4. 点 Create
5. 确认实验卡片出现在列表中，状态为 "pending"

---

## 场景 6：查看评估结果

**目的**：验证评估页面汇总所有 Trace 的评分。

### 6.1 操作步骤

浏览器打开 http://localhost:3001/evaluations

### 6.2 检查清单

| 检查点 | 预期 |
|--------|------|
| 有评分卡片 | 每个已完成 Trace 一张卡片 |
| 卡片内容 | Trace 名称、状态 Badge、各项分数标签 |
| 分数颜色 | ≥0.8 绿色 / 0.5-0.8 黄色 / <0.5 红色 |
| 无数据时 | 显示空状态图标和提示文字 |

---

## 场景 7：错误处理验证

**目的**：验证系统对异常情况的处理。

```bash
# 1. 请求不存在的 Trace
curl -s http://localhost:8000/api/traces/nonexistent-id

# 2. 请求不存在的 Dataset
curl -s http://localhost:8000/api/datasets/nonexistent-id

# 3. 创建 Trace 时缺少必填字段
curl -s -X POST http://localhost:8000/api/public/traces \
  -H "Content-Type: application/json" \
  -d '{}'
```

预期：全部返回统一格式 `{"code":4xx,"message":"...","data":null}`

---

## 一键测试脚本

把下面脚本保存为 `test_flow.sh`，替换 TRACE_ID 后运行：

```bash
#!/bin/bash
BASE="http://localhost:8000"

echo "=== 1. 创建 Trace ==="
TRACE=$(curl -s -X POST $BASE/api/public/traces -H "Content-Type: application/json" -d '{"name":"全链路测试"}')
TRACE_ID=$(echo $TRACE | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "Trace: $TRACE_ID"

echo "=== 2. 上报 5 个步骤 ==="
curl -s -X POST $BASE/api/public/spans -H "Content-Type: application/json" -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"规划\",\"type\":\"agent\"}" > /dev/null
curl -s -X POST $BASE/api/public/spans -H "Content-Type: application/json" -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"搜索\",\"type\":\"tool\",\"output\":{\"found\":true}}" > /dev/null
curl -s -X POST $BASE/api/public/spans -H "Content-Type: application/json" -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"计算\",\"type\":\"tool\",\"output\":{\"result\":42}}" > /dev/null
curl -s -X POST $BASE/api/public/spans -H "Content-Type: application/json" -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"LLM总结\",\"type\":\"llm\",\"model\":\"deepseek-chat\",\"output\":{\"summary\":\"结果总结...\"}}" > /dev/null
curl -s -X POST $BASE/api/public/spans -H "Content-Type: application/json" -d "{\"traceId\":\"$TRACE_ID\",\"name\":\"格式化输出\",\"type\":\"tool\",\"output\":{\"format\":\"markdown\"}}" > /dev/null

echo "=== 3. 完成 Trace ==="
curl -s -X POST $BASE/api/traces/$TRACE_ID/complete > /dev/null

echo "=== 4. 评估 ==="
curl -s -X POST $BASE/api/traces/$TRACE_ID/evaluate > /dev/null

echo "=== 5. 查看结果 ==="
curl -s $BASE/api/traces/$TRACE_ID/scores | python -c "
import sys,json
for s in json.load(sys.stdin)['data']['scores']:
    print(f'  {s[\"name\"]:25s} = {s[\"value\"]:.2f}')
"

echo "=== 6. Dashboard ==="
curl -s $BASE/api/dashboard/overview | python -c "
import sys,json
d = json.load(sys.stdin)['data']
print(f'  总Traces: {d[\"total_traces\"]}')
print(f'  已评价: {d[\"completed\"]}')
print(f'  总Tokens: {d[\"total_tokens\"]}')
print(f'  总费用: \${d[\"total_cost\"]}')
"

echo "=== 完成！浏览器打开 http://localhost:3001/traces/$TRACE_ID ==="
```

---

## 验证清单速查

| # | 场景 | 操作 | 怎么算通过 |
|---|------|------|-----------|
| 1 | Agent 上报 | 场景1 全部 4 步 | Trace 列表出现新记录 |
| 2 | Waterfall 图表 | 点进 Trace 详情 | 看到彩色横条 + 可点击 |
| 3 | Span 详情 | 点击 Waterfall 横条 | 右侧面板显示 Span 信息 |
| 4 | 对话回放 | 切换到 Replay 标签 | 步骤卡片 + 可翻页 |
| 5 | 评估分数 | 点 Evaluate 后查看 | tool_accuracy > 0, completion_rate ≈ 0.95 |
| 6 | Dashboard | 打开首页 | 指标数字正确 |
| 7 | 搜索筛选 | Traces 页搜索 + 筛选 | 结果过滤正确 |
| 8 | 创建 Dataset | Datasets 页 → New | 表格出现新行 |
| 9 | 从 Trace 生成用例 | API 调用 | 刷新页面用例 +1 |
| 10 | 创建 Experiment | Experiments 页 → New | 卡片出现在列表 |
| 11 | 评估页 | Evaluations 页 | 显示评分卡片 |
| 12 | 错误处理 | 请求不存在的资源 | 返回统一错误格式 |
