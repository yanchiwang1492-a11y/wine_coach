# WineCoach 后端

葡萄酒销售实战模拟平台后端——基于 FastAPI + LangGraph 的 AI 练习系统。

## 架构总览

```
前端（Vue3 + Element Plus）
        │  SSE 流式 / WebSocket 语音
        ▼
FastAPI（路由 + 鉴权 + lifespan 预热）
        │
   WineCoachGraph（LangGraph 七节点）
        │
   ┌────┴────┐
   ▼         ▼
四层记忆   MCP 工具集
(L1~L4)  (题库/历史/记忆/画像)
```

### LangGraph 七节点图（星型拓扑）

```
           manager（中枢调度）
              │
   ┌───┬───┬──┼──┬───┬───┐
   ▼   ▼   ▼  ▼  ▼   ▼   ▼
 intent  question answer evaluate chat
```

- `manager`：中枢调度节点，所有业务节点执行完都回到它
- `intent`：意图识别（用户想练什么维度）
- `question`：出题（从题库抽题）
- `answer`：收答案
- `evaluate`：综合评价 + 生成图表
- `chat`：自由聊天/追问

所有节点都连回 manager → 星型拓扑，由 manager 决定下一步去哪。

## 四层记忆架构

| 层级 | 名称 | 存储 | 触发时机 | 数据量 |
|------|------|------|----------|--------|
| L1 | 窗口记忆 | Redis List | 每条消息 | 最近 20 条 |
| L2 | 摘要记忆 | PostgreSQL | 窗口 ≥ 10 条触发 | 每会话 1 条 |
| L3 | 长期记忆 | Chroma 向量库 | 每轮对话判断是否值得存 | 跨会话累积 |
| L4 | 用户画像 | Redis Hash | 每次评价后更新 | 每用户 1 份 |

### 记忆组装顺序（PromptBuilder）

```
【历史摘要】        ← L2（首因效应：先给大局观）
【相关长期记忆】    ← L3（语义检索 Top 5）
【用户画像】        ← L4（跨会话稳定特征）
【最近对话】        ← L1（近因效应：末尾最深刻）
```

### 记忆管理器（MemoryManager）

```
on_user_message  →  L1 窗口写入
on_ai_reply      →  L1 写入 + L3 判断是否存入 + L2 窗口满触发
on_evaluation    →  L4 画像更新
```

### 类式架构（参考 exam_0914）

```
SessionManager          ← 会话级入口，一个 session 一个实例
  ├── WindowMemory       (L1 Redis List)
  ├── SummaryMemory      (L2 PostgreSQL)
  ├── LongMemory         (L3 Chroma)
  ├── ProfileMemory      (L4 Redis Hash)
  └── PromptBuilder      （组装 system prompt）

MemoryManager           ← 更新调度器，决定何时触发哪一层
  ├── SummaryAgent       (L2 增量摘要生成)
  ├── LongAgent          (L3 检索 + 是否存入判断)
  └── ProfileAgent       (L4 评价解析 + 画像更新)
```

## 断点续传原理

基于 LangGraph 自带的 `AsyncPostgresSaver`（checkpointer）：

1. 每跑完一个节点，图的 state 自动存到 PG 的 `checkpoints` 表
2. 下次用同一个 `thread_id`（即 `session_id`）调用 `astream` 时，LangGraph 自动从 checkpointer 恢复 state
3. 服务重启后也能接着聊——因为状态在数据库里，不在内存里

进度查询接口：`GET /chat/session_state?session_id=xxx`

返回 `practice_step / current_index / question_count` 等字段，前端用来展示"第 N / M 题"。

## 并发安全：Redis 分布式锁 + Lua

同一 `session_id` 同一时间只允许一个请求跑图，避免 checkpointer 状态互相覆盖。

- 加锁：`SET key token NX EX ttl`（SETNX + 过期）
- 释放锁：Lua 脚本原子执行「GET 判断 + DEL 删除」，防止误删别人的锁

Lua 脚本：
```lua
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
```

锁默认 TTL 5 分钟，异常崩溃也不会永久占用。

## MCP 工具集

基于 FastMCP，通过 SSE 暴露。LangChain 侧用 `MultiServerMCPClient` 连接。

当前工具：
- 题库查询（按维度抽题）
- 历史消息读写
- 长期记忆检索/写入
- 用户画像读写

配置（`.env`）：
```
MCP_SERVERS={"wine_coach":{"transport":"sse","url":"http://localhost:8000/mcp/sse"}}
```

## 目录结构

```
wine_coach_backend/
├── ai/
│   ├── agent/
│   │   └── multi_agent/
│   │       ├── graph/coach_graph.py     # LangGraph 七节点图
│   │       ├── node/                    # 6 个节点（manager/intent/question/answer/evaluate/chat）
│   │       ├── state/coach_state.py     # 图的 state schema
│   │       └── schema/                  # 节点输出 schema
│   ├── model/my_model.py                # 模型封装（线上/本地/Vosk）
│   └── prompt/                          # Prompt YAML 模板
├── chat/
│   ├── controller/                      # FastAPI 路由（聊天 + 历史）
│   └── service/chat_service.py          # 聊天服务层（锁 + 记忆 + 图调用）
├── common/
│   ├── app_context.py                   # 应用上下文（lifespan 预热）
│   ├── redis_util.py                    # Redis 工具
│   ├── redis_lock.py                    # 分布式会话锁（Lua）
│   ├── pg_util.py                       # PostgreSQL 连接池
│   ├── chroma_util.py                   # Chroma 向量库
│   ├── mysql_util.py                    # MySQL 工具
│   ├── jwt_util.py / jwt_decode.py      # JWT 鉴权
│   └── console_util.py                  # Windows UTF-8 控制台
├── memory/
│   ├── manager/                         # SessionManager / MemoryManager / PromptBuilder
│   ├── memory_save/                     # 四个 Memory 类（存储层）
│   └── memory_retrieval/                # 三个 Agent 类（提取层） + 兼容层
├── tools/
│   ├── mcp_server.py                    # FastMCP 服务端
│   ├── mcp_client.py                    # MultiServerMCPClient 客户端
│   ├── knowledge_tool.py                # 题库工具
│   ├── history_tool.py                  # 历史消息工具
│   └── ...
├── users/                               # 用户模块（注册/登录/登出）
├── create_data/                         # 初始化数据脚本
├── main.py                              # FastAPI 入口
├── requirements.txt
└── .env.example
```

## 启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库连接、API Key 等

# 3. 初始化数据库（首次运行）
# - PostgreSQL：AsyncPostgresSaver 会自动创建 checkpoints 表
# - MySQL：运行 create_data/ 下的初始化脚本
# - Chroma：首次运行自动创建本地持久化目录

# 4. 启动服务
python main.py
```

服务启动后：
- API 文档：`http://localhost:8000/docs`
- MCP SSE：`http://localhost:8000/mcp/sse`

## 关于 exam_0914 的借鉴

| 组件 | 借鉴程度 | 说明 |
|------|----------|------|
| SessionManager 类 | ✅ 借鉴 | 会话级入口，封装四层记忆 |
| MemoryManager 概念 | ✅ 借鉴 | 统一调度更新时机 |
| PromptBuilder 独立模块 | ✅ 借鉴 | 四层记忆按顺序组装 |
| Memory 类封装 | ✅ 借鉴 | 每层一个类，职责清晰 |
| SummaryAgent / LongAgent / ProfileAgent | ✅ 借鉴 | 提取层与存储层解耦 |
| Redis 分布式锁 + Lua | ✅ 直接用 | 会话并发安全 |
| checkpointer 断点续传 | ✅ 已经有 | LangGraph 自带，补进度接口 |
| 全异步 redis.asyncio | ❌ 不用 | to_thread 隔离足够，全异步化成本高 |

## 重难点速查

- **为什么窗口记忆用 JSON 不用字符串？** — 结构化存储，避免 content 含冒号时误切
- **为什么画像存在 Redis 不用 MySQL？** — 高频小数据键值场景，Redis 亚毫秒级
- **为什么长期记忆用向量数据库？** — 语义检索，按意思搜不按关键词
- **为什么释放锁要用 Lua 脚本？** — GET+DEL 两步非原子，Lua 保证原子性
- **为什么记忆按 L2→L3→L4→L1 顺序拼 prompt？** — 首因+近因效应，模型对开头结尾最敏感
- **为什么增量摘要不全量摘要？** — 控制 token 消耗，长对话场景标准做法
- **为什么画像用正则不用 LLM 提取？** — 格式固定，规则更快更准
- **断点续传的原理？** — LangGraph checkpointer，state 存 PG，同 thread_id 自动恢复
