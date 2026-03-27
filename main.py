import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from models import IssueCreate, PullRequestCreate

# Load secrets from the .env file
load_dotenv()

GITHUB_PAT = os.getenv("GITHUB_PAT")
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# Initialize the FastAPI app
app = FastAPI(title="GitHub Cloud Connector", description="Assignment API")

# Helper function to get the headers needed for GitHub API
def get_github_headers(custom_token: str = None):
    # If the user logged in via OAuth, use their token, otherwise use our PAT
    token = custom_token if custom_token else GITHUB_PAT
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

# ==========================================
# CORE ACTIONS (REPOS, ISSUES, PRs)
# ==========================================

@app.get("/repos/{username}")
async def fetch_repositories(username: str):
    """Fetch public repositories for a specific user."""
    url = f"https://api.github.com/users/{username}/repos"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=get_github_headers())
        
        # Error handling! If GitHub says "Not Found", we tell our user.
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found on GitHub")
        response.raise_for_status() # Raise error for any other failures
        
        # Only return the important data, not the massive GitHub payload
        repos = response.json()
        return [{"id": r["id"], "name": r["name"], "url": r["html_url"]} for r in repos]


@app.get("/repos/{owner}/{repo}/issues")
async def list_issues(owner: str, repo: str):
    """List issues from a specific repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=get_github_headers())
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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=get_github_headers())
        if response.status_code != 201: # 201 means "Created"
            raise HTTPException(status_code=response.status_code, detail=response.json())
            
        return response.json()


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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=get_github_headers())
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