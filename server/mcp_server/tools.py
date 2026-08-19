from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "fin-research-tools",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "decorator-simply-seventy.ngrok-free.dev"]
    ),
)
@mcp.tool()
def search_filings(ticker:str, query:str)->str:
    """Search SEC filings for a given ticker and query"""
    return f" fake filing result for {ticker}: {query}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")