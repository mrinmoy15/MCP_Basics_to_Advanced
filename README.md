# MCP Servers: From Basics to Advanced tutorials
MCP_Deepdive document has the related basic theory about how MCP server works. This repo contains the codes for some of the best MCP materials available on the internet. Here are the links of the materials.
- [MCP Crash course by Krish Naik](https://www.youtube.com/playlist?list=PLZoTAELRMXVPC8r1xF68Gksi241DAtMsK)
- [MCP Course By Hugging Face](https://huggingface.co/learn/mcp-course/en/unit0/introduction)

## Setup Steps
- Create a project folder and then go to that location in terminal. Initialize a project folder using uv with the following command
```bash
uv init
```

- Create a virtual environment and activate it using the following commands
```bash
python -m venv .venv
.venv\Source\activate
```

- Install all dependencies with the following command
```bash
uv add -r requirements.txt
```


## Running The server
To run the server with MCP inspector for development run the following command (change the filename accordingly)
```bash
uv run mcp dev custom_weather_mcp_server/weather.py
```
To run the server normally use the following command (change the filename accordingly)
```bash
uv run mcp custom_weather_mcp_server/weather.py
```
To install the server use the following command (change the filename accordingly)
```bash
uv run mcp install custom_weather_mcp_server/weather.py
```

Once the server is installed it can be accessed as a tool using Calude Desktop as well. You can get the configuration and then use it in cursor/vscode as well.

The code repo contains several examples of how an mcp can be used. For example `sample_mcp_app.py` contains codes to create a chatbot that is powered by LLM and also has access to various MCP servers through the `browser_mcp.json`.   

Similarlly, `hello_world_mcp.py` contains very basic code just to show case all the capabilities of an mcp server (viz tools, resources, prompts)  
  
Inside the `custom_weather_mcp_server` folder we have created a weather alerts related mcp server that can be accessed by clients. The file `weather.py` contains the server side code where as the `client.py` has the client side codes with llm calls.   
  
Inside the `mcpserver` folder a very basic framework for tool call is demonstrated via both `stdio transport` and `sse transport`. Also the containerization using `Dockerfile` is demonstrated.