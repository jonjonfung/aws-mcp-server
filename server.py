from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

load_dotenv()

# AWS credentials (for local dev; on AWS these come from IAM role)
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2')

if aws_key:
    os.environ['AWS_ACCESS_KEY_ID'] = aws_key
if aws_secret:
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret
os.environ['AWS_DEFAULT_REGION'] = aws_region

mcp = FastMCP("Claude MCP")

# Register connectors
from connectors.aws import register as register_aws
from connectors.github import register as register_github

register_aws(mcp)
register_github(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')
