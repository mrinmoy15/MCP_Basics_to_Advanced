import asyncio
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from contextlib import AsyncExitStack
from typing import Any, Dict, List
import os


class MCPToolWrapper:
    """Wrapper to convert MCP tools to LangChain tools"""
    
    def __init__(self, session: ClientSession, tool_name: str, tool_description: str):
        self.session = session
        self.tool_name = tool_name
        self.tool_description = tool_description
        self._loop = None
    
    def _sync_call(self, **kwargs: Any) -> str:
        """Synchronous wrapper for async MCP tool call"""
        # Use existing event loop or create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use a different approach
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._async_call(**kwargs)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self._async_call(**kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self._async_call(**kwargs))
    
    async def _async_call(self, **kwargs: Any) -> str:
        """Execute the MCP tool asynchronously"""
        result = await self.session.call_tool(self.tool_name, kwargs)
        # Extract text content from result
        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                return "\n".join(str(item) for item in result.content)
            return str(result.content)
        return str(result)
    
    async def __call__(self, **kwargs: Any) -> str:
        """Async call interface"""
        return await self._async_call(**kwargs)


async def load_mcp_servers(config_file: str):
    """Load MCP servers from config file and return active sessions"""
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    sessions = {}
    exit_stack = AsyncExitStack()
    
    for server_name, server_config in config.get("mcpServers", {}).items():
        command = server_config.get("command", "uvx")
        args = server_config.get("args", [])
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None
        )
        
        # Create stdio transport
        stdio_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        
        # Create client session
        session = await exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        # Initialize the session
        await session.initialize()
        
        sessions[server_name] = session
    
    return sessions, exit_stack


async def create_langchain_tools(sessions: Dict[str, ClientSession]):
    """Convert MCP tools to LangChain tools"""
    tools = []
    tool_map = {}  # Map tool names to async wrappers
    
    for server_name, session in sessions.items():
        # List available tools from this server
        tools_response = await session.list_tools()
        
        for mcp_tool in tools_response.tools:
            # Create async wrapper
            tool_wrapper = MCPToolWrapper(
                session=session,
                tool_name=mcp_tool.name,
                tool_description=mcp_tool.description or f"Tool: {mcp_tool.name}"
            )
            
            # Create LangChain tool with sync wrapper and async coroutine
            langchain_tool = StructuredTool.from_function(
                func=tool_wrapper._sync_call,
                coroutine=tool_wrapper._async_call,
                name=f"{server_name}_{mcp_tool.name}",
                description=mcp_tool.description or f"Tool: {mcp_tool.name}",
            )
            
            tools.append(langchain_tool)
            tool_map[langchain_tool.name] = tool_wrapper
    
    return tools, tool_map


async def run_agent_loop(llm, tools, tool_map, messages, max_iterations=15):
    """Run agent loop with tool calling"""
    for iteration in range(max_iterations):
        try:
            # Bind tools to LLM
            if hasattr(llm, 'bind_tools'):
                llm_with_tools = llm.bind_tools(tools)
            else:
                # Fallback: use tools directly if bind_tools not available
                llm_with_tools = llm
            
            # Get response from LLM
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            
            # Check if we're done - handle different response formats
            tool_calls = None
            if hasattr(response, 'tool_calls'):
                tool_calls = response.tool_calls
            elif hasattr(response, 'additional_kwargs') and 'tool_calls' in response.additional_kwargs:
                tool_calls = response.additional_kwargs['tool_calls']
            
            if not tool_calls:
                # Get content from response
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)
            
            # Execute tool calls
            for tool_call in tool_calls:
                # Handle different tool_call formats
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                    tool_args_str = tool_call.get("args") or tool_call.get("function", {}).get("arguments", "{}")
                    tool_call_id = tool_call.get("id") or tool_call.get("id", "")
                else:
                    tool_name = getattr(tool_call, 'name', None)
                    tool_args_str = getattr(tool_call, 'args', "{}")
                    tool_call_id = getattr(tool_call, 'id', "")
                
                # Parse args if string
                if isinstance(tool_args_str, str):
                    import json
                    try:
                        tool_args = json.loads(tool_args_str)
                    except:
                        tool_args = {}
                else:
                    tool_args = tool_args_str or {}
                
                if tool_name and tool_name in tool_map:
                    # Execute the tool
                    tool_result = await tool_map[tool_name](**tool_args)
                    
                    # Add tool result to messages
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    ))
                else:
                    messages.append(ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_call_id
                    ))
        
        except Exception as e:
            return f"Error in agent loop: {str(e)}"
    
    return "Maximum iterations reached. Please try a simpler query."


async def run_memory_chat():
    """Run a chat using MCP tools with conversation memory."""
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    
    # Configure file path
    config_file = "browser_mcp.json"
    
    print("Initializing Chat.....")
    
    # Load MCP servers
    sessions, exit_stack = await load_mcp_servers(config_file)
    
    # Create LangChain tools from MCP tools
    tools, tool_map = await create_langchain_tools(sessions)
    
    if not tools:
        print("No tools found from MCP servers!")
        return
    
    print(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")
    
    # Initialize LLM
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # Conversation memory
    memory = []
    
    print("\n=====Interactive MCP Chat======")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'clear' to clear the conversation history.")
    print("==================================\n")
    
    try:
        while True:
            user_input = input("\nYou: ")
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                print("\nThank you for using the MCP Chat! Goodbye!")
                break
            
            # Check for clear history command
            if user_input.lower() == 'clear':
                memory.clear()
                print("\nConversation history cleared.")
                continue
            
            # Prepare messages with history
            messages = []
            for i in range(0, len(memory), 2):
                if i < len(memory):
                    messages.append(HumanMessage(content=memory[i]))
                if i + 1 < len(memory):
                    messages.append(AIMessage(content=memory[i + 1]))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Get response from agent
            print("\nAssistant: ", end="", flush=True)
            
            try:
                assistant_response = await run_agent_loop(llm, tools, tool_map, messages)
                print(assistant_response)
                
                # Update memory
                memory.append(user_input)
                memory.append(assistant_response)
                
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
    
    finally:
        # Clean up
        await exit_stack.aclose()
        print("\nChat session ended.")


if __name__ == "__main__":
    asyncio.run(run_memory_chat())