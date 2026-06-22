# Ragent

Ragent 是一个面向私有知识库问答和研究报告生成的多智能体 GraphRAG 平台。项目把文档解析、向量检索、知识图谱、多轮对话、人工审核和深度研究流程整合在一起。

## 核心功能

- 文档上传与知识库管理：支持 PDF、Word、Excel、Markdown、图片等文件上传，后台完成解析、分块、向量化和图谱抽取。
- 文档处理进度展示：上传后前端展示排队、解析、切块、向量写入、图谱构建等阶段进度。
- 知识库问答：基于私有文档进行问答，返回答案、检索过程和上下文证据。
- GraphRAG 检索：同时使用 Milvus 向量检索和 Neo4j 图谱关系扩展，提高多跳关系问题的召回能力。
- 多智能体编排：使用 LangGraph 编排 RAG、图谱检索、联网搜索、数据分析、答案综合与校验等节点。
- HITL 人工介入：当检索置信度不足或需要人工确认时，中断流程并等待用户修改问题后继续。
- 深度研究：输入研究主题后自动收集证据、生成结构化研究报告，并支持 Markdown 查看和浏览器打印保存 PDF。
- 用户与会话管理：支持注册登录、JWT 鉴权、历史会话、研究记录与多租户权限隔离。
- 缓存与异步任务：使用 Redis 作为缓存、处理状态存储和文档摄入队列。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3 CDN、原生 HTML/CSS/JavaScript、SSE 流式响应 |
| 后端 | Python 3.12、FastAPI、Uvicorn、Pydantic、SQLAlchemy、Alembic |
| 智能体 | LangGraph、LangChain、OpenAI 兼容模型接口 |
| 模型服务 | DashScope/Qwen，支持 chat、embedding、rerank 配置 |
| 向量数据库 | Milvus 2.5 |
| 图数据库 | Neo4j 5 |
| 关系数据库 | MySQL 8 |
| 缓存/队列 | Redis 7、Redis Streams、arq |
| 文件与多模态 | MinIO、pypdf、docx2txt、unstructured、openpyxl |
| 可观测性 | OpenTelemetry、Prometheus、Grafana、Jaeger |
| 部署 | Docker Compose、本地 Conda/PyCharm 运行 |

## 架构理解

```mermaid
flowchart LR
    User["用户"] --> Frontend["Vue 前端"]
    Frontend --> API["FastAPI 后端"]

    API --> Auth["JWT 鉴权/会话"]
    API --> Agent["LangGraph 多智能体"]
    API --> Upload["文档上传接口"]
    API --> Research["深度研究接口"]

    Upload --> Redis["Redis Streams 队列"]
    Redis --> Worker["文档消费者"]
    Worker --> Parser["解析/分块"]
    Parser --> Milvus["Milvus 向量库"]
    Parser --> Neo4j["Neo4j 知识图谱"]
    Parser --> MySQL["MySQL 文档索引"]

    Agent --> RAG["RAG 检索"]
    RAG --> Milvus
    RAG --> Neo4j
    Agent --> Web["联网搜索/工具调用"]
    Agent --> MySQL

    Research --> Web
    Research --> MySQL
```

一句话理解：用户上传资料后，系统把资料拆成文本块，文本块进 Milvus 做语义检索，实体关系进 Neo4j 做图谱检索，业务数据和会话进 MySQL，处理状态与队列进 Redis；用户提问时，LangGraph 负责调度不同智能体完成检索、推理、校验和回答。

## 项目结构

```text
ragent-main/
├── backend/
│   ├── api/              # FastAPI 应用、聊天、文档、MCP 等接口
│   ├── agent/            # LangGraph 智能体编排、工具、模型路由
│   ├── auth/             # 用户注册、登录、JWT 鉴权
│   ├── documents/        # 文档解析、图片/布局处理、图谱抽取
│   ├── embedding/        # Embedding 服务封装
│   ├── graph/            # 图谱聚类、实体消歧等逻辑
│   ├── milvus/           # Milvus collection 初始化与写入
│   ├── pipeline/         # Redis Streams / arq 文档处理队列
│   ├── rag/              # 混合检索、重排、自动合并、查询改写
│   ├── research/         # 深度研究流程、证据与报告生成
│   └── storage/          # MySQL、Redis、Neo4j、文档生命周期
├── frontend/             # 单页前端界面
├── alembic/              # 数据库迁移
├── config/               # 权重矩阵等配置
├── docs/                 # 运行手册和辅助文档
├── tests/                # 自动化测试
├── docker-compose.yml    # 中间件与完整服务编排
├── start.py              # 本地启动 FastAPI
└── start_worker.py       # arq worker 启动入口
```

## 快速启动

### 1. 准备环境

推荐使用 Conda 环境：

```powershell
conda activate ragent
python --version
```

项目要求 Python 3.12 及以上。你当前 PyCharm 中的解释器可以使用：

```text
D:\App\Anaconda\envs\ragent\python.exe
```

安装依赖：

```powershell
pip install -e .
```

### 2. 启动 Docker 中间件

本地 PyCharm 运行后端时，只需要先启动中间件：

```powershell
docker compose up -d etcd minio standalone mysql redis neo4j
```

常用端口：

| 服务 | 地址 |
| --- | --- |
| FastAPI | http://127.0.0.1:8000 |
| Milvus | 127.0.0.1:19530 |
| Attu 可视化 | http://127.0.0.1:8080，需 `--profile obs` |
| MySQL | 127.0.0.1:3307 |
| Redis | 127.0.0.1:6379 |
| Neo4j Browser | http://127.0.0.1:7474 |
| MinIO Console | http://127.0.0.1:9001 |

查看容器状态：

```powershell
docker compose ps
```

### 3. 配置环境变量

复制示例文件：

```powershell
Copy-Item .env.example .env
```

至少需要配置：

```env
ARK_API_KEY=你的 DashScope API Key
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-plus
EMBEDDER=text-embedding-v1
JWT_SECRET=换成一串足够长的随机字符串
DATABASE_URL=mysql+pymysql://root:password@localhost:3307/agent_chat
REDIS_URL=redis://localhost:6379/0
MILVUS_URI=http://127.0.0.1:19530
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

如果需要深度研究联网搜索，再配置：

```env
TAVILY_API_KEY=你的 Tavily Key
```

注意：`.env` 包含密钥，已被 `.gitignore` 忽略，不要提交到 GitHub。

### 4. 初始化数据库

首次运行前执行迁移：

```powershell
alembic upgrade head
```

如果数据库已经初始化过，可以跳过。

### 5. 启动后端服务

启动 FastAPI：

```powershell
python start.py
```

看到类似下面日志说明后端已启动：

```text
Uvicorn running on http://0.0.0.0:8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

### 6. 启动文档处理消费者

`start.py` 只负责网页、登录、聊天、上传接口等 HTTP 服务。文档上传后的解析、向量化、图谱写入需要消费者进程继续处理。

推荐另开一个 PyCharm Terminal：

```powershell
python -c "from backend.pipeline.stream_consumer import run_stream_consumer; run_stream_consumer()"
```

如果使用 arq worker，可以运行：

```powershell
python start_worker.py
```

本地测试时，最容易理解的方式是开两个窗口：

| 窗口 | 命令 | 作用 |
| --- | --- | --- |
| 后端窗口 | `python start.py` | 提供网页和 API |
| 消费者窗口 | `python -c "from backend.pipeline.stream_consumer import run_stream_consumer; run_stream_consumer()"` | 处理上传文档 |

## 使用流程

1. 注册或登录账号。
2. 进入知识库管理，上传测试文档。
3. 保持消费者窗口运行，等待文档处理进度到完成。
4. 回到对话页，围绕上传内容提问。
5. 点击“查看检索过程”，观察 Dense 检索、图谱检索、重写、HITL 等流程。
6. 进入深度研究，输入研究主题，生成证据和报告。
7. 把关键运行截图、问题排查过程、项目理解记录到学习笔记，用于简历和面试复盘。

## 核心接口

| 接口 | 说明 |
| --- | --- |
| `POST /auth/register` | 用户注册 |
| `POST /auth/token` | 登录并获取 JWT |
| `POST /api/chat/stream` | 流式智能体对话 |
| `POST /api/chat/hitl/resume` | HITL 人工确认后恢复执行 |
| `GET /api/sessions` | 获取历史会话 |
| `POST /api/documents/upload` | 上传文档 |
| `GET /api/documents` | 查看已入库文档 |
| `GET /api/documents/{filename}/processing-status` | 查看文档处理进度 |
| `DELETE /api/documents/{filename}` | 删除文档 |
| `POST /api/research/create` | 创建深度研究任务 |
| `GET /api/research/{execution_id}/report` | 获取研究报告 |
