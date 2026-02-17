from mcp.server.fastmcp import FastMCP

# create a FastMCP server instance
mcp = FastMCP("Weather_Bot")

# tool implementation
@mcp.tool()
def get_weather(location: str) -> str:
    # In a real implementation, you would call a weather API here.
    # For this example, we'll return a dummy weather report.
    return f"The current weather in {location} is sunny with a temperature of 25°C."

# resource implementation
@mcp.resource("weather://{location}")
def weather_resource(location: str) -> str:
    # This resource can be used to fetch weather information for a given location.
    return f"The current weather in {location} is sunny with a temperature of 25°C."

# Prompt implementation
@mcp.prompt()
def weather_report(location: str) -> str:
    """Create a weather report prompt."""
    return f"""You are a weather reporter. Weather report for {location}?"""

# run the server
if __name__ == "__main__":
    mcp.run()