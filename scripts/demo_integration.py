#!/usr/bin/env python3
"""
AgentDevInsight Demo — 模拟 Agent 运行并通过 SDK 上报 Trace

用法:
  1. 启动 AgentDevInsight 后端: cd backend && uvicorn app.main:app --port 8000
  2. 安装 SDK: pip install -e sdk-python/
  3. 运行本脚本: python scripts/demo_integration.py
  4. 打开浏览器: http://localhost:3000 查看 Trace
"""

import sys
import os
import time
import uuid

# Add SDK path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk-python"))

from agentdevinsight import AgentDevInsight

API_URL = os.environ.get("ADEV_API_URL", "http://localhost:8000")


def simulate_agent_run():
    """模拟一个多步骤 Agent 运行，上报完整 Trace"""

    client = AgentDevInsight(
        project="demo-agent",
        api_url=API_URL,
    )

    print("[Demo] Starting agent run...")
    print(f"[Demo] API: {API_URL}")

    with client.trace(name="demo-search-summarize") as t:
        # Step 1: Planning
        with t.span(name="plan-task", type="agent") as plan:
            time.sleep(0.1)  # simulate work
            plan.generation(
                model="deepseek-chat",
                prompt=[{"role": "user", "content": "Search and summarize latest AI news"}],
                completion="Plan: 1) Search web 2) Extract key points 3) Summarize",
                usage={"prompt_tokens": 25, "completion_tokens": 18, "total_tokens": 43},
                cost=0.00001,
            )

        # Step 2: Web Search (tool call)
        with t.span(name="web-search", type="tool", parent_span_id=plan._span_id if False else None) as search:
            time.sleep(0.2)  # simulate API call
            search.generation(
                model="tavily-search",
                prompt=[{"role": "user", "content": "latest AI news 2026"}],
                completion="1) OpenAI releases GPT-5\n2) Anthropic launches Claude 4\n3) DeepSeek open-sources new model",
                usage={"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
                cost=0.001,
            )

        # Step 3: LLM summarization
        with t.span(name="llm-summarize", type="llm") as llm:
            time.sleep(0.15)
            llm.generation(
                model="deepseek-chat",
                prompt=[{
                    "role": "user",
                    "content": "Summarize: 1) OpenAI releases GPT-5\n2) Anthropic launches Claude 4\n3) DeepSeek open-sources new model",
                }],
                completion="Major AI releases in 2026: OpenAI GPT-5 with enhanced reasoning, Anthropic Claude 4 with 200K context, and DeepSeek's new open-source model competing with proprietary alternatives.",
                usage={"prompt_tokens": 50, "completion_tokens": 40, "total_tokens": 90},
                cost=0.00003,
            )

        t.score(name="completeness", value=0.95, comment="All steps completed successfully")

    print(f"[Demo] Trace ID: {t.id}")
    print("[Demo] Agent run completed. Check http://localhost:3000/traces")
    return t.id


def run_and_evaluate():
    """运行 Agent 并通过评估 API 评估"""
    import requests

    trace_id = simulate_agent_run()

    print("\n[Demo] Running evaluation...")
    resp = requests.post(
        f"{API_URL}/api/traces/{trace_id}/evaluate",
        json={"evaluator_names": ["completion_rate", "tool_accuracy", "token_cost", "latency", "hallucination"]},
    )
    if resp.status_code == 200:
        data = resp.json()
        scores = data["data"]["scores"]
        print(f"[Demo] Evaluation complete. {len(scores)} scores generated:")
        for s in scores:
            bar = "#" * int(s["value"] * 10) + "-" * (10 - int(s["value"] * 10))
            print(f"  {s['name']:20s} [{bar}] {s['value']:.2f}")
    else:
        print(f"[Demo] Evaluation failed: {resp.status_code}")

    print(f"\n[Demo] View result: {API_URL.replace(':8000', ':3000')}/traces/{trace_id}")


if __name__ == "__main__":
    run_and_evaluate()
