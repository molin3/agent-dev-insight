# AgentDevInsight — 前端设计规范

## 技术栈

- Next.js 14 (App Router)
- Tailwind CSS
- shadcn/ui 组件库
- Recharts 图表
- Zustand 状态管理
- Lucide React 图标

## 页面路由

```
/                          → Dashboard 总览
/traces                    → Trace 列表（筛选 + 分页）
/traces/[traceId]          → Trace 详情（Waterfall + 回放）
/datasets                  → 数据集列表
/datasets/[datasetId]      → 数据集详情 + 用例管理
/experiments               → 实验列表
/experiments/[experimentId] → 实验对比详情
/evaluations               → 评估报告列表
```

## 组件树

```
layout.tsx
├── AppSidebar (导航)
└── main
    └── 各页面组件

Traces/[traceId]/page.tsx
├── TraceMetadata (trace 元信息)
├── WaterfallChart (时间瀑布图)
├── SpanDetail (选中 Span 的详情)
│   └── JsonViewer (JSON 树形查看)
└── ConversationReplay (对话回放)
```

## Dashboard 布局

```
┌────────────────────────────────────────────────┐
│  [MetricCard]  [MetricCard]  [MetricCard]  [MetricCard]
│  总Traces      平均延迟      总Token消耗    错误率
├────────────────────────────────────────────────┤
│  [HealthPanel]                                  │
│  Agent1  ████████████  95%  P95: 234ms         │
│  Agent2  ██████        87%  P95: 567ms  ⚠     │
├────────────────────────────────────────────────┤
│  [RecentTraces]                                 │
│  时间  │ 名称        │ 状态    │ 延迟  │ 分数 │
│  10:23 │ agent-run-1 │ ✅     │ 1.2s │ 0.95 │
└────────────────────────────────────────────────┘
```

## Waterfall 时间线设计

- 每个 Span 一行，X 轴为相对时间
- 颜色编码：llm=蓝、tool=绿、retriever=紫、custom=灰
- 嵌套 Span 缩进显示
- 点击 Span 在右侧面板显示详情 + JSON
- 支持水平滚轮缩放

## 色彩规范

| 用途 | Tailwind Class |
|------|---------------|
| LLM Span | bg-blue-500 |
| Tool Span | bg-emerald-500 |
| Retriever Span | bg-purple-500 |
| Error | bg-red-500 |
| Score >= 0.8 | text-green-600 |
| Score 0.5-0.8 | text-yellow-600 |
| Score < 0.5 | text-red-600 |
