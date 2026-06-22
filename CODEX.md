# CODEX.md

Codex collaboration notes for this project.

## How To Work With Codex

Use Codex as a project navigator, runbook executor, and debugging partner. Keep each request small and verifiable:

1. Ask Codex to inspect before changing code.
2. Ask for the exact file and command involved.
3. Ask Codex to explain errors in beginner language.
4. Record every command, result, and fix in `docs/codex-3day-runbook.md`.

Good prompts:

```text
请只检查启动失败原因，不要改代码，告诉我第一个应该修的问题。
```

```text
请根据报错定位是哪一个环境变量/服务没配置，并告诉我如何验证。
```

```text
请帮我把今天跑通的步骤追加整理成简历可描述的项目流程。
```

## Project Positioning

Ragent AI is an enterprise-style multi-agent GraphRAG knowledge-base platform.

Core idea:

```text
document upload
-> document parsing and chunking
-> embedding and vector storage in Milvus
-> entity/relation extraction and graph storage in Neo4j
-> user question
-> LangGraph supervisor routes to workers
-> hybrid retrieval / graph reasoning / web search / data analysis
-> streamed answer with trace
```

## Beginner Learning Rule

Do not try to understand every file first. Learn the project in this order:

1. Run the infrastructure.
2. Start the API.
3. Open the frontend and API docs.
4. Register/login.
5. Upload one small document.
6. Ask one document-related question.
7. Trace the request through the key files.
8. Convert the experience into resume language.

## Key Files

| File | What To Remember |
| --- | --- |
| `start.py` | Starts FastAPI through Uvicorn |
| `backend/api/app.py` | Creates the app, mounts routes and frontend |
| `backend/api/routes.py` | Chat, document upload, sessions, MCP endpoints |
| `backend/auth/routes.py` | Register and login |
| `backend/agent/brain.py` | Conversation storage and streaming entry |
| `backend/agent/orchestrator.py` | LangGraph Supervisor and worker routing |
| `backend/rag/pipeline.py` | RAG retrieve-grade-rewrite flow |
| `backend/rag/utils.py` | Hybrid retrieval, rerank, RRF merge |
| `backend/documents/loader.py` | Document parsing and chunking |
| `backend/milvus/client.py` | Milvus vector database operations |
| `backend/storage/graph_ingestion.py` | Neo4j entity/relation writes |
| `backend/research/routes.py` | Research task API |
| `frontend/index.html` | Main UI |
| `frontend/script.js` | Frontend API calls and SSE handling |

## Resume Focus

Use this project as the upgraded platform project. If compared with Agent1, describe Agent1 as the vertical product-assistant prototype and Agent3 as the platformized multi-agent GraphRAG version.

