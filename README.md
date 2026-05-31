# AgentDevInsight

AI Agent 评估与可观测性平台 — 兼容 LangFuse 协议，提供全链路 Trace、自动评估、多模型对比和回归测试。

## 功能特性

- **全链路追踪**：Trace → Span → Generation 三级层级，Waterfall 时间线可视化
- **自动评估**：5 个内置评估器（完成率、工具准确率、延迟、Token 成本、幻觉检测）
- **多模型对比**：一键对比 DeepSeek / GPT-4o / Claude / Qwen 等模型
- **回归测试**：数据集管理 + 从 Trace 一键生成测试用例
- **LangFuse 兼容**：SDK 可直接指向本平台，无需修改业务代码
- **Python SDK**：`@trace` 装饰器 + LangChain/LangGraph 回调处理器

## 快速启动

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL（或使用 SQLite 开发模式）
- Redis（可选，用于异步任务队列）

### 首次启动

```bash
# 一键配置环境（安装所有依赖）
scripts\setup.bat
```

脚本会自动完成：
1. 检查 Python / Node.js 版本
2. 创建后端虚拟环境并安装 Python 依赖
3. 安装前端 npm 依赖
4. 复制环境变量模板到 `backend/.env`

**配置环境变量**：编辑 `backend/.env`，填写数据库连接、Redis 地址和 LLM API Key。

### 日常启动

```bash
# 一键启动前后端服务
scripts\start.bat
```

启动后访问：
- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

### 手动启动（开发者）

```bash
# 后端
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload

# 前端（另开终端）
cd frontend
npm run dev
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| ORM | SQLAlchemy (async) |
| 数据库 | PostgreSQL / SQLite |
| 缓存/队列 | Redis + Celery |
| 前端框架 | Next.js 14 |
| 样式 | Tailwind CSS |
| 图表 | Recharts |
| 状态管理 | Zustand |
| 部署 | Docker Compose |

## 项目结构

```
agent-dev-insight/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/             # REST API（含 LangFuse 兼容层）
│   │   ├── core/            # 配置 / 数据库 / Celery
│   │   ├── evaluators/      # 评估器注册表 + 5 个内置评估器
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── services/        # 业务服务层
│   │   └── utils/           # 工具函数
│   └── tests/               # 测试用例
├── frontend/                # Next.js 前端
│   └── src/
│       ├── app/             # 页面路由
│       ├── components/      # Waterfall / Span 详情 / JSON 查看器
│       ├── stores/          # Zustand 状态管理
│       └── lib/             # API 客户端
├── sdk-python/              # pip-installable SDK
├── docs/                    # 项目文档
├── scripts/                 # 启动 / 配置脚本
├── .env.example             # 环境变量模板
└── docker-compose.yml       # 一键部署
```

## 文档

- [需求文档](REQUIREMENTS.md)
- [技术架构](docs/architecture.md)
- [API 规范](docs/api_spec.md)
- [编码规范](docs/development_standards.md)
- [部署文档](docs/deployment.md)

## License

MIT
