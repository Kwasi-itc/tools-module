## Agent Integration API Guide

This reference outlines the HTTP calls an agent or LLM client should make when interacting with the Tools Module. The examples assume the FastAPI service runs locally at `http://localhost:8000` and that you seeded the database with `python -m app.database.seed_data`.

---

### Conventions and Prerequisites
- **Base URL:** `http://localhost:8000/api/v1`
- **Authentication:** Seed endpoints do not require auth. If you add auth later, include the appropriate headers in each call.
- **IDs:** Replace placeholder UUIDs such as `<TOOL_ID>` or `<ROLE_ID>` with values returned from discovery endpoints.
- **Agent identity:** Provide a string `agent_id`. It is recorded with each execution for auditing.

---

### 1. Discover Available Tools

**List Tools**
- **Method / Path:** `GET /tools`
- **Query Params (optional):**
  - `search`, `tool_type`, `is_active`, `page`, `page_size`
- **Expected 200 Response Snapshot:**
  ```json
  {
    "items": [
      {
        "id": "9f4e5b94-4358-4b4a-9e57-83dbdb67eb9e",
        "name": "account_balance_lookup",
        "type": "http",
        "description": "Fetch sample account profile information from a public placeholder API (JSONPlaceholder)",
        "is_active": true,
        "version": "1.2.0"
      }
      // ... more tools
    ],
    "total": 7,
    "page": 1,
    "page_size": 10
  }
  ```

**Get Tool Detail**
- **Method / Path:** `GET /tools/<TOOL_ID>`
- **Purpose:** Obtain parameters, configs, and rate limits for a specific tool.
- **Expected 200 Response Snapshot:**
  ```json
  {
    "id": "9f4e5b94-4358-4b4a-9e57-83dbdb67eb9e",
    "name": "account_balance_lookup",
    "parameters": [
      {
        "name": "account_id",
        "type": "number",
        "required": true,
        "parameter_type": "input"
      },
      {
        "name": "profile",
        "type": "object",
        "required": false,
        "parameter_type": "output"
      }
    ],
    "configs": [
      {"config_key": "base_url", "config_value": "https://jsonplaceholder.typicode.com"},
      {"config_key": "endpoint", "config_value": "/users/{account_id}"},
      {"config_key": "method", "config_value": "GET"}
    ],
    "rate_limits": [
      {"scope": "global", "max_requests": 1000, "time_window_seconds": 3600},
      {"scope": "agent", "max_requests": 30, "time_window_seconds": 60}
    ]
  }
  ```

**Tool Arguments Documentation**
- When calling tools, refer to the `parameters` array in the tool detail response to understand required and optional arguments.
- For database query tools that accept natural language questions, common arguments include:

**Args:**

- `question`: Natural language question (NOT SQL code) - e.g., "What are the top 3 institutions by population?"

- `preferred_visualization`: Preferred way to display the results (auto, table, bar_chart, pie_chart, line_chart, area_chart, text)

**Update Tool Parameter**
- **Method / Path:** `PUT /tools/parameters/<PARAMETER_ID>`
- **Purpose:** Update an existing parameter's properties (name, type, required, description, default_value, parameter_type).
- **Request Body:** All fields are optional - only include fields you want to update:
  ```json
  {
    "name": "updated_param_name",
    "type": "string",
    "required": false,
    "description": "Updated parameter description",
    "default_value": "default_value",
    "parameter_type": "input"
  }
  ```
- **Expected 200 Response Snapshot:**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "tool_id": "9f4e5b94-4358-4b4a-9e57-83dbdb67eb9e",
    "name": "updated_param_name",
    "type": "string",
    "required": false,
    "description": "Updated parameter description",
    "default_value": "default_value",
    "parameter_type": "input"
  }
  ```
- **Note:** You cannot update a parameter to have the same name and parameter_type as another parameter on the same tool.

---

### 2. Resolve Roles and Permissions

**Lookup Tools by Role**
- **Method / Path:** `GET /registry/by-role-name/<ROLE_NAME>`
- **Query Params (optional):** `permission_action`, `page`, `page_size`
- **Purpose:** Fetch all tools a role can access. Use `platform-admin`, `fintech-analyst`, or `customer-support` from the seed data.
- **Expected 200 Response Snapshot:**
  ```json
  {
    "role": {
      "id": "7bdf4c7d-7a75-4a0e-a58d-47c1b5375dfc",
      "name": "platform-admin"
    },
    "items": [
      {
        "tool_id": "9f4e5b94-4358-4b4a-9e57-83dbdb67eb9e",
        "tool_name": "account_balance_lookup",
        "actions": ["manage", "execute", "read"]
      }
      // ... more tools
    ]
  }
  ```

**Check Permission**
- **Method / Path:** `GET /registry/check-permission/<TOOL_ID>/<ROLE_ID>`
- **Query Param (optional):** `required_action` (`execute` by default)
- **Expected 200 Response Snapshot:**
  ```json
  {
    "tool_id": "9f4e5b94-4358-4b4a-9e57-83dbdb67eb9e",
    "role_id": "7bdf4c7d-7a75-4a0e-a58d-47c1b5375dfc",
    "has_permission": true,
    "required_action": "execute"
  }
  ```

---

### 3. Execute a Tool

**Run Tool Execution**
- **Method / Path:** `POST /executions`
- **Request Body Template:**
  ```json
  {
    "tool_id": "<TOOL_ID>",
    "agent_id": "postman-agent",
    "role_id": "<ROLE_ID>",
    "input_data": {}
  }
  ```
- **Fill `input_data` based on the tool definition.** Examples for seeded tools:
  - `account_balance_lookup`: `{"account_id": 3}`
  - `initiate_payment`: `{"source_account": "ACC123456","destination_account": "ACC987654","amount": 250.0,"currency": "USD"}`
  - `transaction_insights`: `{"post_id": 2}`
  - `web_search`: `{"query": "latest fintech compliance regulations"}`
  - `african_country_directory`: `{"region": "africa","fields": "name,capital,population"}`
  - `earnings_call_transcript_fetcher`: `{"symbol": "IBM","quarter": "2024Q1","apikey": "demo"}`
  - `bearer_protected_resource_probe`: `{"bearer_token": "sample-token-value"}`
- **Successful 200 Response Snapshot:**
  ```json
  {
    "id": "f5a7f831-5dbf-4895-8b90-40bfe1a53d10",
    "tool_id": "f2b2c0de-4262-4542-a3c2-5a6a6aa3dd65",
    "agent_id": "postman-agent",
    "role_id": "7bdf4c7d-7a75-4a0e-a58d-47c1b5375dfc",
    "status": "success",
    "input_data": {
      "bearer_token": "sample-token-value"
    },
    "output_data": {
      "probe_result": {
        "authenticated": true,
        "token": "sample-token-value"
      }
    },
    "execution_time_ms": 210,
    "created_at": "2025-11-11T10:35:12.345678",
    "error_message": null
  }
  ```
- **Failure Response:** Returns `status: "failed"` with `error_message` describing the issue (e.g., permission denied, rate limit exceeded, upstream HTTP error).

---

### 4. Inspect Execution History

**List Executions**
- **Method / Path:** `GET /executions`
- **Query Params (optional):** `tool_id`, `agent_id`, `role_id`, `status`, `page`, `page_size`
- **Expected 200 Response Snapshot:**
  ```json
  {
    "items": [
      {
        "id": "f5a7f831-5dbf-4895-8b90-40bfe1a53d10",
        "tool": {
          "id": "f2b2c0de-4262-4542-a3c2-5a6a6aa3dd65",
          "name": "bearer_protected_resource_probe"
        },
        "agent_id": "agent-shield",
        "role_id": "7bdf4c7d-7a75-4a0e-a58d-47c1b5375dfc",
        "status": "success",
        "execution_time_ms": 190,
        "created_at": "2025-11-11T10:34:52.123456"
      }
      // ... more executions
    ],
    "total": 7,
    "page": 1,
    "page_size": 10
  }
  ```

**Get Execution Detail**
- **Method / Path:** `GET /executions/<EXECUTION_ID>`
- **Expected 200 Response Snapshot:** Same structure as the `POST /executions` success payload, including `input_data`, `output_data`, and `error_message`.

**List Executions for a Tool**
- **Method / Path:** `GET /executions/tool/<TOOL_ID>`
- **Purpose:** Quickly browse history for a single tool.

---

### 5. Troubleshooting Responses
- **401/403:** Indicates authentication or permission failures. Confirm the role has at least `execute` permission via `/registry/check-permission`.
- **429:** Rate limit exceeded. Inspect `error_message` for rate limit details and retry after the indicated window.
- **5xx or `status: "failed"` with `error_message`:** The executor caught an exception (network failure, upstream API error, validation issue). Use the message to diagnose, then re-run the tool as needed.

With these endpoints and samples, an agent can discover tools, verify permissions, execute them, and monitor results with predictable request and response shapes.


