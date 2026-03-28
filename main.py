import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from models import IssueCreate, PullRequestCreate
from typing import Optional

# Load secrets from the .env file
load_dotenv()

GITHUB_PAT = os.getenv("GITHUB_PAT")
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# Initialize the FastAPI app
app = FastAPI(title="GitHub Cloud Connector", description="Assignment API")

@app.get("/", include_in_schema=False)
def read_root():
    """Redirect root URL to interactive API docs."""
    return RedirectResponse(url="/docs")

# Helper function to get the headers needed for GitHub API
def resolve_token(custom_token: Optional[str] = None) -> Optional[str]:
    """Return a clean token value or None if no token exists."""
    token = (custom_token or GITHUB_PAT or "").strip()
    return token or None


def get_github_headers(
    custom_token: Optional[str] = None,
    include_auth: bool = True,
) -> dict:
    """Build headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github+json"}

    if include_auth:
        token = resolve_token(custom_token)
        if token:
            headers["Authorization"] = f"Bearer {token}"

    return headers


async def github_get_with_auth_fallback(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
) -> httpx.Response:
    """
    Try GET with auth first; if token is invalid (401), retry unauthenticated.
    This keeps public endpoints usable even when a PAT is missing/incorrect.
    """
    response = await client.get(url, headers=get_github_headers(), params=params)
    if response.status_code == 401:
        response = await client.get(
            url,
            headers=get_github_headers(include_auth=False),
            params=params,
        )
    return response


def get_required_token() -> str:
    """Ensure token exists for write operations."""
    token = resolve_token()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing GITHUB_PAT. Add it to .env for write operations.",
        )
    return token

# ==========================================
# CORE ACTIONS (REPOS, ISSUES, PRs)
# ==========================================

@app.get("/repos/{username}")
async def fetch_repositories(username: str):
    """Fetch public repositories for a specific user."""
    url = f"https://api.github.com/users/{username}/repos"
    
    async with httpx.AsyncClient() as client:
        response = await github_get_with_auth_fallback(client, url)
        
        # Error handling! If GitHub says "Not Found", we tell our user.
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found on GitHub")
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        response.raise_for_status()  # Raise error for any other failures
        
        # Only return the important data, not the massive GitHub payload
        repos = response.json()
        return [{"id": r["id"], "name": r["name"], "url": r["html_url"]} for r in repos]


@app.get("/repos/{owner}/{repo}/issues")
async def list_issues(owner: str, repo: str):
    """List issues from a specific repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    async with httpx.AsyncClient() as client:
        response = await github_get_with_auth_fallback(client, url)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch issues")
            
        issues = response.json()
        return [{"id": i["id"], "title": i["title"], "state": i["state"]} for i in issues]


@app.post("/repos/{owner}/{repo}/issues")
async def create_issue(owner: str, repo: str, issue: IssueCreate):
    """Create a new issue in a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    # We convert our Pydantic model back to a dictionary to send to GitHub
    payload = {"title": issue.title, "body": issue.body}
    token = get_required_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers=get_github_headers(custom_token=token),
        )
        if response.status_code != 201: # 201 means "Created"
            raise HTTPException(status_code=response.status_code, detail=response.json())
            
        return response.json()


# Fetch commits from a repository
@app.get("/repos/{owner}/{repo}/commits")
async def fetch_commits(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
    per_page: int = Query(default=30, ge=1, le=100),
    page: int = Query(default=1, ge=1),
):
    """Fetch commits from a specific repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": per_page, "page": page}

    if branch:
        params["sha"] = branch

    async with httpx.AsyncClient() as client:
        response = await github_get_with_auth_fallback(client, url, params=params)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found on GitHub")
        if response.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="Repository is empty or has no commits yet",
            )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Could not fetch commits",
            )

        commits = response.json()
        return [
            {
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message"),
                "author": (c.get("commit", {}).get("author") or {}).get("name"),
                "date": (c.get("commit", {}).get("author") or {}).get("date"),
                "url": c.get("html_url"),
            }
            for c in commits
        ]


# BONUS: Create a Pull Request
@app.post("/repos/{owner}/{repo}/pulls")
async def create_pull_request(owner: str, repo: str, pr: PullRequestCreate):
    """Create a pull request in a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": pr.title,
        "head": pr.head,
        "base": pr.base,
        "body": pr.body
    }
    token = get_required_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers=get_github_headers(custom_token=token),
        )
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.json())
            
        return response.json()


# ==========================================
# BONUS: OAUTH 2.0 AUTHENTICATION FLOW
# ==========================================

@app.get("/auth/login")
def login_via_github():
    """Redirects the user to GitHub to authorize our app."""
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=repo"
    return RedirectResponse(github_auth_url)

@app.get("/auth/callback")
async def github_callback(code: str):
    """GitHub redirects here with a 'code'. We exchange it for an access token."""
    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }
    headers = {"Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=payload, headers=headers)
        data = response.json()
        
        if "access_token" not in data:
            raise HTTPException(status_code=400, detail="OAuth failed")
            
        # In a real app, you would save this token to a database.
        # Here, we just return it to the user.
        return {"message": "Success! Use this token for your API calls.", "access_token": data["access_token"]}
