# 每周热点深度梳理 — 设计文档

## 概述

嵌入博客的「每周精选热点」功能页面。AI 自动筛选有价值的热点事件，梳理时间线、关系网、证据链和真伪标注。设计走"溯源报告"风格——与博客同一家族，但排版纪律和气质更严肃精准。

---

## 架构

```
每周执行一次 Python CLI
  ↓
DeepSeek API（联网）→ 获取本周热点候选
  ↓
[第零阶段] 政审过滤
  ↓
[第一阶段] AI 评分筛选（事件影响 > 信息增量）→ 前 5-8 个
  ↓
[第二阶段] 逐事件梳理 → 时间线 + 证据 + 关系边
  ↓
输出 JSON → blog src/content/weekly/
  ↓
Astro 构建 + React 交互组件
```

- **Python CLI**：独立脚本，手动或 cron 每周运行，调用 DeepSeek API
- **Content Collection**：`src/content/weekly/` 下每周一个 JSON，Astro 内置类型安全
- **前端**：Astro page + React islands（时间线、关系网）

---

## 数据模型

```typescript
WeeklyIssue {
  id: string            // "2026-W21"
  weekStart: string     // "2026-05-18"
  weekEnd: string       // "2026-05-24"
  events: Event[]       // 5-8 个
}

Event {
  id: string
  title: string
  impactScore: number        // 1-5
  infoGainScore: number      // 1-5
  summary: string            // ≤200 字
  timeline: TimelineNode[]
  evidence: EvidenceNode[]
  edges: Edge[]
}

TimelineNode {
  id: string
  time: string               // ISO datetime
  title: string
  description: string
  evidenceRefs: string[]
}

EvidenceNode {
  id: string
  sourceType: "官媒" | "社交平台" | "一手材料" | "其他"
  sourceName: string
  sourceUrl: string | null
  content: string
  authenticity: "真实" | "存疑" | "不实" | "待验证"
  aiReason: string
}

Edge {
  from: string
  to: string
  type: "因果" | "关联" | "反驳"
  description: string
}
```

---

## AI Pipeline

### 第零阶段：政审

排除纯政治敏感、审查违规、不适合公开的内容。只返回通过审查的事件列表。

### 第一阶段：筛选

两个维度（各 1-5 分）：事件影响 > 信息增量。取前 5-8 个，每个生成 ≤200 字概述。

### 第二阶段：逐事件梳理

对每个事件单独调用：
1. 构建 5-10 个关键时间线节点（含确切时间）
2. 收集标注证据（真实/存疑/不实/待验证 + 理由）
3. 标注节点间关系（因果/关联/反驳 + 一句话说明）
4. 输出符合 JSON Schema 的结构化数据

---

## 前端设计

### 风格：「溯源报告」

**与博客同一家族：**
- 复用 PageLayout、Header、Footer、CSS 变量色系
- 跟随系统 light/dark 主题

**差异化（严肃精确）：**
- 博客现有字体，靠字重/间距/大小区分层次
- 数据区域用 `font-variant-numeric: tabular-nums` 对齐数字
- 真伪标签仿印章效果（彩色细边框 + 淡底色）
- 排版纪律严格，不用 emoji 和花哨装饰

### 路由

| 路径 | 内容 |
|------|------|
| `/weekly/` | 往期列表（卡片网格） |
| `/weekly/[id]` | 当期详情 |

### 详情页组件

- `WeeklyHeader`：日期、事件数量概览
- `EventCard × N`：每个事件一张大卡片
  - 标题 + 双评分徽章（数字 + 进度条）
  - AI 概述
  - Tab：[时间线] [关系网] [证据]
- `TimelineView`：左侧竖线 + 圆点垂直时间轴
- `GraphView`：react-force-graph-2d 力导向关系网
- `EvidenceView`：严格表格对齐，真伪印章标签

### 互动

- Tab 切换三种视图
- 关系网可拖拽/缩放
- 时间线节点可展开/折叠详情

---

## 技术选型

| 层 | 选择 | 理由 |
|----|------|------|
| 后端脚本 | Python CLI | DeepSeek SDK 支持好，串行调用简单 |
| AI | DeepSeek API | 用户指定 |
| 前端框架 | Astro + React 18 | 与博客一致 |
| 样式 | Tailwind CSS | 与博客一致 |
| 关系图 | react-force-graph-2d | D3-force 的 React 封装，API 简单 |
| 数据存储 | JSON files（content collection） | 无需数据库，构建时加载 |

---

## 关键约束

- 第零阶段政审不可跳过
- 所有 AI 输出需符合 JSON Schema，解析失败时重试一次
- 每周 CLI 输出写入 `src/content/weekly/{id}.json`
- 前端无运行时 API 调用，全静态构建
