# AgentDevInsight

Agent 评估与可观测性平台 — 兼容 LangFuse 协议，提供全链路 Trace、自动评估、多模型对比和回归测试。

## 功能

- **全链路追踪**：Trace → Span → Generation 三级层级，Waterfall 时间线可视化
- **自动评估**：5 个内置评估器（完成率、工具准确率、延迟、Token 成本、幻觉检测）
- **多模型对比**：一键对比 DeepSeek / GPT-4o / Claude / Qwen 等模型
- **回归测试**：数据集管理 + 从 Trace 一键生成测试用例
- **LangFuse 兼容**：SDK 可直接指向本平台
- **Python SDK**：`@trace` 装饰器 + LangChain/LangGraph 回调处理器

## 快速启动

```bash
# 后端
cd backend
python -m venv venv && source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev -- -p 3001
```

浏览器打开 http://localhost:3001

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy(async) |
| 数据库 | PostgreSQL / SQLite |
| 缓存/队列 | Redis + Celery |
| 前端 | Next.js 14 + Tailwind CSS + Recharts |
| 部署 | Docker Compose |

## 项目结构

```
agent-dev-insight/
├── backend/                 # Python FastAPI
│   ├── app/
│   │   ├── api/             # REST API（含 LangFuse 兼容层）
│   │   ├── core/            # 配置/数据库/Celery
│   │   ├── evaluators/      # 评估器注册表 + 内置评估器
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── services/        # 业务服务层
│   │   └── utils/           # 工具函数
│   └── tests/               # 69 个测试用例
├── frontend/                # Next.js 前端
│   └── src/
│       ├── app/             # 6 个页面路由
│       ├── components/      # Waterfall / Span 详情 / JSON 查看器
│       ├── stores/          # Zustand 状态管理
│       └── lib/             # API 客户端
├── sdk-python/              # pip-installable SDK
├── docs/                    # 项目文档
├── scripts/                 # 测试/演示脚本
└── docker-compose.yml       # 一键部署
```

## 文档

- [项目需求](REQUIREMENTS.md)
- [技术架构](docs/architecture.md)
- [API 规范](docs/api_spec.md)
- [编码规范](docs/development_standards.md)
- [浏览器测试指南](docs/browser_test_guide.md)

## License

MIT
