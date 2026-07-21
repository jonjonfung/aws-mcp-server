import os
import requests

GITHUB_API = "https://api.github.com"


def _headers():
    token = os.getenv('GITHUB_TOKEN')
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }


def register(mcp):

    @mcp.tool()
    def list_my_repos() -> str:
        """List all GitHub repos for the authenticated user."""
        try:
            response = requests.get(f"{GITHUB_API}/user/repos?per_page=50&sort=updated", headers=_headers())
            repos = response.json()
            if isinstance(repos, dict) and "message" in repos:
                return f"Error: {repos['message']}"
            lines = [f"{r['full_name']} — {r['description'] or 'no description'} ({'private' if r['private'] else 'public'})" for r in repos]
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing repos: {str(e)}"

    @mcp.tool()
    def list_issues(owner: str, repo: str, state: str = "open") -> str:
        """
        List issues for a GitHub repo.
        state: open, closed, or all
        """
        try:
            response = requests.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues?state={state}&per_page=30",
                headers=_headers()
            )
            issues = response.json()
            if isinstance(issues, dict) and "message" in issues:
                return f"Error: {issues['message']}"
            if not issues:
                return f"No {state} issues found in {owner}/{repo}"
            lines = [f"#{i['number']} [{i['state']}] {i['title']}" for i in issues if 'pull_request' not in i]
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing issues: {str(e)}"

    @mcp.tool()
    def read_file(owner: str, repo: str, path: str, branch: str = "main") -> str:
        """Read the contents of a file from a GitHub repo."""
        try:
            import base64
            response = requests.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}?ref={branch}",
                headers=_headers()
            )
            data = response.json()
            if "message" in data:
                return f"Error: {data['message']}"
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @mcp.tool()
    def create_issue(owner: str, repo: str, title: str, body: str = "") -> str:
        """Create a new issue in a GitHub repo."""
        try:
            response = requests.post(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                headers=_headers(),
                json={"title": title, "body": body}
            )
            issue = response.json()
            if "message" in issue:
                return f"Error: {issue['message']}"
            return f"Created issue #{issue['number']}: {issue['html_url']}"
        except Exception as e:
            return f"Error creating issue: {str(e)}"

    @mcp.tool()
    def list_pull_requests(owner: str, repo: str, state: str = "open") -> str:
        """
        List pull requests for a GitHub repo.
        state: open, closed, or all
        """
        try:
            response = requests.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls?state={state}&per_page=30",
                headers=_headers()
            )
            prs = response.json()
            if isinstance(prs, dict) and "message" in prs:
                return f"Error: {prs['message']}"
            if not prs:
                return f"No {state} pull requests found in {owner}/{repo}"
            lines = [f"#{pr['number']} {pr['title']} ({pr['head']['ref']} → {pr['base']['ref']})" for pr in prs]
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing PRs: {str(e)}"
