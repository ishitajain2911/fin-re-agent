from dotenv import load_dotenv
import os
import anthropic

load_dotenv()
client = anthropic.Anthropic()

response = client.beta.messages.tool_runner(max_tokens=500, model="claude-sonnet-5",messages=[{"role":"user", "content":"Look up Micron's latest 10-K filing"}], tools=[{"type": "mcp_toolset", "mcp_server_name":"fin-research-tools"}], mcp_servers=[{"type":"url","url":"https://decorator-simply-seventy.ngrok-free.dev/mcp", "name": "fin-research-tools"}], betas=["mcp-client-2025-11-20"])

for message in response:
    print(message)