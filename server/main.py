from dotenv import load_dotenv
import anthropic
from fastapi import FastAPI
app = FastAPI()


load_dotenv()
client = anthropic.Anthropic()



@app.get("/health")
def health():
    health_status ={"status": "ok"}
    return health_status

@app.post("/research")
def research(ticker:str):
    response = client.beta.messages.tool_runner(max_tokens=500, model="claude-sonnet-5",messages=[{"role":"user", "content": f"Look up {ticker}'s latest 10-K filing"}], tools=[{"type": "mcp_toolset", "mcp_server_name":"fin-research-tools"}], mcp_servers=[{"type":"url","url":"https://decorator-simply-seventy.ngrok-free.dev/mcp", "name": "fin-research-tools"}], betas=["mcp-client-2025-11-20"])

    

    final_message = None
    for message in response:
        final_message = message

    for block in final_message.content:
        if block.type == "text":
            return {"result": block.text}

