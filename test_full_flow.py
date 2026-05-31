"""
AgentDevInsight 全链路功能验证脚本
模拟一个完整的 Agent 运行生命周期，验证所有核心功能
"""
import requests
import json
import sys

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def test(name: str, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        FAIL += 1
        print(f"  [FAIL] {name}: {e}")

def api(method, path, **kwargs):
    res = requests.request(method, f"{BASE}{path}", **kwargs)
    return res.json()

print("=" * 60)
print("AgentDevInsight 全链路功能验证")
print("=" * 60)

# ====== 1. 健康检查 ======
print("\n--- 1. 健康检查 ---")
test("GET /api/health 返回 200", lambda: (
    api("GET", "/api/health")["code"] == 200
))
test("数据库状态 healthy", lambda: (
    api("GET", "/api/health")["data"]["database"] == "healthy"
))

# ====== 2. 创建 Trace ======
print("\n--- 2. 创建 Trace（模拟 Agent 启动）---")
res = api("POST", "/api/public/traces", json={
    "name": "智能客服Agent-测试",
    "userId": "user-001",
    "tags": ["customer-service"],
    "metadata": {"env": "test", "version": "1.0"}
})
trace_id = res["data"]["id"]
test("POST /api/public/traces 返回 201", lambda: (
    res["code"] == 201 and res["data"]["id"] is not None
))
print(f"    Trace ID: {trace_id}")

# ====== 3. 上报 Spans ======
print("\n--- 3. 上报 Spans（模拟 Agent 执行步骤）---")
span_ids = []

# Span 1: 任务规划
res = api("POST", "/api/public/spans", json={
    "traceId": trace_id,
    "name": "任务规划",
    "type": "agent",
    "input": {"user_query": "我的订单发货了吗？"},
    "output": {"plan": ["查询订单", "检查物流", "生成回复"]}
})
test("Span 1 创建: 任务规划 (agent)", lambda: res["code"] == 201)

# Span 2: 搜索知识库
res = api("POST", "/api/public/spans", json={
    "traceId": trace_id,
    "name": "搜索知识库",
    "type": "tool",
    "output": {"results": ["找到3条相关FAQ", "物流时效: 3-5天"]}
})
test("Span 2 创建: 搜索知识库 (tool)", lambda: res["code"] == 201)

# Span 3: 查询订单
res = api("POST", "/api/public/spans", json={
    "traceId": trace_id,
    "name": "查询订单",
    "type": "tool",
    "output": {"order_id": "ORD-123456", "status": "已发货", "amount": 299.5}
})
test("Span 3 创建: 查询订单 (tool)", lambda: res["code"] == 201)

# Span 4: LLM 生成回复
res = api("POST", "/api/public/spans", json={
    "traceId": trace_id,
    "name": "生成回复",
    "type": "llm",
    "model": "deepseek-chat",
    "output": {"reply": "您好，您的订单ORD-123456已发货，预计3天内送达。"}
})
test("Span 4 创建: LLM 生成回复 (llm)", lambda: res["code"] == 201)

# ====== 4. 完成 Trace ======
print("\n--- 4. 完成 Trace ---")
res = api("POST", f"/api/traces/{trace_id}/complete")
test("POST /api/traces/{id}/complete 返回 200", lambda: (
    res["code"] == 200
))
test("Trace 状态变为 completed", lambda: (
    api("GET", f"/api/traces/{trace_id}")["data"]["status"] == "completed"
))

# ====== 5. Trace 详情 ======
print("\n--- 5. Trace 详情 ---")
res = api("GET", f"/api/traces/{trace_id}")
test("GET /api/traces/{id} 返回完整数据", lambda: (
    res["data"]["name"] == "智能客服Agent-测试"
    and len(res["data"]["spans"]) == 4
))
print(f"    Span 数量: {len(res['data']['spans'])}")
for s in res["data"]["spans"]:
    print(f"      [{s['type']:6s}] {s['name']}")

# ====== 6. 对话回放 ======
print("\n--- 6. 对话回放 ---")
res = api("GET", f"/api/traces/{trace_id}/replay")
test("GET /api/traces/{id}/replay 返回事件列表", lambda: (
    len(res["data"]["events"]) >= 4
))
print(f"    回放事件数: {len(res['data']['events'])}")

# ====== 7. Dashboard 概览 ======
print("\n--- 7. Dashboard 概览 ---")
res = api("GET", "/api/dashboard/overview")
test("Dashboard 总览数据正确", lambda: (
    res["data"]["total_traces"] >= 1
    and res["data"]["completed"] >= 1
))
print(f"    总Traces: {res['data']['total_traces']}")
print(f"    已完成: {res['data']['completed']}")
print(f"    错误: {res['data']['errors']}")
print(f"    总Tokens: {res['data']['total_tokens']}")
print(f"    总成本: ${res['data']['total_cost']}")

# ====== 8. 创建 Dataset ======
print("\n--- 8. 创建 Dataset（回归测试数据集）---")
res = api("POST", "/api/datasets", json={
    "name": "客服Agent回归测试集",
    "description": "用于回归测试的客服场景用例"
})
test("POST /api/datasets 返回 201", lambda: res["code"] == 201)
dataset_id = res["data"]["id"]
print(f"    Dataset ID: {dataset_id}")

# 添加测试用例
res = api("POST", f"/api/datasets/{dataset_id}/items", json={
    "input": {"query": "我的订单发货了吗？"},
    "expected_output": "您好，您的订单已发货，预计3天内送达。"
})
test("添加测试用例到数据集", lambda: res["code"] == 201)

# 从 Trace 一键生成用例
res = api("POST", f"/api/datasets/{dataset_id}/items/from-trace?trace_id={trace_id}")
test("从 Trace 一键生成测试用例", lambda: res["code"] == 201)

# 查看数据集
res = api("GET", f"/api/datasets/{dataset_id}")
test("GET /api/datasets/{id} 返回数据集详情", lambda: (
    len(res["data"]["items"]) >= 2
))
print(f"    用例数量: {len(res['data']['items'])}")

# ====== 9. 创建 Experiment ======
print("\n--- 9. 创建 Experiment（模型对比实验）---")
res = api("POST", "/api/experiments", json={
    "name": "DeepSeek vs GPT-4o 对比",
    "task_description": "比较 DeepSeek 和 GPT-4o 在客服场景的表现",
    "description": "对比两个模型的任务完成率和响应质量"
})
test("POST /api/experiments 返回 201", lambda: res["code"] == 201)
experiment_id = res["data"]["id"]
print(f"    Experiment ID: {experiment_id}")

# 查看实验
res = api("GET", f"/api/experiments/{experiment_id}")
test("GET /api/experiments/{id} 返回实验详情", lambda: (
    res["data"]["experiment"]["name"] == "DeepSeek vs GPT-4o 对比"
))

# ====== 10. 查看评估器列表 ======
print("\n--- 10. 评估器列表 ---")
res = api("GET", "/api/evaluators")
builtin = res["data"]["builtin"]
test("内置评估器数量正确", lambda: len(builtin) >= 5)
print(f"    内置评估器: {', '.join(builtin)}")

# ====== 汇总 ======
print()
print("=" * 60)
total = PASS + FAIL
print(f"测试完成: {total} 项, 通过 {PASS} 项, 失败 {FAIL} 项")
if FAIL == 0:
    print("所有功能验证通过！项目运行正常。")
else:
    print(f"有 {FAIL} 项失败，请检查。")
print("=" * 60)
