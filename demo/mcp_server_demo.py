from mcp.server.fastmcp import FastMCP
from typing import List
import subprocess


MCP_SERVER_NAME = "elasticsearch-mcp-server"
mcp = FastMCP(MCP_SERVER_NAME)




@mcp.tool()
def list_indices() -> List[str]:
    """列出所有 Elasticsearch 索引"""
    return [index["index"] for index in es.cat.indices(format="json")]

@mcp.tool()
def get_index(index: str) -> dict:
    """获取特定 Elasticsearch 索引的详细信息"""
    return es.indices.get(index=index)




@mcp.resource("es://logs")
def get_logs() -> str:
    """Get Elasticsearch container logs"""
    result = subprocess.run(["docker", "logs", "elasticsearch-mcp-server-example-es01-1"], capture_output=True, text=True, check=True)
    return result.stdout

@mcp.resource("file://docker-compose.yaml")
def get_file() -> str:
    """Return the contents of docker-compose.yaml file"""
    with open("docker-compose.yaml", "r") as f:
        return f.read()
    


@mcp.prompt()
def es_prompt(index: str) -> str:
    """Create a prompt for index analysis"""
    return f"""You are an elite Elasticsearch expert with deep knowledge of search engine architecture, data indexing strategies, and performance optimization. Please analyze the index '{index}' considering:
- Index settings and mappings
- Search optimization opportunities
- Data modeling improvements
- Potential scaling considerations
"""