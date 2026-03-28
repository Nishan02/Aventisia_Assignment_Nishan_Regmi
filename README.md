# GitHub Cloud Connector

A backend API built with Python and FastAPI to connect with GitHub and perform common repository actions.

## Features
- Authentication via Personal Access Token (PAT)
- Bonus OAuth 2.0 login flow
- Fetch repositories for a GitHub user
- List issues from a repository
- Fetch commits from a repository
- Create an issue in a repository
- Bonus: Create a pull request

## Tech Stack
- Python
- FastAPI
- HTTPX
- Pydantic

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <your-repo-link>
   cd Aventisia_Assignment_Nishan_Regmi
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   ```
   Mac/Linux:
   ```bash
   source venv/bin/activate
   ```
   Windows (PowerShell):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```bash
   pip install fastapi uvicorn httpx python-dotenv
   ```

4. Create a `.env` file in the project root:
   ```env
   GITHUB_PAT=your_personal_access_token
   GITHUB_CLIENT_ID=your_oauth_app_client_id
   GITHUB_CLIENT_SECRET=your_oauth_app_client_secret
   ```

## Run the Project

```bash
uvicorn main:app --reload
```

API base URL:
`http://127.0.0.1:8000`

Interactive docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### 1) Fetch Repositories
- Method: `GET`
- Endpoint: `/repos/{username}`
- Description: Returns public repositories for the given user.

Example:
```bash
curl http://127.0.0.1:8000/repos/octocat
```

### 2) List Issues
- Method: `GET`
- Endpoint: `/repos/{owner}/{repo}/issues`
- Description: Lists issues for the specified repository.

Example:
```bash
curl http://127.0.0.1:8000/repos/octocat/Hello-World/issues
```

### 3) Create Issue
- Method: `POST`
- Endpoint: `/repos/{owner}/{repo}/issues`
- Description: Creates a new issue in the specified repository.

Request body:
```json
{
  "title": "Bug report",
  "body": "Describe the issue here"
}
```

Example:
```bash
curl -X POST http://127.0.0.1:8000/repos/<owner>/<repo>/issues \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Bug report\",\"body\":\"Describe the issue here\"}"
```

### 4) Fetch Commits
- Method: `GET`
- Endpoint: `/repos/{owner}/{repo}/commits`
- Description: Returns commits from the repository.
- Query params:
  - `branch` (optional): branch name (example: `main`)
  - `per_page` (optional): number of results per page (1-100, default 30)
  - `page` (optional): page number (default 1)

Example:
```bash
curl "http://127.0.0.1:8000/repos/octocat/Hello-World/commits?branch=main&per_page=10&page=1"
```

### 5) Create Pull Request (Bonus)
- Method: `POST`
- Endpoint: `/repos/{owner}/{repo}/pulls`
- Description: Creates a pull request.

Request body:
```json
{
  "title": "Add feature",
  "head": "feature-branch",
  "base": "main",
  "body": "PR description"
}
```

### 6) OAuth Login (Bonus)
- Method: `GET`
- Endpoint: `/auth/login`
- Description: Redirects to GitHub OAuth consent screen.

- Method: `GET`
- Endpoint: `/auth/callback?code=<github_code>`
- Description: Exchanges authorization code for an access token.

## Project Structure

```text
.
|-- main.py      # FastAPI routes and GitHub API integration
|-- models.py    # Pydantic request models
`-- README.md
```

## Notes
- Keep secrets in `.env` and never hardcode tokens.
- Ensure your PAT has appropriate permissions (`repo` scope for private repo operations).
