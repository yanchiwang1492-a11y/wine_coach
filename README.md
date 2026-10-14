# WineCoach 葡萄酒销售实战模拟平台

一个基于 **FastAPI + LangGraph 多智能体 + 四层记忆系统** 的葡萄酒销售陪练应用。
前端 Vue3，后端通过 SSE 流式输出 AI 陪练对话，支持语音识别、练习评分、历史记录、评估报告邮件。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI + LangGraph（多智能体状态图） |
| 模型 | 线上 dashscope（qwen-plus）为主，本地 ollama 兜底 |
| 工具协议 | FastMCP（题库/历史/记忆/画像工具集） |
| 数据存储 | MySQL（业务数据）、PostgreSQL（摘要+图状态）、Redis（窗口/画像/黑名单）、Chroma（长期记忆向量） |
| 前端 | Vue3 + Element Plus + ECharts + marked |

---

## 一、整体请求链路

```
前端 Chat.vue
   │  GET /chat/stream?question=...&session_id=...（SSE 流式）
   ▼
chat_service.stream_chat          ← 保存消息 + 调用记忆系统
   │
   ▼
WineCoachGraph.chat_events        ← LangGraph 多智能体（星型拓扑，manager 中央调度）
   │  节点：manager → intent → question → answer → evaluate / chat
   │  （intent 识别意图 → question 出题 → answer 记录答案 → evaluate 评分 → chat 闲聊）
   ▼
四层记忆系统 + MCP 工具集
```

**SSE 事件流**（后端逐条推送，前端据此更新界面）：
- `{"kind": "status", "text": "..."}` — 后台状态提示（"正在干嘛"）
- `{"kind": "token",  "text": "..."}` — AI 回答文本片段（流式打字）
- `{"kind": "chart",  "data": [...]}` — 结构化评分（前端 ECharts 绘图）
- `{"kind": "done"}` — 结束标记

---

## 二、目录结构

### 后端 `wine_coach_backend/`

```
main.py                  入口：lifespan 预加载 + 路由注册 + MCP 挂载
common/                  基础设施（连接池/工具）
  ├─ mysql_util.py        MySQL 连接池（pymysql + DBUtils）
  ├─ pg_util.py           PostgreSQL 连接池（psycopg3 + AsyncConnectionPool）
  ├─ redis_util.py        Redis 客户端（单例）
  ├─ chroma_util.py       Chroma 向量库（单例）
  ├─ app_context.py       启动预加载（图/checkpointer/语音/MCP）
  ├─ jwt_util.py          JWT 生成与验证
  ├─ jwt_decode.py        认证依赖（get_current_user / verify_token_or_none）
  ├─ password_util.py     bcrypt 密码哈希
  ├─ token_blacklist.py   退出登录黑名单
  └─ console_util.py      Windows 控制台 UTF-8 配置

ai/
  ├─ model/
  │  ├─ my_model.py       线上/本地/语音模型单例
  │  └─ call_helper.py    「线上→本地→兜底」降级调用封装
  ├─ prompt/              YAML 提示词（意图/路由/聊天/评价）+ builder_prompt.py
  ├─ tool/                原生 LLM 工具（mysql_tool / send_email_tool）
  └─ agent/
     ├─ vosk_agent.py     语音识别
     └─ multi_agent/
        ├─ graph/coach_graph.py   多智能体图（七节点）
        ├─ node/          各节点（manager/intent/question/answer/evaluate/chat/router）
        ├─ schema/        意图/评价/路由 的 Pydantic Schema
        └─ state/         CoachState 状态定义

memory/                  四层记忆系统
  ├─ memory_save/         L1窗口(Redis) / L2摘要(PG) 存储
  ├─ memory_retrieval/    L3长期/L4画像的读写与调度（memory_manager 统一入口）
  └─ prompt_builder.py    把四层记忆拼进 system prompt

tools/                   MCP 工具集
  ├─ mcp_server.py        FastMCP 注册工具（题库/历史/记忆/画像）
  ├─ mcp_client.py        MCP 工具 → LangChain 工具（同进程直连）
  ├─ question_tool.py     题库查询（唯一入口）
  ├─ knowledge_tool.py    长期记忆检索（唯一入口）
  ├─ profile_tool.py      用户画像（唯一入口）
  └─ history_tool.py      历史消息/会话的读写

chat/                    controller → service（历史/聊天）
users/                   controller → service → dao（注册/登录/登出）
```

### 前端 `wine_coach_frontend/src/`

```
main.js              axios 拦截器（自动附 token / 401 跳登录）
router/index.js      路由 + 登录守卫
utils/               公共工具（auth / date / markdown）
api/chat.js          SSE 流式对话封装
components/
  ├─ Chat.vue        主聊天页（侧边栏 + 聊天 + 语音 + 图表）
  ├─ History.vue     历史记录列表
  ├─ SessionDetail.vue  会话详情
  ├─ Login.vue / Register.vue  登录/注册
  └─ Home.vue        首页
```

---

## 三、四层记忆系统

| 层 | 存储 | 内容 | 触发时机 |
|---|---|---|---|
| **L1 窗口** | Redis List | 最近 20 条对话（JSON） | 每轮对话写入 |
| **L2 摘要** | PostgreSQL | 会话增量摘要 | 窗口 ≥ 10 条时触发 |
| **L3 长期** | Chroma 向量库 | 跨会话的问答知识点 | 每轮判断"是否值得存" |
| **L4 画像** | Redis Hash | 薄弱题型/阶段、评分均值 | 每次评价结束后更新 |

组装顺序：`L2摘要 → L3长期Top5 → L4画像 → L1窗口`，拼进 `chat_node` 的 system prompt 前面。

---

## 四、异步模型说明（为什么这样设计）

生产级的关键是「**别让同步阻塞 IO 卡住事件循环**」，而非"全部改成 async"。本项目采用**分层策略**：

| 存储 | 方案 | 理由 |
|---|---|---|
| PostgreSQL | psycopg3 **异步** + `AsyncConnectionPool`（checkpointer 和摘要共用一个池） | LangGraph checkpointer 本身需要 async；池控连接数 |
| MySQL | pymysql **同步** + `DBUtils.PooledDB` 连接池 | 换异步驱动（aiomysql）改动大、收益低 |
| Redis / Chroma | **同步**驱动，在 async 上下文用 `asyncio.to_thread` 隔离 | 操作够快，异步化意义小 |

要点：
- 同步节点（question/intent/answer）里的同步 IO 由 LangGraph 自动丢线程池执行，安全。
- async 节点（chat/evaluate）里的同步 IO（Redis/Chroma/MySQL）统一用 `asyncio.to_thread` 包，避免阻塞事件循环（见 `memory_manager.py`、`chat_service.py`）。

---

## 五、启动方式

### 后端
```bash
cd wine_coach_backend
pip install -r requirements.txt
# 复制 .env.example 为 .env，填好数据库/模型/密钥配置
python main.py        # 默认 0.0.0.0:8000
```

### 前端
```bash
cd wine_coach_frontend
npm install
npm run dev           # 默认 localhost:8080，已配 Vite 代理到后端
```

### 前置依赖
- MySQL：`wine_coach` 库（`user` / `question_library` / `practice_session` / `practice_message`）
- PostgreSQL：`wine_coach_memory` 库（`session_summary` + checkpointer 表自动建）
- Redis：本地 6379
- Chroma：本地持久化目录 `./db_chroma`
- 题库种子数据：`python create_data/seed_question_library.py`

---

## 六、关键设计决策

1. **多智能体星型拓扑**：所有节点都连回 `manager`，由 manager 用「关键词短路 → 路由分类 → 状态机」统一调度，避免节点间混乱跳转。
2. **三级兜底**：模型调用统一「线上 → 本地 → 静态默认」（见 `ai/model/call_helper.py`）；题库查询「维度筛选 → 去排除 → 全库随机」。
3. **MCP SSE 标准协议**：FastMCP 服务端挂 `/mcp/sse`，MultiServerMCPClient 客户端通过 SSE 连接，标准 MCP 协议，想加第二个服务改 `.env` 就行。
4. **JWT 无状态 + Redis 黑名单**：实现"退出即失效"。

---

## 七、记忆架构（类式封装，参考 exam_0914）

```
SessionManager          ← 会话级入口，一个 session 一个实例
  ├── WindowMemory       L1 Redis List（最近 20 条）
  ├── SummaryMemory      L2 PostgreSQL（会话摘要）
  ├── LongMemory         L3 Chroma（跨会话知识）
  ├── ProfileMemory      L4 Redis Hash（用户画像）
  └── PromptBuilder      组装四层记忆为 system prompt

MemoryManager           ← 更新调度器
  ├── SummaryAgent       L2 增量摘要生成
  ├── LongAgent          L3 检索 + 是否存入判断
  └── ProfileAgent       L4 评价解析 + 画像更新
```

- **存储层 / 提取层 / 调度层** 三层解耦
- 旧函数式入口保留兼容层（`memory_on_user_message` 等），迁移平滑
- 组装顺序：`L2摘要 → L3长期 → L4画像 → L1窗口`（首因 + 近因效应）

---

## 八、并发安全与断点续传

### 分布式会话锁（Redis + Lua）

同一 `session_id` 同一时间只允许一个请求跑图，防止 checkpointer 状态互相覆盖。

- 加锁：`SET key token NX EX 300`（SETNX + 5 分钟过期）
- 释放：Lua 脚本原子执行「GET 判断持有者 → DEL 删除」，防止误删别人的锁

### 断点续传（LangGraph checkpointer）

基于 `AsyncPostgresSaver`，图状态持久化到 PostgreSQL：

1. 每跑完一个节点，state 自动存到 `checkpoints` 表
2. 同 `thread_id` 下一次调用自动恢复 state
3. 服务重启也能接着练——状态在数据库，不在内存

进度查询接口：`GET /chat/session_state?session_id=xxx`
返回 `practice_step / current_index / question_count` 等，前端展示进度条。

---

## 九、前端组件拆分

`Chat.vue` 拆为 4 个子组件 + 1 个主组件：

| 组件 | 职责 |
|------|------|
| `ChatSidebar.vue` | 左侧边栏（新建/搜索/会话列表） |
| `ChatHeader.vue` | 顶部栏（标题/用户/登出） |
| `ChatMessageList.vue` | 消息列表（空状态/消息/进度条/图表） |
| `ChatInput.vue` | 底部输入区（文本/语音/发送） |
| `Chat.vue` | 主组件，状态管理 + 语音 WebSocket 逻辑 |

语音逻辑留在主组件（WebSocket + AudioContext + 降采样 ~160 行），其余全部拆出。
