# AgentDevInsight

Agent 评估与可观测性平台。兼容 LangFuse 协议，提供 SDK + LangChain/LangGraph 回调双模接入，覆盖 Trace → 评估 → 对比 → 回归测试完整链路。

---

## 启动命令（开发模式）

### 后端 (FastAPI)

```powershell
# 终端 1：启动后端
cd D:\test2\agent-dev-insight\backend

# 方式 A：临时用 SQLite（无需 Docker/PostgreSQL，推荐本地开发）
set DATABASE_URL=sqlite+aiosqlite:///./agentdev.db
set DATABASE_URL_SYNC=sqlite:///./agentdev.db
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 方式 B：用 Docker Compose 启动全部服务（PostgreSQL + Redis + 后端 + 前端）
docker compose up -d
```

API 文档自动生成在 http://localhost:8000/docs

### 前端 (Next.js)

```powershell
# 终端 2：启动前端
cd D:\test2\agent-dev-insight\frontend
npm run dev -- -p 3001
```

浏览器打开 http://localhost:3001

### 运行测试

```powershell
cd D:\test2\agent-dev-insight\backend
venv\Scripts\python.exe -m pytest tests/ -v
# 69 个测试用例，全部通过才算正常
```

---

## 新用户快速上手指南

### 这个项目是什么

AI Agent 的可观测性平台——监控和分析 AI Agent 每次运行的质量、延迟、成本和准确性。

### 浏览器端能做什么

| 页面 | 可以做什么 |
|------|------|
| **Dashboard** `/` | 看全局概览：总调用数、平均延迟、Token 消耗、成本、错误率 |
| **Traces** `/traces` | 搜索/筛选 Agent 运行记录 → 点击名称查看 Waterfall 时间线、Span 详情、对话回放 |
| **Evaluations** `/evaluations` | 查看所有已完成 Trace 的评估分数 → 点击 Evaluate 按钮一键评分 |
| **Datasets** `/datasets` | 创建测试数据集 → 点击展开添加用例 → 用于回归测试 |
| **Experiments** `/experiments` | 创建模型对比实验 → 点击展开查看各 Run 的延迟/成本/分数对比 |

### 数据怎么进来

数据来自你的 AI Agent 代码，通过以下方式自动上报：
- **HTTP API**：`POST /api/public/traces`、`POST /api/public/spans`（兼容 LangFuse 协议格式）
- **Python SDK**：`from agentdevinsight import trace`
- **验证脚本**：运行 `python test_full_flow.py` 模拟一次完整的 Agent 调用

### 5 分钟体验流程

```bash
# 1. 启动后端和前端（两个终端）
# 2. 运行验证脚本，向平台灌入模拟数据
cd D:\test2\agent-dev-insight
python test_full_flow.py

# 3. 打开浏览器 http://localhost:3001
# 4. Dashboard 看总览 → Traces 点击一条记录看 Waterfall
# 5. Evaluations 页面点 Evaluate 按钮自动评分
# 6. Datasets 页面点 New Dataset 创建测试集
# 7. Experiments 页面点 New Experiment 创建对比实验
```

---

## 项目文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目需求 | [docs/requirements.md](docs/requirements.md) → 根 [REQUIREMENTS.md](REQUIREMENTS.md) | 完整需求定义 |
| 技术架构 | [docs/architecture.md](docs/architecture.md) | 架构图、数据流、技术决策 |
| 编码规范 | [docs/development_standards.md](docs/development_standards.md) | Python/TS 规范、Git 提交格式 |
| API 规范 | [docs/api_spec.md](docs/api_spec.md) | 全部 API 接口定义 |
| 前端设计 | [docs/frontend_design.md](docs/frontend_design.md) | 页面路由、组件树、色彩规范 |
| 执行步骤 | [docs/execution_plan.md](docs/execution_plan.md) | Phase 1-6 步骤清单 |
| 手工测试指南 | [docs/manual_test_guide.md](docs/manual_test_guide.md) | 手工验证各功能的 curl 命令 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy(async) |
| 数据库 | PostgreSQL（生产）/ SQLite（本地开发） |
| 缓存/队列 | Redis + Celery（可选，本地开发可跳过） |
| 前端 | Next.js 14 + Tailwind CSS + shadcn/ui + Recharts |
| 部署 | Docker Compose |

---

## 开发中断与恢复

### 每次重新打开项目时

1. 先看 [dev_logs/](dev_logs/) 里最新的日志文件，了解上次做到哪了
2. 按上方"启动命令"启动后端和前端
3. 运行测试确认环境正常：`venv\Scripts\python.exe -m pytest tests/ -v`
4. 继续开发

### 每次开发结束前

在 `dev_logs/` 创建 `YYYY-MM-DD.md`，记录：
```markdown
## 今日完成
- [x] 修了 Evaluations 页面空白的 bug
- [x] 加了一键 Evaluate 按钮
- [x] 修复 Span 创建时没算 latency_ms 的问题

## 下一步
- [ ] Experiments 对比数据需要接入真实 LLM
- [ ] 前端加雷达图可视化
- [ ] 写 Phase 2: LangFuse 兼容层测试
```

---

## 工作约定

### 开发流程
1. 严格按 [docs/execution_plan.md](docs/execution_plan.md) 的 Phase/Step 顺序推进
2. 每个 Step 完成后运行测试确保不回归
3. Phase 完成后在 [dev_logs/](dev_logs/) 记录阶段总结

### 开发日志
- 每次开发会话结束时，在 `dev_logs/` 创建当天日志文件（格式：`YYYY-MM-DD.md`）
- 日志内容：完成的事项 + 待办的下一步
- 参考模板：[dev_logs/TEMPLATE.md](dev_logs/TEMPLATE.md)

### 代码规范
- 遵循 [ai_agent_multi_coordination](D:\test2\ai_agent_multi_coordination) 项目已建立的代码模式
- 具体标准见 [docs/development_standards.md](docs/development_standards.md)

### 响应格式
- 所有 API 使用统一格式：`{"code": int, "message": str, "data": ...}`
- 分页响应包含 `total`, `page`, `page_size`, `items`

## 项目结构

```
agent-dev-insight/
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── api/              # 路由层 + public/ (LangFuse兼容)
│   │   ├── core/             # 配置、数据库、Celery
│   │   ├── evaluators/       # 评估器注册表 + builtin/
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── sdk/              # Python SDK
│   │   ├── services/         # 业务服务层
│   │   ├── tasks/            # Celery 任务
│   │   └── utils/            # 工具函数
│   └── tests/                # 后端测试
├── frontend/                 # Next.js 前端
│   └── src/
│       ├── app/              # 页面路由
│       ├── components/       # UI 组件
│       ├── hooks/            # 自定义 Hook
│       ├── lib/              # API 客户端
│       ├── stores/           # Zustand 状态
│       └── types/            # TypeScript 类型
├── sdk-python/               # pip-installable SDK
├── tests/                    # 根级测试
├── docs/                     # 项目文档
├── dev_logs/                 # 开发日志
└── docker-compose.yml
```
