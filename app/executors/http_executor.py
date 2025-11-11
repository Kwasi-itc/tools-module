import httpx
import json
from string import Formatter
from typing import Dict, Any, Optional
from app.database.models import Tool, ToolConfig


class HTTPExecutor:
    """Executor for HTTP-based tools"""
    
    @staticmethod
    async def execute(
        tool: Tool,
        input_data: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute an HTTP tool.
        
        Args:
            tool: Tool model instance
            input_data: Input parameters for the tool
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing execution result
        """
        # Get tool configurations
        configs = {config.config_key: config.config_value for config in tool.configs}
        
        # Build request
        base_url = configs.get("base_url", "")
        endpoint = configs.get("endpoint", "")
        method = configs.get("method", "GET").upper()
        
        # Extract path parameters from endpoint template
        formatter = Formatter()
        path_param_names = {
            field_name for _, field_name, _, _ in formatter.parse(endpoint) if field_name
        }

        path_values = {}
        for name in path_param_names:
            if name in input_data:
                path_values[name] = input_data[name]
            else:
                raise Exception(f"Missing required path parameter '{name}' for endpoint template '{endpoint}'")

        # Construct full URL with formatted endpoint
        formatted_endpoint = endpoint.format(**path_values) if path_param_names else endpoint
        if formatted_endpoint.startswith("http"):
            url = formatted_endpoint
        else:
            url = f"{base_url.rstrip('/')}/{formatted_endpoint.lstrip('/')}"
        
        # Get headers
        headers = {}
        if "headers" in configs:
            try:
                headers = json.loads(configs["headers"])
            except json.JSONDecodeError:
                headers = {}

        # Default query parameters
        default_params = {}
        if "query_params" in configs:
            try:
                parsed = json.loads(configs["query_params"])
                if isinstance(parsed, dict):
                    default_params = parsed
            except json.JSONDecodeError:
                default_params = {}
        
        # Handle authentication
        auth_type = configs.get("auth_type", "")
        if auth_type == "bearer_token" and "api_key" in configs:
            headers["Authorization"] = f"Bearer {configs['api_key']}"
        elif auth_type == "api_key" and "api_key" in configs:
            api_key_header = configs.get("api_key_header", "X-API-Key")
            headers[api_key_header] = configs["api_key"]
        elif auth_type == "basic_auth":
            # Basic auth would need username/password in configs
            if "username" in configs and "password" in configs:
                import base64
                credentials = f"{configs['username']}:{configs['password']}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        
        # Prepare request data
        request_kwargs = {
            "url": url,
            "headers": headers,
            "timeout": timeout
        }
        
        # Remove path parameters from input when preparing request payloads
        sanitized_input = {
            key: value for key, value in input_data.items() if key not in path_param_names
        }

        # Map input values into headers if configured
        headers_input_map = configs.get("headers_input_map")
        if headers_input_map:
            try:
                parsed_map = json.loads(headers_input_map)
                if isinstance(parsed_map, dict):
                    for input_key, mapping in parsed_map.items():
                        if input_key not in sanitized_input:
                            continue

                        header_name = None
                        template = "{value}"

                        if isinstance(mapping, dict):
                            header_name = mapping.get("header")
                            template = mapping.get("template", "{value}")
                        elif isinstance(mapping, str):
                            header_name = mapping
                        else:
                            continue

                        if not header_name:
                            continue

                        headers[header_name] = template.format(value=sanitized_input[input_key])
                        sanitized_input.pop(input_key, None)
            except json.JSONDecodeError:
                pass

        # Add body for POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"]:
            content_type = headers.get("Content-Type", "application/json")
            if content_type == "application/json":
                request_kwargs["json"] = sanitized_input
            else:
                request_kwargs["data"] = sanitized_input

        # Add query params for GET/DELETE
        elif method in ["GET", "DELETE"]:
            combined_params = {**default_params, **sanitized_input}
            request_kwargs["params"] = combined_params
        else:
            request_kwargs["params"] = default_params
        
        # Make the request
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.request(method, **request_kwargs)
                
                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = {"text": response.text}
                
                return {
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers)
                }
            except httpx.TimeoutException:
                raise Exception(f"Request timeout after {timeout} seconds")
            except httpx.RequestError as e:
                raise Exception(f"Request failed: {str(e)}")

