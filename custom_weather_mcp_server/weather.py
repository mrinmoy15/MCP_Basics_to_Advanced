from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from constants import NWS_API_BASE, USER_AGENT


# initialize the FastMCP server: don't use spaces
mcp = FastMCP("Weather_MCP_Server")

async def make_nws_request(url:str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling"""

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string"""

    props = feature['properties']
    return f"""
    Event: {props.get('event', 'Unkown')}
    Area: {props.get('areaDesc', 'Unkown')}
    Severity: {props.get('severity', 'Unkown')}
    Description: {props.get('description', 'No descriptions available')}
    Instructions: {props.get('instruction', 'No instructions provided')}
    """


@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Get weather alerts for US state

    Args:
        state(str): two letter US state code (e.g. CA, TX, NY etc.)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data['features']:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data['features']]
    return "\n-----\n".join(alerts)


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource."""
    return f"Resource echo: {message}"


