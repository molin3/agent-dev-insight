# AgentDevInsight — 执行步骤

## 总体迭代

参见项目根目录 [CLAUDE.md](../CLAUDE.md) 和各 Phase 步骤清单

### Phase 1：项目基础 ✅
- [x] 1.1 目录结构
- [x] 1.2 配置文件
- [x] 1.3 数据库连接
- [x] 1.4 Celery 配置
- [x] 1.5 BaseModel
- [x] 1.6 数据模型
- [x] 1.7 FastAPI 入口 + 健康检查
- [x] 1.8 工具模块
- [x] 1.9 测试基础
- [x] 1.10 Docker Compose
- [x] 1.11 文档规范
- [x] 1.12 CLAUDE.md

### Phase 2：Trace 采集
- [ ] 2.1 LangFuse 兼容 API
- [ ] 2.2 字段名兼容层
- [ ] 2.3 TraceService
- [ ] 2.4 内部查询 API
- [ ] 2.5 Celery Trace 任务
- [ ] 2.6 WebSocket 实时推送
- [ ] 2.7 Python SDK
- [ ] 2.8 测试 Phase 2

### Phase 3：前端 Trace 可视化
- [ ] 3.1 Next.js 脚手架
- [ ] 3.2 API 客户端 + 类型
- [ ] 3.3 状态管理
- [ ] 3.4 布局 + 导航
- [ ] 3.5 Dashboard 总览页
- [ ] 3.6 Trace 列表页
- [ ] 3.7 Trace 详情页
- [ ] 3.8 对话回放 + WebSocket

### Phase 4：自动评估
- [ ] 4.1 Evaluator 注册表
- [ ] 4.2 内置评估器
- [ ] 4.3 自定义评估规则
- [ ] 4.4 EvaluationService
- [ ] 4.5 Celery 评估任务
- [ ] 4.6 前端评估视图

### Phase 5：模型对比 + 回归测试
- [ ] 5.1 Dataset 管理 CRUD
- [ ] 5.2 数据集前端
- [ ] 5.3 Experiment CRUD
- [ ] 5.4 Celery 实验/回归任务
- [ ] 5.5 对比可视化
- [ ] 5.6 测试 Phase 5

### Phase 6：集成收尾
- [ ] 6.1 Alembic 迁移
- [ ] 6.2 Demo 集成
- [ ] 6.3 全量测试
- [ ] 6.4 Bug 修复
- [ ] 6.5 CI/CD 配置
