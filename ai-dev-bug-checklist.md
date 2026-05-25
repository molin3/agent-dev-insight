# AI Agent 开发项目 — 通用 Bug 预防清单

> 丢到任何项目文件夹里，在 CLAUDE.md 里加一行 `@ai-dev-bug-checklist.md` 即可自动生效。
> 或者每次让 AI 写代码时说一句：「动手前先过一遍桌面上的 ai-dev-bug-checklist.md」。

---

## 一、LangGraph 工作流

### 1.1 Agent 节点返回值
- [ ] **节点函数必须返回 dict，不能返回自定义对象**（如 AgentResult）。
  - 如果 Agent 返回自定义对象，用包装函数提取 `.state` 字段。
  - LangGraph 的 `InvalidUpdateError: Expected dict, got X` 就是这个原因。

### 1.2 条件边函数不能修改状态
- [ ] **条件边回调只做路由判断，不要在里面改 state**。
  - 条件边返回值是 `"next_node"` 字符串，不是 state dict。
  - 状态修改放到前一个节点函数内部完成。

### 1.3 实时进度显示
- [ ] **用 `astream()` 代替 `ainvoke()`**，否则前端看不到中间进度。
  - 每收到一个 chunk 就更新一次数据库的 `current_agent` 字段。
  - 配合 WebSocket 推送可实现前端实时看到 Agent 逐个执行。

### 1.4 并行节点状态冲突
- [ ] **并行执行多个 Agent 时，不要全量 merge state**。
  - 后面的 Agent state 会覆盖前面的结果（如 reviewer 的 state 里 `test_results` 是 None，覆盖了 tester 的结果）。
  - 改成**按字段选择性合并**，各自只取自己产出的 key。

---

## 二、Agent / LLM 调用

### 2.1 解析输出必须有默认值兜底
- [ ] **LLM 返回的 JSON 每个字段都要 `{**defaults, **parsed}`**。
  - 不要直接信任 LLM 返回的字段存在或有值。
  - 质量评分、测试覆盖率等关键字段缺失会导致得分为 0。

### 2.2 LLM 调用异常时必须有降级输出
- [ ] **不要 `try/except` 后返回 `AgentResult(success=False, state=原封不动的state)`**。
  - 这会导致状态永远不推进，死循环。
  - 正确做法：异常时仍然返回 success=True + 降级/默认的输出数据。

### 2.3 LLM 配置启动前校验
- [ ] **工作流启动前验证 API Key 不为空**。
  - 不要依赖 LLM 调用失败后的异常，那样任务已入 DB，状态卡在 pending。
  - validate 失败时在创建任务的 API 端点就返回明确错误。

### 2.4 JSON 解析容错
- [ ] **`parse_json_from_text` 要处理三种情况**：直接 JSON / markdown 代码块 / 裸花括号。
  - LLM 经常在 JSON 外包 ```json ... ``` 或直接包在文字里。

---

## 三、FastAPI 后端

### 3.1 不要 return tuple 来返回 HTTP 状态码
- [ ] **`return {"error": "..."}, 404` 在 FastAPI 里不会返回 404 状态码**。
  - 它会被当成 200 OK，body 是个 tuple。
  - 正确做法：`raise HTTPException(status_code=404, detail="...")`。

### 3.2 API 响应格式统一
- [ ] **所有端点统一用 `{"code": int, "message": str, "data": any}` 格式**。
  - 前端拦截器可以统一解包，不用每个 API 调用手动处理。

### 3.3 任务创建后必须启动工作流
- [ ] **POST /tasks 不能只写 DB，要同步启动工作流**。
  - 启动失败时 catch 异常，把任务状态标为 failed，返回有用错误信息。

### 3.4 数据库字段要全量保存
- [ ] **workflow 产出的所有数据都要存 DB**。容易出现只存了 `code_files` 忘了存 `test_files`。

---

## 四、React / Next.js 前端

### 4.1 useEffect 依赖死循环
- [ ] **useEffect 依赖数组里不能放会因自身副作用而改变引用的值**。
  - 典型错误：`useEffect(..., [fetchTask, addLog])`，addLog 调用 setState 导致重渲染，又创建新 addLog 引用。
  - 解决方案：用 `useRef` 存回调，不在依赖数组里放它。

### 4.2 WebSocket 重连保护
- [ ] **WebSocket 断开时重连间隔不能太短**（至少 5 秒），失败后指数退避。
  - 频繁重连会拖慢整个浏览器。

### 4.3 状态数组越界
- [ ] **`indexOf` 查不到时返回 -1**，所有依赖 indexOf 的判断都要处理 -1 的情况。
  - 例如 `current_agent = "completed"` 不在 agentFlow 列表里，所有 Agent 都会显示 idle。

### 4.4 TypeScript 类型同步
- [ ] **后端加了新字段 / 新状态值，前端 type 定义要同步更新**。
  - 典型案例：后端返回 agent.status = "active"，但前端 AgentStatus 类型没有这个值。

### 4.5 API 拦截器解包一致性
- [ ] **拦截器解包后，所有 API 方法不要再手动 `.data`**。
  - 确保 TypeScript 类型也知道这个转换（用泛型或 any 强制）。

---

## 五、质量评分

### 5.1 评分维度数据校验
- [ ] **每个评分维度函数入参可能为 None 或空 dict**。
  - 必须 `if not data: return 0.0` 写在最前面。
  - 从 dict 取值用 `.get(key, 0.0)` 不要用 `[]`。

### 5.2 检查式评分不能只看是否存在
- [ ] **代码检查（Lint、类型、复杂度）要有实质性检查**，不能"有文件就给满分"。
  - 当前是"有代码文件就 15 分"，应该实际调用 ruff/mypy 检查。

---

## 六、代码生成

### 6.1 防止生成的 .py 文件双击闪退
- [ ] **提示词要求生成的代码末尾加 `input("\n按 Enter 键退出...")`**。
  - Windows 双击 .py 文件会开 cmd 窗口，执行完就关。加 input 让用户能看到输出。

### 6.2 提高代码质量评分的生成策略
- [ ] **提示词明确要求**：类型注解、docstring、`if __name__ == "__main__"`、错误处理。
  - 这些直接影响质量评分的 3-4 个维度。

---

## 七、通用检查流程

每次写完一个功能模块，按这个顺序过一遍：

```
1. 返回值类型对吗？（dict vs 自定义对象）
2. 异常时有降级吗？（不能 return original state）
3. 数据从 LLM 回来后用 defaults merge 了吗？
4. 并行执行时 key 会不会互相覆盖？
5. 前端类型定义和 API 返回一致吗？
6. useEffect 依赖会不会导致死循环？
7. 新字段存 DB 了吗？前端显示了没？
8. 生成的代码加 input() 了吗？
```
