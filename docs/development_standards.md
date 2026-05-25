# AgentDevInsight — 编码规范

## 通用原则

- 遵循 [ai_agent_multi_coordination](D:\test2\ai_agent_multi_coordination) 项目已建立的模式
- 每个 package 的 `__init__.py` 仅包含文档字符串，不导出符号
- 导入在使用处执行（惰性导入），不在模块顶层做重量级导入
- 最小变更原则：一个 PR 只做一件事

## Python 规范

### 代码风格
- Ruff 格式化，line-length=88
- 类型注解使用 Python 3.10+ 语法（`str | None` 而非 `Optional[str]`）
- 异步函数使用 `async/await`，数据库操作用 `AsyncSession`

### 模型层 (`app/models/`)
- 所有模型继承 `BaseModel`（提供 id, created_at, updated_at, to_dict()）
- 主键：`String(36)` UUID，在 Python 层生成
- 复杂数据使用 `JSONB` 类型
- Mapped 类型注解完整标注

### API 层 (`app/api/`)
- 每个路由文件包含独立的 `APIRouter()` 实例
- Pydantic 请求/响应模型定义在路由文件顶部
- 统一响应格式：`{"code": int, "message": str, "data": ...}`
- 错误用 `HTTPException`，不泄露内部错误细节

### 服务层 (`app/services/`)
- 服务类接收 `AsyncSession` 作为构造参数
- 方法返回 `Model | None`（找不到时返回 None）
- 不使用全局单例模式（由 caller 管理生命周期）

### 评估器 (`app/evaluators/`)
- 继承 `BaseEvaluator`，实现 `async def evaluate()`
- 通过 `EvaluatorRegistry` 注册
- 内置评估器放在 `builtin/` 子包

### 测试
- `conftest.py` 使用 SQLite 内存测试数据库
- per-function `db_session` fixture（create_all → yield → drop_all）
- `httpx.AsyncClient` + `ASGITransport` 做集成测试
- `pytest-asyncio` auto 模式
- 测试命名：`test_<模块名>.py`

## TypeScript 规范

### 代码风格
- Prettier 默认配置
- ESLint + Next.js 推荐规则
- 使用 TypeScript strict mode

### 组件结构
```
components/
  <domain>/
    component-name.tsx    # 主组件
```

### 状态管理
- Zustand stores 按 domain 分文件
- API 调用通过 `lib/api-client.ts` 统一处理

### 类型定义
- `types/` 下按 domain 分文件
- 与后端 Pydantic 模型保持对应

## Git 提交规范

```
feat: 新功能
fix: Bug 修复
refactor: 重构
test: 测试
docs: 文档
chore: 构建/工具
```
