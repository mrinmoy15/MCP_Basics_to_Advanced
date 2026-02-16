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
To run the server with MCP inspector for development run the following command
```bash
uv run mcp dev custom_weather_mcp_server/weather.py
```
To run the server normally use the following command
```bash
uv run mcp custom_weather_mcp_server/weather.py
```
To install the server use the following command
```bash
uv run mcp install custom_weather_mcp_server/weather.py
```

Once the server is installed it can be accessed as a tool using Calude Desktop as well. You can get the configuration and then use it in cursor/vscode as well.