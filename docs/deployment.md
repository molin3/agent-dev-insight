# 部署文档

## 开发环境部署

见 [README.md](../README.md) 中的「快速启动」章节。

## 生产环境部署

### 方式一：Docker Compose（推荐）

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

服务启动后：
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：手动部署

#### 1. 数据库准备

**PostgreSQL**（推荐）：

```sql
CREATE DATABASE agentdev;
CREATE USER agentdev_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE agentdev TO agentdev_user;
```

**Redis**：

确保 Redis 服务已启动，默认连接 `redis://localhost:6379/0`。

#### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ..\.env.example .env
# 编辑 .env 填写实际配置

# 数据库迁移（如使用 Alembic）
# alembic upgrade head

# 启动服务（生产模式）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 启动服务
npm start
```

#### 4. Celery Worker（可选）

如需异步任务处理（批量评估、实验等）：

```bash
cd backend
venv\Scripts\activate
celery -A app.core.celery_app worker --loglevel=info
```

## 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite+aiosqlite:///./agentdev.db` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `LLM_API_KEY` | LLM 评估用的 API Key | 必填 |
| `DEBUG` | 调试模式 | `false` |

完整配置参见 [.env.example](../.env.example)。

## 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/api/health

# 返回示例
{"status": "healthy", "database": "connected", "redis": "connected"}
```
