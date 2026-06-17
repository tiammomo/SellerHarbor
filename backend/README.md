# SellerHarbor Backend

Python backend for SellerHarbor, built with FastAPI, LangChain, and LangGraph.

## Runtime

The generation path is an agent-style graph:

1. `normalize_input`
2. `apply_platform_rule`
3. `extract_facts`
4. `policy_guard`
5. `safe_alternative` when policy blocks first-person or merchant-voice review risk
6. `generate_drafts`
7. `evaluate_and_check_risk`
8. `rewrite_drafts` when quality or risk checks fail, then evaluate once more

The graph keeps the frontend response contract stable while adding trace markers such as `agent.node.rewrite_drafts` and `agent.node.safe_alternative` to `sourceTrace`.

LangChain owns the model-call runnable:

```text
ChatPromptTemplate -> LocalAnthropic Runnable -> JSON parser
```

The local runnable calls the Anthropic-compatible `/v1/messages` endpoint from Claude Code settings, so `mimo-v2.5-pro` is the default model for generation and rewrite nodes.
The default LLM timeout is 180 seconds to leave room for generation plus one automatic rewrite pass.

The LLM defaults to local Claude Code settings:

- `claudeCode.selectedModel`
- `claudeCode.environmentVariables`
- `ANTHROPIC_BASE_URL`
- `ANTHROPIC_AUTH_TOKEN`
- `ANTHROPIC_MODEL`

## Python Package Location

This backend uses `uv` for Python dependency management. On this machine, reusable user-level assets are stored here:

- Package cache: `/home/tiammomo/.cache/uv`
- Managed Python versions: `/home/tiammomo/.local/share/uv/python`

Each project can still keep its own `.venv`, while downloaded wheels and managed Python versions are reused across projects by `uv`.

## Start

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 38081 --reload
```

Health checks:

- `GET /healthz`
- `GET /api/health`
- `GET /api/llm/config`

The API keeps the same frontend contract as before:

- `GET /api/dashboard`
- `GET /api/products`
- `POST /api/products`
- `GET /api/feedback`
- `POST /api/feedback`
- `GET /api/generations`
- `POST /api/generations`
- `GET /api/contents`
- `POST /api/contents/{id}/review`
- `GET /api/rules/platforms`
