import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
import argparse

nest_asyncio.apply()  # Needed to run interactive python

"""
Make sure:
1. The server is running before running this script.
2. The server is configured to use SSE transport.
3. The server is listening on port 8050.

To run the server:
uv run server.py
"""

## just note that no LLM call is happening here, it is purely a tool call demonstration with this client

async def main(port:int):
    # Connect to the server using SSE
    async with sse_client(f"http://localhost:{port}/sse") as (read_stream, write_stream):
         async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call our Weather tool
            result = await session.call_tool("get_alerts", arguments={"state":"CA"})
            print(f"The weather alerts are = {result.content[0].text}") # type: ignore


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="MCP Client with SSE transport")
    
    # Add the port argument
    # 'type=int' ensures the input is converted to an integer automatically
    # 'default=8050' provides a fallback if the user skips the argument
    parser.add_argument(
        "--port", 
        type=int, 
        default=8050, 
        help="Port of the MCP server (default: 8050)"
    )

    # Parse the arguments from the command line
    args = parser.parse_args()

    try:
        # Pass the parsed port to your main function
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except Exception as e:
        print(f"Error: {e}")