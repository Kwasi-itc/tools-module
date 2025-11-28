## Tools Module Overview

This module provides a registry and execution surface for calling external or internal services as “tools.” It is designed so an agent or LLM can discover available capabilities, understand their inputs/outputs, and invoke them safely with auditing, permissions, and rate limits.

---

### Core Concepts

- **Tool** (`app.database.models.Tool`): the canonical record for a capability. Key fields include `name`, `description`, `type` (`http` or `database`), semantic `tool_metadata`, and `is_active`.
- **Parameters** (`ToolParameter`): define structured inputs and outputs. Each parameter has a `parameter_type` of `input` or `output`. Inputs are validated before execution; outputs document expected response shape for agents.
- **Configs** (`ToolConfig`): per-tool key/value data such as endpoints, headers, API keys, or query defaults. They are surfaced to executors at runtime.
- **Rate Limits** (`ToolRateLimit`): optional throttling rules per tool at scopes `global`, `user`, or `agent`.
- **Permissions** (`ToolPermission`): map tools to roles with allowed actions (`read`, `execute`, `manage`). Execution requires `execute` access.
- **Executions** (`ToolExecution`): immutable audit trail for each run, capturing inputs, outputs, errors, and latency.

The module uses SQLAlchemy models stored in PostgreSQL (UUID primary keys), with Pydantic schemas (`app.schemas.tool` and `app.schemas.execution`) for validation at API boundaries.

---

### API Surface

All endpoints live under `/api/v1`. Key categories:

**Tool Registry (`/tools`)**
- `GET /tools`: list tools with pagination (`page`, `page_size`) and filters (`search`, `tool_type`, `is_active`).
- `POST /tools`: create using `ToolCreate`.
- `GET /tools/{tool_id}`: full detail with parameters/configs.
- `PUT /tools/{tool_id}`: update mutable fields (`ToolUpdate`).
- `DELETE /tools/{tool_id}`: soft delete (deactivate) by default; set `hard_delete=true` to remove permanently.

**Tool Parameters (`/tools/{tool_id}/parameters`)**
- `POST`: add a parameter (`ToolParameterCreate`).
- `GET`: list parameters; optional `parameter_type` filter (`input` or `output`).
- `PUT /tools/parameters/{parameter_id}`: update a parameter (`ToolParameterUpdate`).
- `DELETE /tools/parameters/{parameter_id}`: remove a parameter.

**Tool Configs (`/tools/{tool_id}/configs`)**
- `POST`: add or update a config (`ToolConfigCreate`), enforcing uniqueness by `config_key`.
- `GET`: list all configs for the tool.
- `GET /tools/{tool_id}/configs/{config_key}`: fetch a single config.
- `DELETE /tools/{tool_id}/configs/{config_key}`: delete a config entry.

**Registry Discovery (`/registry`)**
- `GET /registry/by-role/{role_id}`: role-scoped discovery. Requires `role_id`, optional `permission_action` (default `read`), `page`, `page_size`. Uses `ToolRegistryService.get_tools_by_role`.
- `GET /registry/by-role-name/{role_name}`: same as above but resolves role by name.
- `GET /registry/check-permission/{tool_id}/{role_id}`: boolean check for whether a role has at least the supplied `required_action` (defaults to `execute`).

**Executions (`/executions`)**
- `POST /executions`: run a tool via `ExecutionRequest` (tool ID, agent ID, role ID, `input_data`).
- `GET /executions`: list executions with filters (`tool_id`, `agent_id`, `role_id`, `status`) plus pagination.
- `GET /executions/{execution_id}`: retrieve details for a single run.
- `GET /executions/tool/{tool_id}`: shortcut to list executions for one tool.

All endpoints require valid permission scopes enforced by `PermissionService.check_tool_permission`.

---

### Execution Flow for Agents / LLMs

1. **Discover tools**: call `GET /tools` (optionally filtered by metadata). Use descriptions, parameters, and configs to decide applicability.
2. **Read schema**: inspect the `parameters` array (name, type, required, description) and `configs` to construct the correct payload.
3. **Prepare inputs**: build `input_data` in the agent’s request. Only supply keys marked as `input`. Outputs are informational.
4. **Submit execution**: call `POST /executions` with the agent’s `agent_id`, `role_id`, target `tool_id`, and `input_data`.
5. **Handle response**:
   - On success, `output_data` contains executor results (HTTP response JSON, rows from database, etc.).
   - On failure, `status` becomes `failed` with an `error_message`. The execution record persists for audits.

Execution automatically:

- Verifies the tool is active.
- Checks rate limits (`RateLimitService.check_rate_limit`).
- Validates permissions against the supplied `role_id`.
- Records metrics (`execution_time_ms`, optional `cost` field).
- Increments rate-limit counters post-execution.

---

### HTTP Tools Runtime Behavior

`app.executors.http_executor.HTTPExecutor` is the default runtime for tools with `type="http"`. It translates persisted configs and per-call inputs into outgoing HTTP requests.

**1. Collect configs and inputs**
- `ToolConfig` entries are materialized into a `configs` dict (e.g., `base_url`, `endpoint`, `method`, `headers`, `query_params`, `headers_input_map`).
- `input_data` from the execution request is copied so path/header substitutions can remove values before they become query/body parameters.

**2. Build URL**
- `base_url` + `endpoint` define the target. If `endpoint` is absolute it overrides `base_url`.
- Path templating uses Python’s `Formatter`: placeholders like `/region/{region}` are extracted and replaced with values from `input_data`. Missing placeholders raise a descriptive error.

**3. Assemble headers**
- Static headers: the `headers` config stores a JSON object string (e.g., `{"Accept":"application/json"}`).
- Credential configs: the executor interprets common patterns:
  - `auth_type="bearer_token"` + `api_key` config → `Authorization: Bearer <token>`.
  - `auth_type="api_key"` + `api_key_header` + `api_key` → header injection under that key.
  - `auth_type="basic_auth"` + `username` + `password` → base64-encoded `Authorization: Basic ...`.
- Runtime credential inputs: the optional `headers_input_map` config lets you inject per-call values directly into headers. It takes a JSON object mapping input keys to either header names or `{header, template}` objects. Example:
  ```json
  {
    "bearer_token": {
      "header": "Authorization",
      "template": "Bearer {value}"
    },
    "x_api_key": "X-API-Key"
  }
  ```
  During execution, if `input_data` contains `bearer_token`, the executor sets the header to `Bearer …` and removes `bearer_token` from the payload. The same pattern applies for any arbitrary header key/value.

**4. Merge query parameters and body**
- `query_params` config (if present) should be a JSON object string. It becomes the default query param set.
- Remaining `input_data` entries (after path/header extraction) are merged:
  - For `GET`/`DELETE`, they become query parameters alongside `query_params`.
  - For `POST`/`PUT`/`PATCH`, they become the request body. If `Content-Type` is `application/json`, the executor uses `client.request(..., json=…)`; otherwise it falls back to form data.

**5. Execute and parse**
- Uses `httpx.AsyncClient` with `follow_redirects=True`.
- Captures status, attempts to decode JSON (falls back to raw text), and returns a dict with `status_code`, `data`, and `headers`.
- Timeout defaults to `settings.default_execution_timeout_seconds`.

**Credential patterns recap**
- **Pre-configured secrets**: store API keys or tokens in `ToolConfig` (`api_key`, `auth_type`, etc.). The executor pulls them automatically; agents do not need to supply these values.
- **Per-call secrets**: declare input parameters (e.g., `api_token`), then map them into headers via `headers_input_map`. After header injection the values are removed from the payload, so they aren’t logged in query strings or bodies.
- **Mixed approach**: combine configs (e.g., static base URL, method, default query params) with per-execution credentials. This is useful when agents authenticate on behalf of end-users.

The executor is intentionally declarative: changes happen by adjusting tool configs, not code. Adding other transport types (SOAP, gRPC, database) involves implementing parallel executors and extending `ToolType`.

---

### Sample Seed Tools

When you run `python -m app.database.seed_data`, the script populates a sample catalog (see `app/database/seed_data.py`):

- `earnings_call_transcript_fetcher`: calls the Alpha Vantage transcript API. Requires `symbol`, `quarter`, and optional `apikey` inputs.
- `african_country_directory`: hits REST Countries with a templated region endpoint.
- `bearer_protected_resource_probe`: demonstrates runtime bearer tokens passed as inputs and mapped into the Authorization header.
- `account_balance_lookup`, `initiate_payment`, and `transaction_insights`: placeholder finance utilities backed by JSONPlaceholder.

Each tool in the seed data comes with parameters, configs, rate limits, permissions, and sample execution history—handy for demos and integration tests.

---

### Roles, Permissions, and Rate Limits

- **Roles**: created in `ToolRegistryService` or via seed data (e.g. `platform-admin`, `fintech-analyst`). Agents call executions with their `role_id`.
- **Permission hierarchy**: `manage` > `execute` > `read`. Execution requires at least `execute`.
- **Rate limits**: enforced at runtime. If violated, execution returns an error prior to contacting the external service.

Agents should surface permission/rate-limit errors back to users with helpful messaging.

---

### Operational Guidance

- **Configuration management**: long-lived secrets can live in configs, but when you need per-call secrets (rotate frequently or user-scoped) use input parameters with `headers_input_map`.
- **Versioning**: `Tool.version` enables semantic tracking. Update when contracts change; consider storing changelog metadata in `tool_metadata`.
- **Deactivation**: set `is_active` to false (via update/delete endpoint) to disable a tool without removing historical executions.
- **Auditing**: rely on `ToolExecution` records to reconstruct agent actions. The API already returns `tool_name` alongside the execution record for readability.

---

### Getting Started Quickly

1. Install dependencies (`pip install -r requirements.txt`) and configure the database connection in `app/config.py`.
2. Apply migrations / run Alembic if needed.
3. Populate sample data: `python -m app.database.seed_data`.
4. Start the FastAPI app (e.g. `uvicorn app.main:app --reload`).
5. Inspect `/docs` (Swagger UI) to experiment with the tool and execution endpoints.
6. wire your agent or LLM client to:
   - Fetch `/tools` for discovery.
   - Persist available tool schemas locally or update on demand.
   - Issue `POST /executions` calls as needed, handling success and error responses.

With this workflow, an LLM can reason about available tools, validate required fields, and invoke them compliantly within organizational guardrails.

