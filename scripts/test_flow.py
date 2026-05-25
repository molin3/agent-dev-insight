"""
AgentDevInsight 一键功能测试脚本

用法:
  1. 先启动后端: cd backend && uvicorn app.main:app --port 8000
  2. 运行本脚本: python scripts/test_flow.py
  3. 浏览器打开 http://localhost:3001 查看结果
"""

import requests
import json
import sys

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  [OK] {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")


def api(method, path, expected_status, label, body=None):
    url = f"{BASE}{path}"
    try:
        r = getattr(requests, method.lower())(url, json=body, timeout=10)
        if r.status_code == expected_status:
            ok(f"[{r.status_code}] {label}")
        else:
            fail(f"[{r.status_code} expected {expected_status}] {label}: {r.text[:100]}")
        return r
    except Exception as e:
        fail(f"{label}: {e}")
        return None


# ============================================================
print("=" * 60)
print("AgentDevInsight 全链路功能测试")
print("=" * 60)

# 1. 健康检查
print("\n--- 1. 服务健康检查 ---")
api("GET", "/api/health", 200, "健康检查")
api("GET", "/api/dashboard/overview", 200, "Dashboard 总览")
api("GET", "/api/evaluators", 200, "评估器列表")

# 2. 创建 Trace
print("\n--- 2. 创建 Trace ---")
r = api("POST", "/api/public/traces", 201, "创建 Trace",
        {"name": "全链路自动化测试", "tags": ["auto-test"]})
TRACE_ID = r.json()["data"]["id"] if r and r.status_code == 201 else None
print(f"     Trace ID: {TRACE_ID}")

# 3. 上报 Span
print("\n--- 3. 上报 Agent 执行步骤 ---")
SPAN_IDS = []
if TRACE_ID:
    steps = [
        ("任务分析与规划", "agent", None, None),
        ("搜索知识库", "tool", {"found": True, "count": 3}, None),
        ("查询用户数据", "tool", {"user_id": 1001, "balance": 42.50}, None),
        ("生成分析报告", "llm", {"summary": "用户活跃，余额正常"}, "deepseek-chat"),
        ("格式化输出", "tool", {"format": "markdown", "size": 2048}, None),
    ]
    for name, stype, output, model in steps:
        body = {"traceId": TRACE_ID, "name": name, "type": stype}
        if output:
            body["output"] = output
        if model:
            body["model"] = model
        r = api("POST", "/api/public/spans", 201, f"Span: {name}", body)
        if r and r.status_code == 201:
            SPAN_IDS.append(r.json()["data"]["id"])

# 4. 完成 Trace
print("\n--- 4. 完成 Trace ---")
if TRACE_ID:
    api("POST", f"/api/traces/{TRACE_ID}/complete", 200, "完成 Trace")

# 5. 运行评估
print("\n--- 5. 运行评估 ---")
if TRACE_ID:
    api("POST", f"/api/traces/{TRACE_ID}/evaluate", 200, "评估 Trace")

# 6. 查看评分
print("\n--- 6. 评分结果 ---")
if TRACE_ID:
    r = api("GET", f"/api/traces/{TRACE_ID}/scores", 200, "获取评分")
    if r and r.status_code == 200:
        for s in r.json()["data"]["scores"]:
            bar = "#" * int(s["value"] * 20) + "-" * (20 - int(s["value"] * 20))
            print(f"     {s['name']:25s} [{bar}] {s['value']:.3f}")

# 7. 数据集
print("\n--- 7. 数据集管理 ---")
r = api("POST", "/api/datasets", 201, "创建数据集", {"name": "自动化测试数据集"})
DS_ID = r.json()["data"]["id"] if r and r.status_code == 201 else None

if DS_ID and TRACE_ID:
    api("POST", f"/api/datasets/{DS_ID}/items", 201, "添加用例",
        {"input": {"query": "用户余额"}, "expected_output": "42.50"})
    api("POST", f"/api/datasets/{DS_ID}/items/from-trace?trace_id={TRACE_ID}", 201,
        "从 Trace 生成用例")

if DS_ID:
    api("GET", f"/api/datasets/{DS_ID}", 200, "查看数据集详情")

# 8. 实验
print("\n--- 8. 实验管理 ---")
r = api("POST", "/api/experiments", 201, "创建实验",
        {"name": "模型对比实验", "task_description": "比较不同模型在数据分析任务上的表现"})
EXP_ID = r.json()["data"]["id"] if r and r.status_code == 201 else None

if EXP_ID:
    api("GET", f"/api/experiments/{EXP_ID}", 200, "查看实验详情")

# 9. 错误处理
print("\n--- 9. 错误处理 ---")
api("GET", "/api/traces/nonexistent", 404, "404: 不存在的 Trace")
api("GET", "/api/datasets/nonexistent", 404, "404: 不存在的 Dataset")
api("DELETE", "/api/traces/nonexistent", 404, "404: 删除不存在")

# 10. 清理
print("\n--- 10. 清理 ---")
if DS_ID:
    api("DELETE", f"/api/datasets/{DS_ID}", 200, "删除测试数据集")
if EXP_ID:
    api("DELETE", f"/api/experiments/{EXP_ID}", 200, "删除测试实验")

# ============================================================
print("\n" + "=" * 60)
print(f"测试完成: {PASS} 通过, {FAIL} 失败")
print("=" * 60)

if TRACE_ID:
    print(f"\n浏览器打开: http://localhost:3001/traces/{TRACE_ID}")
    print("你应该看到: Waterfall 时间线 + 5个Span + 评分标签")
    print(f"\nDashboard: http://localhost:3001")
    print(f"Evaluations: http://localhost:3001/evaluations")

if FAIL > 0:
    sys.exit(1)
