"""Seed data script for the Tools Module database.

This script inserts sample tools (web search, T-bill calculator, FX rates, loan repayment
calculator, and Chango API endpoints), the core roles, their permissions, and a bit of
execution history so the system can be exercised immediately after setup.
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
        "name": "web_search",
        "description": "Search the web using Tavily's AI-powered search API with pre-configured authentication. Returns comprehensive, real-time web search results optimized for LLMs. API key is pre-configured, so requests do not need to supply credentials.",
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
                "name": "results",
                "type": "object",
                "required": False,
                "description": "Search results object containing answer, results array, response_time, and query.",
                "parameter_type": ParameterType.OUTPUT,
            }
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://api.tavily.com"},
            {"config_key": "endpoint", "config_value": "/search"},
            {"config_key": "method", "config_value": "POST"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Content-Type": "application/json"}),
            },
            {"config_key": "auth_type", "config_value": "bearer_token"},
            {
                "config_key": "api_key",
                "config_value": "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",
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 1000, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 100, "time_window_seconds": 60},
        ],
    },
    {
        "name": "ghana_financial_metrics_search",
        "description": (
            "Targeted search for Ghana-focused macroeconomic and banking metrics from trusted official sources. "
            "Use it to pull GDP updates, Bank of Ghana reference rate notices, Ghana Statistical Service indicators, average "
            "lending/savings rates, and fixed deposit tables from regulators and licensed banks. By default it biases toward "
            "BoG, GSS, SEC, GSE, and major bank domains."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "research",
            "provider": "Tavily",
            "tags": ["ghana", "finance", "macro", "rates", "search"],
        },
        "parameters": [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": (
                    "Financial research question focused on Ghana. Use specific queries targeting official sources: "
                    "'Bank of Ghana reference rate', 'Ghana Statistical Service GDP Q3 2024', 'Standard Chartered fixed deposit rates'. "
                ),
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "search_depth",
                "type": "string",
                "required": False,
                "default_value": "advanced",
                "description": "basic or advanced. Advanced is recommended for regulatory circulars and bank disclosures.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_domains",
                "type": "array",
                "required": False,
                "default_value": json.dumps([
                    "https://www.bog.gov.gh",
                    "https://www.statsghana.gov.gh",
                    "https://www.absa.com.gh",
                    "http://www.ecobank.com",
                    "https://www.gcbbank.com.gh",
                    "http://www.calbank.net",
                    "https://www.sc.com/gh",
                    "https://www.stanbicbank.com.gh",
                    "https://www.firstnationalbank.com.gh",
                    "https://www.fidelitybank.com.gh",
                    "https://www.gtbghana.com",
                    "https://www.zenithbank.com.gh",
                    "https://cbg.com.gh",
                    "https://www.gab.com.gh",
                    "http://www.agricbank.com",
                    "http://www.ghana.accessbankplc.com",
                    "http://www.boaghana.com",
                    "http://www.firstatlanticbank.com.gh",
                    "http://www.fbnbankghana.com",
                    "http://www.nib-ghana.com",
                    "https://www.omnibsic.com.gh",
                    "http://www.prudentialbank.com.gh",
                    "http://www.republicghana.com",
                    "http://www.societegenerale.com.gh",
                    "http://www.ubagroup.com",
                    "http://www.myumbbank.com"
                ]),
                "description": (
                    "Optional override list of trusted domains. Defaults to Ghana's regulators and licensed banks; supply "
                    "your own list to extend or replace the built-in allowlist."
                ),
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "country",
                "type": "string",
                "required": False,
                "default_value": "ghana",
                "description": "Country bias for search results. Defaults to Ghana to keep results Ghana-specific.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "include_answer",
                "type": "string",
                "required": False,
                "default_value": "advanced",
                "description": (
                    "Include an LLM-generated answer to the provided query. Set to 'basic' or 'true' for a quick answer, "
                    "'advanced' for a more detailed answer, or 'false' to exclude the answer. Defaults to 'advanced' for "
                    "comprehensive financial insights."
                ),
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "max_results",
                "type": "number",
                "required": False,
                "default_value": "2",
                "description": "Maximum number of search results to return. Defaults to 2 to keep responses focused.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "results",
                "type": "object",
                "required": False,
                "description": "Structured search response containing summarized answer and source snippets.",
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
            {"config_key": "auth_type", "config_value": "bearer_token"},
            {
                "config_key": "api_key",
                "config_value": "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",
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 800, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 80, "time_window_seconds": 60},
        ],
    },
    {
        "name": "ghana_tbill_calculator",
        "description": (
            "Project Ghana Treasury bill returns using the Bank of Ghana discount methodology. Provide an investment amount, "
            "tenor (91/182/364), and the discount rate from the weekly auction sheet to instantly compute the face value, "
            "interest earned, maturity date, and annualized yield. Use this tool when advising customers, validating bids, "
            "or comparing yields across instruments before settlement. Dates default to the current auction if not provided."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "treasury",
            "provider": "Ghana Treasury Sandbox",
            "tags": ["treasury", "finance", "t-bills", "ghana"],
        },
        "parameters": [
            {
                "name": "investmentAmount",
                "type": "number",
                "required": True,
                "description": "Cash you plan to invest in GHS (purchase price).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "tenor",
                "type": "number",
                "required": True,
                "description": "Tenor in days. Allowed values: 91, 182, 364.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "discountRate",
                "type": "number",
                "required": True,
                "description": "Annual discount rate in percent (e.g., 26.5).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "issueDate",
                "type": "string",
                "required": False,
                "description": "Auction settlement date in YYYY-MM-DD format (defaults to today).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "projection",
                "type": "object",
                "required": False,
                "description": "Projection payload returned by the calculator API.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/treasury/tbills/calculate"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 60, "time_window_seconds": 60},
        ],
    },
    {
        "name": "fx_exchange_rate",
        "description": (
            "Retrieve the latest exchange rate between two currencies and optionally return a converted amount. "
            "Perfect for cross-currency quotes, remittance checks, or pricing international transfers in real time. "
            "Supports Bank of Ghana reference rates along with common global crosses. Available currency codes: "
            "GHS (Ghana), USD (United States), EUR (Euro), NGN (Nigeria), GBP (United Kingdom)."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "treasury",
            "provider": "Ghana Treasury Sandbox",
            "tags": ["fx", "exchange-rate", "ghanacedi", "payments"],
        },
        "parameters": [
            {
                "name": "from",
                "type": "string",
                "required": True,
                "description": "Base currency code (e.g., GHS).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "to",
                "type": "string",
                "required": True,
                "description": "Quote currency code (e.g., USD).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "amount",
                "type": "number",
                "required": False,
                "default_value": "1",
                "description": "Amount to convert (defaults to 1).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "rate_payload",
                "type": "object",
                "required": False,
                "description": "API response containing rate, converted amount, source, and timestamps.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/fx/exchange-rate"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 800, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 80, "time_window_seconds": 60},
        ],
    },
    {
        "name": "loan_repayment_calculator",
        "description": (
            "Instantly model amortized loan repayments for Ghana-cedi facilities. Supply principal, annual percentage rate, "
            "tenure (up to 30 years), and optional extra principal top-ups to receive the monthly installment, total interest, "
            "payoff timeline, and a month-by-month amortization schedule. Ideal for contact center agents who need to compare "
            "installment plans, show the impact of overpayments, or answer payoff-date questions before a formal application."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "lending",
            "provider": "Ghana Treasury Sandbox",
            "tags": ["loans", "repayments", "amortization", "finance"],
        },
        "parameters": [
            {
                "name": "principal",
                "type": "number",
                "required": True,
                "description": "Loan amount in GHS.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "annualRate",
                "type": "number",
                "required": True,
                "description": "Annual interest rate (percentage).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "termMonths",
                "type": "number",
                "required": True,
                "description": "Loan tenure in months (1-360).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "startDate",
                "type": "string",
                "required": False,
                "description": "Disbursement date YYYY-MM-DD (defaults to today).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "extraPayment",
                "type": "number",
                "required": False,
                "default_value": "0",
                "description": "Additional principal paid every month (defaults to 0).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "projection",
                "type": "object",
                "required": False,
                "description": "Loan repayment projection including payments, payoff date, and amortization schedule.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/loans/repayments/calculate"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 600, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 60, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_auth_signup",
        "description": (
            "Create a new user account and send OTP. Register a new user with email, phone number, and password. "
            "An OTP will be sent to the phone number. For dummy implementation, the OTP is returned in the response."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "authentication",
            "provider": "Chango API",
            "tags": ["auth", "signup", "user-registration", "otp"],
        },
        "parameters": [
            {
                "name": "email",
                "type": "string",
                "required": True,
                "description": "User's email address.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "phoneNumber",
                "type": "string",
                "required": True,
                "description": "User's phone number.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "password",
                "type": "string",
                "required": True,
                "description": "User's password.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": "Response containing user ID, email, phone number, status, and OTP code (for dummy implementation).",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/auth/signup"},
            {"config_key": "method", "config_value": "POST"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Content-Type": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 200, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 20, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_auth_verify_otp",
        "description": (
            "Verify OTP code sent to user's phone number during signup. Completes the user registration process."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "authentication",
            "provider": "Chango API",
            "tags": ["auth", "otp", "verification", "user-registration"],
        },
        "parameters": [
            {
                "name": "phoneNumber",
                "type": "string",
                "required": True,
                "description": "Phone number that received the OTP.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "otp",
                "type": "string",
                "required": True,
                "description": "OTP code to verify.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": "Response containing verification status and user details.",
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/auth/verify-otp"},
            {"config_key": "method", "config_value": "POST"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Content-Type": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 300, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 30, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_groups",
        "description": (
            "Get all groups for the authenticated user. Bearer token may be provided but is not required "
            "(dummy implementation - returns all groups)."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "groups",
            "provider": "Chango API",
            "tags": ["groups", "list", "user-data"],
        },
        "parameters": [
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": (
                    "Array of all groups with details including group name, country, description, "
                    "cashout policy, member count, status, and creation date."
                ),
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/groups"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 50, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_campaigns_group",
        "description": (
            "Get all campaigns for a specific group. Bearer token may be provided but is not required "
            "(dummy implementation)."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "campaigns",
            "provider": "Chango API",
            "tags": ["campaigns", "groups", "list"],
        },
        "parameters": [
            {
                "name": "groupName",
                "type": "string",
                "required": True,
                "description": "Name of the group to get campaigns for.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": (
                    "Array of campaigns for the specified group, including campaign name, type, details, "
                    "end date, target amount, and status."
                ),
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/campaigns/group"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 50, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_wallets",
        "description": (
            "Get all wallets for the authenticated user. Bearer token may be provided but is not required "
            "(dummy implementation - returns all wallets). Card numbers are masked in the response."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "wallets",
            "provider": "Chango API",
            "tags": ["wallets", "list", "user-data", "cards"],
        },
        "parameters": [
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": (
                    "Array of all wallets with details including wallet type, country, network/account/card "
                    "information (masked for security), and status."
                ),
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/wallets"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 50, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_contributions",
        "description": (
            "Get all contributions. Can filter by groupName and/or campaignName. Bearer token may be provided "
            "but is not required (dummy implementation - returns all contributions)."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "contributions",
            "provider": "Chango API",
            "tags": ["contributions", "list", "filter", "campaigns", "groups"],
        },
        "parameters": [
            {
                "name": "groupName",
                "type": "string",
                "required": False,
                "description": "Filter by group name.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "campaignName",
                "type": "string",
                "required": False,
                "description": "Filter by campaign name (can be used with groupName).",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": (
                    "Array of contributions with details including contribution type, amount, wallet ID, "
                    "anonymous status, recurring status, on-behalf information, and status."
                ),
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/contributions"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 50, "time_window_seconds": 60},
        ],
    },
    {
        "name": "chango_cashout",
        "description": (
            "Get all cashouts. Can filter by campaignName. Bearer token may be provided but is not required "
            "(dummy implementation - returns all cashouts)."
        ),
        "type": ToolType.HTTP,
        "version": "1.0.0",
        "tool_metadata": {
            "category": "cashouts",
            "provider": "Chango API",
            "tags": ["cashouts", "list", "filter", "campaigns"],
        },
        "parameters": [
            {
                "name": "campaignName",
                "type": "string",
                "required": False,
                "description": "Filter by campaign name.",
                "parameter_type": ParameterType.INPUT,
            },
            {
                "name": "response",
                "type": "object",
                "required": False,
                "description": (
                    "Array of cashouts with details including campaign name, amount, reason, cashout type, "
                    "recipient phone number, wallet ID, and status."
                ),
                "parameter_type": ParameterType.OUTPUT,
            },
        ],
        "configs": [
            {"config_key": "base_url", "config_value": "https://mydummyapi.onrender.com"},
            {"config_key": "endpoint", "config_value": "/chango/cashout"},
            {"config_key": "method", "config_value": "GET"},
            {
                "config_key": "headers",
                "config_value": json.dumps({"Accept": "application/json"}),
            },
        ],
        "rate_limits": [
            {"scope": RateLimitScope.GLOBAL, "max_requests": 500, "time_window_seconds": 3600},
            {"scope": RateLimitScope.AGENT, "max_requests": 50, "time_window_seconds": 60},
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
    {"role": "platform-admin", "tool": "web_search", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "ghana_financial_metrics_search", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "ghana_tbill_calculator", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "fx_exchange_rate", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "loan_repayment_calculator", "action": PermissionAction.MANAGE},
    {"role": "fintech-analyst", "tool": "web_search", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "ghana_financial_metrics_search", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "ghana_tbill_calculator", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "fx_exchange_rate", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "loan_repayment_calculator", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "web_search", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "ghana_financial_metrics_search", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "ghana_tbill_calculator", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "fx_exchange_rate", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "loan_repayment_calculator", "action": PermissionAction.EXECUTE},
    {"role": "platform-admin", "tool": "chango_auth_signup", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_auth_verify_otp", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_groups", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_campaigns_group", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_wallets", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_contributions", "action": PermissionAction.MANAGE},
    {"role": "platform-admin", "tool": "chango_cashout", "action": PermissionAction.MANAGE},
    {"role": "fintech-analyst", "tool": "chango_auth_signup", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_auth_verify_otp", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_groups", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_campaigns_group", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_wallets", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_contributions", "action": PermissionAction.EXECUTE},
    {"role": "fintech-analyst", "tool": "chango_cashout", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_auth_signup", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_auth_verify_otp", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_groups", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_campaigns_group", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_wallets", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_contributions", "action": PermissionAction.EXECUTE},
    {"role": "customer-support", "tool": "chango_cashout", "action": PermissionAction.EXECUTE},
]


EXECUTIONS_DATA = [
    {
        "tool": "web_search",
        "agent_id": "agent-oracle",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"query": "latest fintech compliance regulations"},
        "output_data": {
            "results": [
                {
                    "title": "Fintech Compliance Trends",
                    "url": "https://research.example.com/fintech-compliance-trends",
                },
                {
                    "title": "AML Regulations Update",
                    "url": "https://regulators.example.com/aml-update",
                },
            ]
        },
        "execution_time_ms": 430,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=2),
    },
    {
        "tool": "ghana_financial_metrics_search",
        "agent_id": "agent-akua",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {
            "query": "latest Bank of Ghana reference rate and average lending rate",
            "search_depth": "advanced",
            "country": "GH",
            "include_domains": ["bog.gov.gh", "gss.gov.gh"]
        },
        "output_data": {
            "results": {
                "answer": "The Bank of Ghana reference rate for July 2024 remains 29.95%, with average commercial lending rates ranging 33-36% across tier-1 banks.",
                "response_time": 612,
                "query": "latest Bank of Ghana reference rate and average lending rate",
                "results": [
                    {
                        "title": "BoG Reference Rate Update - July 2024",
                        "url": "https://www.bog.gov.gh/monetary-policy/reference-rate-july-2024"
                    },
                    {
                        "title": "Bank Lending Rates Summary - Ghana Statistical Service",
                        "url": "https://statsghana.gov.gh/lending-rates-summary"
                    }
                ]
            }
        },
        "execution_time_ms": 610,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=3),
    },
    {
        "tool": "ghana_tbill_calculator",
        "agent_id": "agent-yaw",
        "role": "customer-support",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {
            "investmentAmount": 10000,
            "tenor": 91,
            "discountRate": 26.5,
            "issueDate": "2024-02-01",
        },
        "output_data": {
            "projection": {
                "status": "success",
                "data": {
                    "investmentAmount": 10000,
                    "tenorDays": 91,
                    "discountRate": 26.5,
                    "discountFactor": 0.9339,
                    "faceValue": 10708.96,
                    "interestEarned": 708.96,
                    "annualizedYield": 27.74,
                    "issueDate": "2024-02-01T00:00:00.000Z",
                    "maturityDate": "2024-05-02T00:00:00.000Z",
                    "summary": "Invest GHS 10000 to receive GHS 10708.96 at maturity.",
                },
                "message": "Treasury bill projection generated",
                "timestamp": "2024-02-01T10:00:00Z",
                "requestId": "req-1234567890-abc123",
            }
        },
        "execution_time_ms": 520,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=1),
    },
    {
        "tool": "fx_exchange_rate",
        "agent_id": "agent-abbey",
        "role": "fintech-analyst",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {"from": "GHS", "to": "USD", "amount": 100},
        "output_data": {
            "rate_payload": {
                "status": "success",
                "data": {
                    "from": "GHS",
                    "to": "USD",
                    "rate": 0.08957,
                    "amount": 100,
                    "convertedAmount": 8.957,
                    "source": "Bank of Ghana",
                    "retrievedAt": "2024-01-20T10:00:00Z",
                },
                "message": "Exchange rate retrieved",
                "timestamp": "2024-01-20T10:00:00Z",
                "requestId": "req-1234567890-fxabc",
            }
        },
        "execution_time_ms": 310,
        "created_at": datetime.now(timezone.utc) - timedelta(seconds=45),
    },
    {
        "tool": "loan_repayment_calculator",
        "agent_id": "agent-adwoa",
        "role": "customer-support",
        "status": ExecutionStatus.SUCCESS,
        "input_data": {
            "principal": 50000,
            "annualRate": 28.5,
            "termMonths": 24,
            "extraPayment": 200,
        },
        "output_data": {
            "projection": {
                "status": "success",
                "data": {
                    "principal": 50000,
                    "annualRate": 28.5,
                    "termMonths": 24,
                    "baseMonthlyPayment": 2706.14,
                    "scheduledMonthlyPayment": 2906.14,
                    "totalPaid": 69747.36,
                    "totalInterest": 19747.36,
                    "projectedMonths": 22,
                    "payoffDate": "2026-12-01T00:00:00.000Z",
                    "summary": "Pay ~GHS 2906.14 per month to clear the loan in 22 months.",
                },
                "message": "Loan repayment projection generated",
                "timestamp": "2024-02-01T10:00:00Z",
                "requestId": "req-1234567890-loan",
            }
        },
        "execution_time_ms": 640,
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

        session.add(
            ToolParameter(
                id=uuid4(),
                tool_id=tool.id,
                name=param_data["name"],
                type=param_data["type"],
                required=param_data.get("required", False),
                description=param_data.get("description"),
                default_value=param_data.get("default_value"),
                parameter_type=param_data["parameter_type"],
            )
        )

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


def create_execution_history(
    session: Session,
    execution_data: Dict,
    role_map: Dict[str, Role],
    tool_map: Dict[str, Tool],
) -> None:
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
    tool_map: Dict[str, Tool] = {}
    for tool_data in TOOLS_DATA:
        tool = get_or_create_tool(session, tool_data)
        tool_map[tool.name] = tool

    role_map: Dict[str, Role] = {}
    for role_data in ROLES_DATA:
        role = get_or_create_role(session, role_data["name"], role_data["description"])
        role_map[role.name] = role

    for perm_data in PERMISSIONS_DATA:
        role = role_map.get(perm_data["role"])
        tool = tool_map.get(perm_data["tool"])
        if role and tool:
            ensure_permission(session, role, tool, perm_data["action"], True)

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

