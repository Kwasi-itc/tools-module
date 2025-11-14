"""Seed data script for Tools Module database.

This script inserts sample tools, roles, permissions, rate limits, and
execution history so the system can be exercised immediately after setup.

Usage:
    python -m app.database.seed_data

The script is idempotent: running it multiple times will not create duplicate
records; it only adds missing entries.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models import (
    ExecutionStatus,
    ParameterType,
    PermissionAction,
    RateLimitScope,
    Role,
    Tool,
    ToolConfig,
    ToolExecution,
    ToolParameter,
    ToolPermission,
    ToolRateLimit,
    ToolType,
)


TOOLS_DATA: List[Dict] = [
    {
        "name": "account_balance_lookup",
        "description": "Fetch sample account profile information from a public placeholder API (JSONPlaceholder)",
        "type": ToolType.HTTP,
        "version": "1.2.0",
        "tool_metadata": {
            "category": "fintech",
            "provider": "JSONPlaceholder",
            "tags": ["accounts", "profile", "customer"],
        },
        "parameters": [
            {
                "name": "account_id",
                "type": "number",
                "required": True,
                "description": "Numeric placeholder user ID (1-10) used by JSONPlaceholder.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "profile",
                "type": "object",
                "required": False,
                "description": "JSONPlaceholder user profile returned by the API.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://jsonplaceholder.typicode.com"},
            {"config_key": "endpoint", "config_value": "/users/{account_id}"},
            {"config_key": "method", "config_value": "GET"},
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 1000, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 30, "time_window_seconds": 60},
        ],
    },
    {
        "name": "initiate_payment",
        "description": "Simulate initiating a payment using the JSONPlaceholder posts endpoint (public dummy API).",
        "type": ToolType.HTTP,
        "version": "2.0.0",
        "tool_metadata": {
            "category": "fintech",
            "provider": "SwiftPay",
            "tags": ["payments", "transfers", "compliance"],
        },
        "parameters": [
            {
                "name": "source_account",
                "type": "string",
                "required": True,
                "description": "Account ID to debit.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "destination_account",
                "type": "string",
                "required": True,
                "description": "Account ID to credit.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "amount",
                "type": "number",
                "required": True,
                "description": "Transfer amount in the specified currency.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "currency",
                "type": "string",
                "required": True,
                "description": "ISO currency code, e.g. USD, EUR.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "payment_id",
                "type": "string",
                "required": False,
                "description": "Unique identifier returned by the payment gateway.",
                "parameter_type": ParameterType.OUTPUT,
            },
            {
                "name": "status",
                "type": "string",
                "required": False,
                "description": "Payment status provided by the gateway.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://jsonplaceholder.typicode.com"},
            {"config_key": "endpoint", "config_value": "/posts"},
            {"config_key": "method", "config_value": "POST"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Content-Type": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.USER, "max_requests": 100, "time_window_seconds": 86400},
            {"scope": RateLimitScope.AGENT, "max_requests": 20, "time_window_seconds": 300},
        ],
    },
    {
        "name": "transaction_insights",
        "description": "Retrieve sample comments data via JSONPlaceholder to simulate transaction insights.",
        "type": ToolType.HTTP,
        "version": "1.4.3",
        "tool_metadata": {
            "category": "analytics",
            "provider": "JSONPlaceholder",
            "tags": ["transactions", "analytics", "sample-data"],
        },
        "parameters": [
            {
                "name": "post_id",
                "type": "number",
                "required": False,
                "default_value": "1",
                "description": "Placeholder post ID to filter comments (1-100).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "comments",
                "type": "object",
                "required": False,
                "description": "List of comments returned by JSONPlaceholder.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://jsonplaceholder.typicode.com"},
            {"config_key": "endpoint", "config_value": "/comments"},
            {"config_key": "method", "config_value": "GET"},
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 2000, "time_window_seconds": 3600},
            {"scope": RateLimitScope.USER, "max_requests": 200, "time_window_seconds": 3600},
        ],
    },
    {
        "name": "web_search",
        "description": "Search the web using Tavily's AI-powered search API with pre-configured authentication. Returns comprehensive, real-time web search results optimized for LLMs. API key is pre-configured, no need to provide it in requests.",
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "utility",
            "provider": "Tavily",
            "tags": ["web", "search", "research", "ai-search"],
        },
        "parameters": [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Search query string to find relevant information on the web.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "auto_parameters",
                "type": "boolean",
                "required": False,
                "default_value": "false",
                "description": "Whether to let Tavily automatically optimize search parameters.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "topic",
                "type": "string",
                "required": False,
                "default_value": "general",
                "description": "Topic category: 'general', 'news', etc.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "search_depth",
                "type": "string",
                "required": False,
                "default_value": "basic",
                "description": "Search depth: 'basic' (faster, fewer results) or 'advanced' (slower, more comprehensive).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "chunks_per_source",
                "type": "number",
                "required": False,
                "default_value": "3",
                "description": "Number of content chunks to extract from each source (default: 3).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "max_results",
                "type": "number",
                "required": False,
                "default_value": "5",
                "description": "Maximum number of search results to return (default: 5, max: 20).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "time_range",
                "type": "string",
                "required": False,
                "description": "Time range filter (e.g., 'day', 'week', 'month', 'year') or null for all time.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "start_date",
                "type": "string",
                "required": False,
                "description": "Start date for search results in YYYY-MM-DD format.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "end_date",
                "type": "string",
                "required": False,
                "description": "End date for search results in YYYY-MM-DD format.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_answer",
                "type": "boolean",
                "required": False,
                "default_value": "true",
                "description": "Whether to include an AI-generated answer in the response.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_raw_content",
                "type": "boolean",
                "required": False,
                "default_value": "false",
                "description": "Whether to include raw HTML content from sources.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_images",
                "type": "boolean",
                "required": False,
                "default_value": "false",
                "description": "Whether to include images in the results.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_image_descriptions",
                "type": "boolean",
                "required": False,
                "default_value": "false",
                "description": "Whether to include AI-generated image descriptions.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_favicon",
                "type": "boolean",
                "required": False,
                "default_value": "false",
                "description": "Whether to include favicon URLs in the results.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_domains",
                "type": "array",
                "required": False,
                "description": "Array of domains to specifically include in search results.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "exclude_domains",
                "type": "array",
                "required": False,
                "description": "Array of domains to exclude from search results.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "country",
                "type": "string",
                "required": False,
                "description": "Country code (ISO 3166-1 alpha-2) to filter results by country.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "results",
                "type": "object",
                "required": False,
                "description": "Search results object containing answer, results array, response_time, and query.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://api.tavily.com"},
            {"config_key": "endpoint", "config_value": "/search"},
            {"config_key": "method", "config_value": "POST"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Content-Type": "application/json"}),
            },
            # Pre-configured API key using auth_type and api_key config
            {
                "config_key": "auth_type",
                "config_value": "bearer_token",
            },
            {
                "config_key": "api_key",
                "config_value": "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",  # Replace with actual API key when seeding
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 1000, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 100, "time_window_seconds": 60},
        ],
    },
    {
        "name": "african_country_directory",
        "description": "Retrieve country profiles for the Africa region using the REST Countries public API.",
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "reference-data",
            "provider": "REST Countries",
            "tags": ["geography", "countries", "africa"],
        },
        "parameters": [
            {
                "name": "region",
                "type": "string",
                "required": True,
                "default_value": "africa",
                "description": "Continent or sub-region supported by REST Countries (default: africa).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "fields",
                "type": "string",
                "required": False,
                "default_value": "name,capital,currencies,population,area,subregion",
                "description": "Comma-delimited list of fields to return from the API.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "countries",
                "type": "array",
                "required": False,
                "description": "List of country objects returned by REST Countries.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://restcountries.com"},
            {"config_key": "endpoint", "config_value": "/v3.1/region/{region}"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
            {
                "config_key": "query_params",
                "config_value": json.dumps({"fields": "name,capital,currencies,population,area,subregion"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 3600, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 120, "time_window_seconds": 300},
        ],
    },
    {
        "name": "earnings_call_transcript_fetcher",
        "description": "Fetch structured earnings call transcripts via the Alpha Vantage API.",
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "finance",
            "provider": "Alpha Vantage",
            "tags": ["earnings", "transcripts", "investor-relations"],
        },
        "parameters": [
            {
                "name": "symbol",
                "type": "string",
                "required": True,
                "default_value": "IBM",
                "description": "Ticker symbol to retrieve the earnings call transcript for (e.g., IBM).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "quarter",
                "type": "string",
                "required": True,
                "default_value": "2024Q1",
                "description": "Fiscal quarter in the format YYYYQ# (e.g., 2024Q1).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "apikey",
                "type": "string",
                "required": False,
                "default_value": "demo",
                "description": "Alpha Vantage API key. Defaults to the public demo key.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "transcript",
                "type": "object",
                "required": False,
                "description": "Structured transcript response including speakers, roles, and sentiment.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://www.alphavantage.co"},
            {"config_key": "endpoint", "config_value": "/query"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "query_params",
                "config_value": json.dumps({"function": "EARNINGS_CALL_TRANSCRIPT"}),
            },
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 15, "time_window_seconds": 60},
        ],
    },
    {
        "name": "bearer_protected_resource_probe",
        "description": "Demonstrate calling a bearer-protected HTTP endpoint with per-call token input.",
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "security",
            "provider": "HTTPBin",
            "tags": ["authentication", "bearer-token", "demo"],
        },
        "parameters": [
            {
                "name": "bearer_token",
                "type": "string",
                "required": True,
                "description": "Bearer token presented on the Authorization header for this request.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "probe_result",
                "type": "object",
                "required": False,
                "description": "HTTPBin bearer endpoint echoing authentication status.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://httpbin.org"},
            {"config_key": "endpoint", "config_value": "/bearer"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
            {
                "config_key": "headers_input_map",
                "config_value": json.dumps(
                    {"bearer_token": {"header": "Authorization", "template": "Bearer {value}"}}
                ),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 1000, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 60, "time_window_seconds": 60},
        ],
    },
]


ROLES_DATA = [
    {
        "name": "fintech-analyst",
        "description": "Analyst focused on financial insights and transaction monitoring.",
    },
    {
        "name": "customer-support",
        "description": "Support agents assisting customers with account queries and payments.",
    },
    {
        "name": "platform-admin",
        "description": "Administrators with full control over tool configuration and permissions.",
    },
]


PERMISSIONS_DATA = [
    {"role": "platform-admin", "tool": "account_balance_lookup", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "initiate_payment", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "transaction_insights", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "web_search", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "african_country_directory", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "earnings_call_transcript_fetcher", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "bearer_protected_resource_probe", "action": PermissionAction.MANAGE},
    {"role": "fintech-analyst", "tool": "transaction_insights", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "account_balance_lookup", "action": PermissionAction.READ},
    {"role": "fintech-analyst", "tool": "web_search", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "african_country_directory", "action": PermissionAction.READ},
    {"role": "fintech-analyst", "tool": "earnings_call_transcript_fetcher", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "bearer_protected_resource_probe", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "account_balance_lookup", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "initiate_payment", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "web_search", "action": PermissionAction.READ},
    {"role": "customer-support", "tool": "african_country_directory", "action": PermissionAction.READ},
    {"role": "customer-support", "tool": "earnings_call_transcript_fetcher", "action": PermissionAction.READ},
    {"role": "customer-support", "tool": "bearer_protected_resource_probe", "action": PermissionAction.READ},
]


EXECUTIONS_DATA = [
    {
        "tool": "account_balance_lookup",
        "agent_id": "agent-neo",
        "role": "customer-support",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"account_id": 3},
        "output_data": {
            "profile": {
                "id": 3,
                "name": "Clementine Bauch",
                "email": "clementine@example.com"
            }
        },
        "execution_time_ms": 220,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=15),
    },
    {
        "tool": "initiate_payment",
        "agent_id": "agent-trinity",
        "role": "customer-support",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {
            "source_account": "ACC123456",
            "destination_account": "ACC987654",
            "amount": 250.0,
            "currency": "USD",
        },
        "output_data": {"payment_id": 101, "status": "created"},
        "execution_time_ms": 540,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=12),
    },
    {
        "tool": "transaction_insights",
        "agent_id": "agent-morpheus",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"post_id": 2},
        "output_data": {
            "comments": [
                {"id": 6, "name": "et fugit eligendi deleniti quidem qui sint nihil autem"},
                {"id": 7, "name": "repellat consequatur praesentium vel minus molestias voluptatum"},
            ]
        },
        "execution_time_ms": 680,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=5),
    },
    {
        "tool": "web_search",
        "agent_id": "agent-oracle",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"query": "latest fintech compliance regulations"},
        "output_data": {
            "results": [
                {"Title": "Fintech Compliance Trends", "FirstURL": "https://duckduckgo.com/Fintech_Compliance"},
                {"Title": "AML Regulations Update", "FirstURL": "https://duckduckgo.com/Anti-money_laundering"},
            ]
        },
        "execution_time_ms": 430,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=2),
    },
    {
        "tool": "african_country_directory",
        "agent_id": "agent-ubuntu",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"region": "africa", "fields": "name,capital,population"},
        "output_data": {
            "countries": [
                {"name": {"common": "Kenya"}, "capital": ["Nairobi"], "population": 47564296},
                {"name": {"common": "Ghana"}, "capital": ["Accra"], "population": 31072945},
            ]
        },
        "execution_time_ms": 510,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=1),
    },
    {
        "tool": "earnings_call_transcript_fetcher",
        "agent_id": "agent-ledger",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"symbol": "IBM", "quarter": "2024Q1", "apikey": "demo"},
        "output_data": {
            "transcript": {
                "symbol": "IBM",
                "quarter": "2024Q1",
                "speakers": [
                    {"speaker": "Arvind Krishna", "title": "CEO", "sentiment": 0.7},
                    {"speaker": "James Kavanaugh", "title": "CFO", "sentiment": 0.5},
                ],
            }
        },
        "execution_time_ms": 620,
        "created_at": datetime.now(timezone.utc) - timedelta(seconds=30),
    },
    {
        "tool": "bearer_protected_resource_probe",
        "agent_id": "agent-shield",
        "role": "platform-admin",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"bearer_token": "sample-token-value"},
        "output_data": {
            "probe_result": {
                "authenticated": True,
                "token": "sample-token-value",
            }
        },
        "execution_time_ms": 190,
        "created_at": datetime.now(timezone.utc) - timedelta(seconds=20),
    },
]


def get_or_create_role(session: Session, name: str, description: str) -> Role:
    role = session.query(Role).filter(Role.name == name).first()
    if role:
        return role

    role = Role(id=uuid4(), name=name, description=description)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


def get_or_create_tool(session: Session, tool_data: Dict) -> Tool:
    tool = session.query(Tool).filter(Tool.name == tool_data["name"]).first()
    if tool:
        return tool

    tool = Tool(
        id=uuid4(),
        name=tool_data["name"],
        description=tool_data.get("description"),
        type=tool_data["type"],
        version=tool_data.get("version", "1.0.0"),
        is_active=True,
        tool_metadata=tool_data.get("tool_metadata"),
    )
    session.add(tool)
    session.commit()
    session.refresh(tool)

    # Parameters
    for param_data in tool_data.get("parameters", []):
        existing = (
            session.query(ToolParameter)
            .filter(
                ToolParameter.tool_id == tool.id,
                ToolParameter.name == param_data["name"],
                ToolParameter.parameter_type == param_data["parameter_type"],
            )
            .first()
        )
        if existing:
            continue

        parameter = ToolParameter(
            id=uuid4(),
            tool_id=tool.id,
            name=param_data["name"],
            type=param_data["type"],
            required=param_data.get("required", False),
            description=param_data.get("description"),
            default_value=param_data.get("default_value"),
            parameter_type=param_data["parameter_type"],
        )
        session.add(parameter)

    # Configs
    for config in tool_data.get("configs", []):
        existing = (
            session.query(ToolConfig)
            .filter(
                ToolConfig.tool_id == tool.id,
                ToolConfig.config_key == config["config_key"],
            )
            .first()
        )
        if existing:
            continue

        session.add(
            ToolConfig(
                id=uuid4(),
                tool_id=tool.id,
                config_key=config["config_key"],
                config_value=config.get("config_value"),
            )
        )

    # Rate limits
    for rl in tool_data.get("rate_limits", []):
        existing = (
            session.query(ToolRateLimit)
            .filter(
                ToolRateLimit.tool_id == tool.id,
                ToolRateLimit.scope == rl["scope"],
            )
            .first()
        )
        if existing:
            continue

        session.add(
            ToolRateLimit(
                id=uuid4(),
                tool_id=tool.id,
                max_requests=rl["max_requests"],
                time_window_seconds=rl["time_window_seconds"],
                scope=rl["scope"],
            )
        )

    session.commit()
    return tool


def ensure_permission(
    session: Session,
    role: Role,
    tool: Tool,
    action: PermissionAction,
    granted: bool = True,
) -> None:
    permission = (
        session.query(ToolPermission)
        .filter(
            ToolPermission.role_id == role.id,
            ToolPermission.tool_id == tool.id,
            ToolPermission.action == action,
        )
        .first()
    )
    if permission:
        permission.granted = granted
    else:
        session.add(
            ToolPermission(
                id=uuid4(),
                tool_id=tool.id,
                role_id=role.id,
                action=action,
                granted=granted,
            )
        )
    session.commit()


def create_execution_history(session: Session, execution_data: Dict, role_map: Dict[str, Role], tool_map: Dict[str, Tool]) -> None:
    tool = tool_map.get(execution_data["tool"])
    role = role_map.get(execution_data["role"])
    if not tool or not role:
        return

    existing = (
        session.query(ToolExecution)
        .filter(
            ToolExecution.tool_id == tool.id,
            ToolExecution.agent_id == execution_data["agent_id"],
            ToolExecution.created_at >= datetime.now(timezone.utc) - timedelta(hours=1),
        )
        .first()
    )
    if existing:
        return

    session.add(
        ToolExecution(
            id=uuid4(),
            tool_id=tool.id,
            agent_id=execution_data["agent_id"],
            role_id=role.id,
            status=execution_data["status"],
            input_data=execution_data.get("input_data"),
            output_data=execution_data.get("output_data"),
            error_message=execution_data.get("error_message"),
            execution_time_ms=execution_data.get("execution_time_ms"),
            created_at=execution_data.get("created_at", datetime.now(timezone.utc)),
        )
    )
    session.commit()


def seed_data(session: Session) -> None:
    # Create tools
    tool_map: Dict[str, Tool] = {}
    for tool_data in TOOLS_DATA:
        tool = get_or_create_tool(session, tool_data)
        tool_map[tool.name] = tool

    # Create roles
    role_map: Dict[str, Role] = {}
    for role_data in ROLES_DATA:
        role = get_or_create_role(session, role_data["name"], role_data["description"])
        role_map[role.name] = role

    # Create permissions
    for perm_data in PERMISSIONS_DATA:
        role = role_map.get(perm_data["role"])
        tool = tool_map.get(perm_data["tool"])
        if role and tool:
            ensure_permission(session, role, tool, perm_data["action"], True)

    # Sample execution history
    for exec_data in EXECUTIONS_DATA:
        create_execution_history(session, exec_data, role_map, tool_map)


def main() -> None:
    session = SessionLocal()
    try:
        seed_data(session)
        print("✅ Sample data inserted successfully.")
    except Exception as exc:  # pragma: no cover - best effort logging
        session.rollback()
        print(f"❌ Failed to insert sample data: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

