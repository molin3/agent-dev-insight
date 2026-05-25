# AgentDevInsight

Agent 评估与可观测性平台。兼容 LangFuse 协议，提供 SDK + LangChain/LangGraph 回调双模接入，覆盖 Trace → 评估 → 对比 → 回归测试完整链路。

## 项目文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目需求 | [docs/requirements.md](docs/requirements.md) → 根 [REQUIREMENTS.md](REQUIREMENTS.md) | 完整需求定义 |
| 技术架构 | [docs/architecture.md](docs/architecture.md) | 架构图、数据流、技术决策 |
| 编码规范 | [docs/development_standards.md](docs/development_standards.md) | Python/TS 规范、Git 提交格式 |
| API 规范 | [docs/api_spec.md](docs/api_spec.md) | 全部 API 接口定义 |
| 前端设计 | [docs/frontend_design.md](docs/frontend_design.md) | 页面路由、组件树、色彩规范 |
| 执行步骤 | [docs/execution_plan.md](docs/execution_plan.md) | Phase 1-6 步骤清单 |
| 开发计划 | [docs/execution_plan.md](docs/execution_plan.md) | 详细实施步骤 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy(async) |
| 数据库 | PostgreSQL + JSONB |
| 缓存/队列 | Redis + Celery |
| 前端 | Next.js 14 + Tailwind CSS + shadcn/ui + Recharts |
| 部署 | Docker Compose |

## 快速启动

```bash
# 后端
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp ../.env.example .env
python -m uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs

# 测试
python -m pytest tests/ -v
```

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
