# Ragent AI 3-Day Runbook

This file is your running diary. Fill it while operating the project.

## Goal

In about 3 days, be able to:

- Run the project locally.
- Explain the core workflow from upload to answer.
- Know the key files and services.
- Describe the project clearly on a resume.
- Answer basic interview questions without memorizing every implementation detail.

## Mental Model

Remember this one sentence first:

```text
Ragent AI = FastAPI backend + Vue CDN frontend + LangGraph multi-agent orchestration + Milvus vector retrieval + Neo4j knowledge graph + MySQL/Redis persistence.
```

Main workflow:

```text
Upload document
-> parse and chunk
-> write vectors to Milvus
-> extract entities/relations to Neo4j
-> ask a question
-> Supervisor chooses worker agents
-> retrieve / graph search / web search / data analysis
-> stream answer to frontend
```

## Day 1: Run It

### Target

Get the infrastructure and API running. Do not try to understand all code yet.

### Checklist

- [ ] Confirm Docker Desktop is running.
- [ ] Create `.env` from `.env.example`.
- [ ] Add required environment variables.
- [ ] Start Docker services.
- [ ] Create or verify Python environment.
- [ ] Install dependencies.
- [ ] Start API.
- [ ] Open frontend.
- [ ] Open API docs.
- [ ] Register/login once.

### Required `.env` Notes

For local Python + Docker services, MySQL should use port `3307`:

```env
ARK_API_KEY=your_dashscope_key
JWT_SECRET=replace_with_a_long_random_string
DATABASE_URL=mysql+pymysql://root:password@localhost:3307/agent_chat
REDIS_URL=redis://localhost:6379/0
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Commands

```powershell
cd D:\App\Codex\workspaces\Agent3\ragent-main
copy .env.example .env
docker compose up -d
docker compose ps
D:\App\Anaconda\python.exe -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .
python start.py
```

### Record

Date: 2026-06-19

What worked:

- Docker Desktop started successfully.
- Docker Compose infrastructure services started:
  - MySQL on host port `3307`
  - Redis on `6379`
  - Milvus on `19530`
  - MinIO on `9000/9001`
  - Neo4j on `7474/7687`
- Neo4j showed `unhealthy` in `docker compose ps`, but `cypher-shell` query succeeded, so it was usable.
- `.env` was created and confirmed ignored by git.
- Conda environment `D:\App\Anaconda\envs\ragent\python.exe` worked with Python 3.12.13.
- Project dependencies were installed into the Conda `ragent` environment.
- FastAPI app imported successfully.
- Backend started successfully from PyCharm using `start.py`.
- Frontend `/`, Swagger `/docs`, and `/openapi.json` all returned HTTP 200.
- Registered a test user and logged in successfully.
- Authenticated `/sessions` request returned `{"sessions":[]}`.

What failed:

- `pip install -e .` initially failed because setuptools found multiple top-level folders.
- `pip install -e .` then failed because `redis>=7.4.0` conflicted with `arq`, which requires Python `redis<6`.
- FastAPI app import crashed because `pyarrow 24.0.0` caused a Windows access violation.
- `/auth/register` initially returned HTTP 500 because `bcrypt 5.0.0` was incompatible with `passlib 1.7.4`.
- Codex PowerShell background launch was unreliable because the shell environment had duplicated `Path/PATH` keys. PyCharm was used to run the backend instead.

Error message:

- `Multiple top-level packages discovered in a flat-layout`
- `ResolutionImpossible` for `redis>=7.4.0` and `arq`
- `Windows fatal exception: access violation` from `pyarrow`
- `module 'bcrypt' has no attribute '__about__'`
- `ValueError: password cannot be longer than 72 bytes`

Fix:

- Added setuptools package discovery to `pyproject.toml`:
  - `include = ["backend", "backend.*"]`
- Changed Python Redis client dependency to:
  - `redis>=5.0,<6.0`
- Downgraded `pyarrow`:
  - `pyarrow==22.0.0`
- Added bcrypt constraint and installed compatible version:
  - `bcrypt>=4.0,<5.0`
  - installed `bcrypt 4.3.0`
- Used PyCharm to run `start.py` with the configured Conda `ragent` interpreter.

Screenshot or page opened:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

Test account:

```text
username: day1_user_215801
password: Day1Test123456
tenant: day1_org
role: admin
```

## Day 2: Run One Full Business Flow

### Target

Upload one small file, ask a question, and understand the main request path.

### Checklist

- [ ] Prepare one small Markdown or PDF file.
- [ ] Upload it from the frontend.
- [ ] Confirm document list shows it.
- [ ] Ask one question about the document.
- [ ] Watch streaming answer and trace events.
- [ ] Open Swagger docs and identify related endpoints.
- [ ] Read the key files for this path.

### Files To Read

| Step | File |
| --- | --- |
| App startup | `backend/api/app.py` |
| Upload endpoint | `backend/api/routes.py` |
| Document parsing | `backend/documents/loader.py` |
| Embedding | `backend/embedding/service.py` |
| Milvus write/search | `backend/milvus/client.py`, `backend/milvus/writer.py` |
| Chat streaming | `backend/agent/brain.py` |
| Agent routing | `backend/agent/orchestrator.py` |
| RAG pipeline | `backend/rag/pipeline.py`, `backend/rag/utils.py` |
| Frontend calls | `frontend/script.js` |

### Record

Uploaded file:

Question asked:

Answer summary:

Which services were used:

Which files I understood:

One sentence explanation:

## Day 3: Convert To Resume And Interview Story

### Target

Be able to explain the project in 1 minute, 3 minutes, and resume bullet form.

### 1-Minute Version

```text
Ragent AI 是一个企业级多智能体 GraphRAG 知识库平台。我负责/学习跑通了文档上传、解析切片、Milvus 向量检索、Neo4j 知识图谱、LangGraph 多智能体路由和 FastAPI 流式问答流程。用户上传资料后，系统会把文本写入向量库，把实体关系写入图数据库；用户提问时，Supervisor 会根据问题类型调度 RAG、图谱检索、网页搜索或数据分析 Agent，最后通过 SSE 流式返回答案。
```

### Resume Draft

```text
企业级多智能体 GraphRAG 知识库平台
- 基于 FastAPI + LangGraph 构建 Supervisor-Workers 多智能体问答架构，支持 RAG 检索、图谱检索、联网搜索、数据分析等多路能力调度。
- 设计文档摄入链路，支持 PDF/Word/Excel/Markdown 等资料解析、层级切片、Qwen Embedding 向量化，并写入 Milvus 进行混合检索。
- 集成 Neo4j 构建知识图谱，抽取文档实体关系，支持局部图谱扩展、多跳关系推理和 GraphRAG 增强回答。
- 实现 JWT 登录、多租户数据隔离、Redis 缓存/限流、MySQL 会话持久化，并接入 Prometheus/Grafana/Jaeger 可观测能力。
- 前端基于 Vue 3 CDN 实现文档上传、流式问答、研究任务进度和历史记录展示。
```

### Interview Questions To Practice

1. 这个项目解决了什么问题？
2. 为什么需要 RAG？
3. Milvus 在项目里做什么？
4. Neo4j 在项目里做什么？
5. LangGraph 的 Supervisor-Workers 是什么？
6. 用户上传文档后发生了什么？
7. 用户提问后请求怎么流转？
8. Redis 和 MySQL 分别负责什么？
9. Agent1 和 Agent3 的区别是什么？
10. 你在项目里最大的收获是什么？

### Record

Final project summary:

My resume version:

Questions I can answer:

Questions I still cannot answer:

## Memory Method

Use the "5 boxes" method:

```text
入口层: frontend + FastAPI
智能层: LangGraph + agents
检索层: RAG + Milvus + BM25 + rerank
图谱层: Neo4j + entities + relations
支撑层: MySQL + Redis + Docker + monitoring
```

When confused, map every file into one of these boxes.
