# WineCoach 前端

葡萄酒销售实战模拟平台前端——Vue 3 + Element Plus + Vite。

## 技术栈

- **Vue 3** + `<script setup>` 组合式 API
- **Element Plus** UI 组件库
- **Vite** 构建工具
- **ECharts** 图表库（雷达图 + 柱状图）
- **SSE** 流式对话（原生 fetch + ReadableStream）
- **WebSocket** 语音识别（Vosk）

## 目录结构

```
src/
├── components/
│   ├── Chat.vue              # 主聊天页面（组合 4 个子组件）
│   ├── ChatSidebar.vue       # 左侧边栏（会话列表 + 搜索 + 新建）
│   ├── ChatHeader.vue        # 顶部栏（标题 + 用户 + 登出）
│   ├── ChatMessageList.vue   # 消息列表（空状态 + 消息 + 进度条 + 图表）
│   ├── ChatInput.vue         # 底部输入区（文本 + 语音 + 发送）
│   ├── Home.vue              # 主页
│   ├── Login.vue             # 登录页
│   ├── Register.vue          # 注册页
│   ├── History.vue           # 历史记录页
│   └── SessionDetail.vue     # 会话详情页
├── api/
│   └── chat.js               # 聊天 API 封装（SSE 流 + 进度查询）
├── utils/
│   ├── auth.js               # 鉴权工具（token 存取）
│   ├── date.js               # 日期格式化
│   └── markdown.js           # Markdown 渲染
├── router/
│   └── index.js              # 路由配置
├── App.vue
└── main.js
```

## 核心功能

### 1. 流式对话（SSE）

后端逐事件推送，前端边收边渲染：

```
kind: status   → 后台状态提示（"正在识别意图…"）
kind: token    → 回答文本片段（逐字显示）
kind: chart    → 评估图表数据（ECharts 渲染）
kind: done     → 结束标记
```

实现：`src/api/chat.js` 里的 `streamChat()`，用 `fetch` + `ReadableStream.getReader()` 逐块读取。

### 2. 断点续传进度条

切换会话时调 `GET /chat/session_state`，拿到 `current_index / question_count / practice_step`，在聊天区顶部展示"进度：第 N / M 题"。

### 3. 语音识别（Vosk）

- 前端采集麦克风音频（48k 单声道 PCM）
- 降采样到 16k，通过 WebSocket 发给后端
- 后端用 Vosk 实时识别，返回 partial / final 文本
- 识别结果填入输入框，用户点发送

### 4. 评估图表

每次练习结束后，后端返回 `evaluation_detail` 数组（每题三个维度得分），前端渲染：
- **雷达图**：知识/技巧/表达 三维能力画像
- **柱状图**：逐题总分对比

### 5. 维度卡片出题

空状态展示 4 个维度卡片：
- 考什么（类型）：知识 / 话术 / 情景应对 / 产品推荐
- 哪个环节（销售阶段）：迎宾 / 需求挖掘 / 推荐 / 异议处理 / 成交 / 售后
- 哪类客户（客户画像）：新手 / 送礼 / 宴请 / 收藏 / 团购
- 涉哪个品类（产品知识）：产区 / 品种 / 年份 / 配餐 / 储存

点卡片标题 → 该维度随机抽一题
点具体标签 → 精准抽该分类的题

## 启动方式

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

默认端口 5173，后端代理到 8000（见 `vite.config.js`）。
