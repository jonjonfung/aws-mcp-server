# claude-mcp

An MCP (Model Context Protocol) server that connects Claude to AWS data infrastructure and GitHub. Run it locally to give Claude direct access to your data and repos via natural language.

## What it does

This server exposes tools to Claude across two connectors:

### AWS
- **query_athena** — Run SQL queries against AWS Athena (databases: `olist_silver_db`, `stock_db`)
- **list_s3_files** — List files in S3 buckets
- **get_stock_data** — Fetch recent stock prices for AAPL, GOOGL, MSFT, AMZN, META
- **predict_delivery** — Predict delivery time in days for Brazilian e-commerce orders using an ML model
- **get_business_summary** — High-level summary of Olist e-commerce data (orders, revenue, customers)

### GitHub
- **list_my_repos** — List all repos for the authenticated user
- **list_issues** — List issues for a repo (open/closed/all)
- **list_pull_requests** — List PRs for a repo (open/closed/all)
- **read_file** — Read the contents of a file from a repo
- **create_issue** — Create a new issue in a repo

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file:
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_DEFAULT_REGION=ap-southeast-2
   GITHUB_TOKEN=your_github_token
   ```

3. Add the server to your Claude config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "claude-mcp": {
         "command": "/path/to/venv/bin/python",
         "args": ["/path/to/claude-mcp/server.py"]
       }
     }
   }
   ```

4. Restart Claude Desktop.

## Adding a connector

Create a new folder under `connectors/`, define a `register(mcp)` function, and import it in `server.py`.
